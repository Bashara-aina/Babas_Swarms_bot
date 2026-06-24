"""Conversation interface — extracted shared state for llm_client/router/agents.

This module provides a single import point for conversation history, thread
memory, and routing helpers (detect_agent, get_fallback_chain) to avoid
circular import chains between llm_client ↔ router ↔ agents.

All conversation state lives here; agents.py and router.py re-export from here.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from core.agent_registry import detect_agent as _detect_agent
from core.agent_registry import get_fallback_chain as _get_fallback_chain
from core.thread_store import (
    ACTIVE_THREADS,
    add_to_thread,
    clear_thread,
    get_thread_context,
    list_threads,
    list_threads_raw,
)

logger = logging.getLogger(__name__)

# ── Re-export routing helpers ─────────────────────────────────────────────────
detect_agent = _detect_agent
get_fallback_chain = _get_fallback_chain

# ── Conversation history ─────────────────────────────────────────────────────
CONVERSATION_HISTORY: dict[str, list[dict]] = {}
MAX_HISTORY_TURNS = 20
MAX_HISTORY_CHARS = 8000
_HISTORY_TTL_DAYS = 30

_CONV_DB_PATH = os.path.join(os.path.expanduser("~"), ".legionswarm", "memory", "conversation_history.db")
_conv_db_ready = False
_conv_db_loaded_users: set[str] = set()


def _ensure_conv_db_dir() -> None:
    os.makedirs(os.path.dirname(_CONV_DB_PATH), exist_ok=True)


async def _init_conv_db() -> None:
    """Create the conversation_history table if it doesn't exist."""
    global _conv_db_ready
    if _conv_db_ready:
        return
    try:
        import aiosqlite

        _ensure_conv_db_dir()
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    ts REAL NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_turns(user_id, ts)")
            await db.commit()
        _conv_db_ready = True
    except Exception as exc:
        logger.warning("Conversation DB init failed (non-fatal): %s", exc)


async def _load_history_from_db(user_id: str) -> None:
    """Load last N turns from SQLite into RAM cache (once per user per session)."""
    if user_id in _conv_db_loaded_users:
        return
    _conv_db_loaded_users.add(user_id)
    try:
        import aiosqlite

        await _init_conv_db()
        async with aiosqlite.connect(_CONV_DB_PATH) as db, db.execute(
            "SELECT role, content, ts FROM conversation_turns WHERE user_id = ? ORDER BY ts DESC LIMIT ?",
            (user_id, MAX_HISTORY_TURNS * 2),
        ) as cursor:
            rows = await cursor.fetchall()
        if rows:
            turns = [{"role": r[0], "content": r[1], "ts": r[2]} for r in reversed(rows)]  # type: ignore[reportCallIssue]
            if user_id not in CONVERSATION_HISTORY:
                CONVERSATION_HISTORY[user_id] = turns
            else:
                existing_ts = {t["ts"] for t in CONVERSATION_HISTORY[user_id]}
                for t in turns:
                    if t["ts"] not in existing_ts:
                        CONVERSATION_HISTORY[user_id].append(t)
                CONVERSATION_HISTORY[user_id].sort(key=lambda x: x["ts"])
            logger.info("Loaded %d conversation turns from DB for user %s", len(turns), user_id)
    except Exception as exc:
        logger.debug("Conversation DB load failed (non-fatal): %s", exc)


async def _persist_turn_to_db(user_id: str, role: str, content: str, ts: float) -> None:
    """Fire-and-forget SQLite write for a single conversation turn."""
    try:
        import aiosqlite

        await _init_conv_db()
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            await db.execute(
                "INSERT INTO conversation_turns (user_id, role, content, ts) VALUES (?, ?, ?, ?)",
                (user_id, role, content[:MAX_HISTORY_CHARS], ts),
            )
            await db.commit()
    except Exception as exc:
        logger.debug("Conversation DB persist failed (non-fatal): %s", exc)


