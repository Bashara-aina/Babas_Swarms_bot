"""
SQLite-backed conversation store — guaranteed persistence fallback.
Runs even if mem0, MemoryOS, and all cloud memory fail.
Every turn stored and retrievable across restarts.
"""
from __future__ import annotations
import asyncio
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".legion" / "conversations.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_CONTENT_PREVIEW_CHARS = 200


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metadata_json TEXT DEFAULT '{}'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_ts ON conversations(user_id, timestamp)")
    conn.commit()
    return conn


async def store_turn(user_id: str, role: str, content: str, metadata: dict | None = None) -> None:
    def _store() -> None:
        conn = _get_db()
        conn.execute(
            "INSERT INTO conversations (user_id, role, content, timestamp, metadata_json) VALUES (?, ?, ?, ?, ?)",
            (user_id, role, content, time.time(), json.dumps(metadata or {})),
        )
        conn.commit()
        conn.close()
    try:
        await asyncio.to_thread(_store)
    except Exception as e:
        logger.warning("store_turn failed: %s", e)


async def get_recent_turns(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    def _get() -> list[dict]:
        conn = _get_db()
        rows = conn.execute(
            "SELECT role, content, timestamp FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in reversed(rows)]
    try:
        return await asyncio.to_thread(_get)
    except Exception as e:
        logger.warning("get_recent_turns failed: %s", e)
        return []


async def build_history_prompt(user_id: str, limit: int = 10) -> str:
    turns = await get_recent_turns(user_id, limit=limit)
    if not turns:
        return ""
    lines = ["[Recent conversation history:"]
    for t in turns:
        role_label = "Bashara" if t["role"] == "user" else "Legion"
        lines.append(f"  {role_label}: {t['content'][:_CONTENT_PREVIEW_CHARS]}")
    lines.append("]")
    return "\n".join(lines)