async def _cleanup_old_turns() -> None:
    """Delete turns older than TTL."""
    try:
        import aiosqlite

        await _init_conv_db()
        cutoff = time.time() - (_HISTORY_TTL_DAYS * 86400)
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            await db.execute("DELETE FROM conversation_turns WHERE ts < ?", (cutoff,))
            await db.commit()
            logger.info("Cleaned up old conversation turns (cutoff: %d days)", _HISTORY_TTL_DAYS)
    except Exception as exc:
        logger.debug("Conversation DB cleanup failed: %s", exc)


def get_conversation_history(user_id: str, last_n: int = MAX_HISTORY_TURNS) -> list[dict]:
    """Return recent conversation history as litellm-compatible messages."""
    if user_id not in _conv_db_loaded_users:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_load_history_from_db(user_id))
        except Exception:
            pass
    if user_id not in CONVERSATION_HISTORY:
        return []
    turns = CONVERSATION_HISTORY[user_id][-last_n:]
    return [{"role": t["role"], "content": t["content"]} for t in turns]


def add_to_conversation(user_id: str, role: str, content: str) -> None:
    """Append a turn to conversation history."""
    ts = time.time()
    if user_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[user_id] = []
    CONVERSATION_HISTORY[user_id].append(
        {
            "role": role,
            "content": content,
            "ts": ts,
        }
    )
    if len(CONVERSATION_HISTORY[user_id]) > MAX_HISTORY_TURNS * 2:
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY[user_id][-(MAX_HISTORY_TURNS * 2) :]
    logger.debug("Conversation history for %s: %d turns", user_id, len(CONVERSATION_HISTORY[user_id]))

    # Fire-and-forget SQLite persistence
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_persist_turn_to_db(user_id, role, content, ts))
    except Exception:
        pass

    # Fire-and-forget OpenViking L1 persistence
    if role == "assistant":
        user_turns = CONVERSATION_HISTORY[user_id]
        last_user_msg = ""
        for t in reversed(user_turns):
            if t["role"] == "user":
                last_user_msg = t["content"]
                break
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist_to_viking(user_id, last_user_msg, content))
        except Exception:
            pass

    # Fire-and-forget session transcript persistence (U1)
    try:
        loop = asyncio.get_running_loop()
        from core.session.transcript import get_transcript_store

        store = get_transcript_store()
        loop.create_task(store.save_turn(None, user_id, role, content))
    except Exception:
        pass


async def _persist_to_viking(user_id: str, user_msg: str, assistant_msg: str) -> None:
    """Async helper: persist conversation turn to OpenViking L1."""
    try:
        from tools.viking_context import save_interaction_to_l1

        await save_interaction_to_l1(user_id, user_msg, assistant_msg)
    except Exception as e:
        logger.debug("Viking L1 persist skipped (non-fatal): %s", e)


def clear_conversation(user_id: str) -> None:
    """Wipe conversation history for a user (fresh start)."""
    if user_id in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[user_id]
        logger.info("Cleared conversation history for %s", user_id)
    _conv_db_loaded_users.discard(user_id)


def get_conversation_summary_prompt(user_id: str) -> str:
    """Build a compact context block to prepend to the system prompt."""
    history = get_conversation_history(user_id, last_n=6)
    if not history:
        return ""
    lines = ["[CONVERSATION CONTEXT — last exchanges:]", ""]
    for turn in history:
        role_label = "Bashara" if turn["role"] == "user" else "Legion"
        snippet = turn["content"][:300].replace("\n", " ")
        if len(turn["content"]) > 300:
            snippet += "..."
        lines.append(f"{role_label}: {snippet}")
    lines.append("[end context]")
    return "\n".join(lines)


def get_last_message_timestamp(user_id: str) -> float:
    """Return timestamp of last message from user, or 0 if no messages."""
    if user_id not in CONVERSATION_HISTORY or not CONVERSATION_HISTORY[user_id]:
        return 0.0
    return CONVERSATION_HISTORY[user_id][-1].get("ts", 0.0)


__all__ = [
    "ACTIVE_THREADS",
    "CONVERSATION_HISTORY",
    "add_to_conversation",
    "add_to_thread",
    "clear_conversation",
    "clear_thread",
    "detect_agent",
    "get_conversation_history",
    "get_conversation_summary_prompt",
    "get_fallback_chain",
    "get_thread_context",
    "list_threads",
    "list_threads_raw",
]
