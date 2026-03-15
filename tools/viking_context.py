"""tools/viking_context.py — OpenViking hybrid context database layer.

Architecture (L0 / L1 / L2):
  L0  Identity / persona abstract  — loaded on every single request
      URI: viking://legion/identity
  L1  Per-user session overview    — loaded for the current user each request
      URI: viking://legion/users/{user_id}/sessions/current
  L2  Deep history / knowledge     — loaded only when find() scores > threshold
      URI: viking://legion/users/{user_id}/history/{yyyymmdd}

Fallback policy:
  If openviking is not installed OR if the local data dir is unavailable,
  ALL functions return empty strings / empty lists — NEVER raise to caller.
  The caller (memory.py, agents.py) will then fall back to SQLite/TF-IDF.

Install:
  pip install openviking

Storage: ~/.legion_viking/   (local file store, no server needed)
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Data directory ─────────────────────────────────────────────────────────
VIKING_DIR = Path(os.environ.get(
    "VIKING_DATA_DIR",
    Path.home() / ".legion_viking"
))

# ── Lazy singleton client ──────────────────────────────────────────────────
_client = None
_client_lock = asyncio.Lock()
_available: Optional[bool] = None   # None = not yet probed


def _get_client_sync():
    """Return a SyncOpenViking client, initialised once. Returns None on failure."""
    global _client, _available
    if _available is False:
        return None
    if _client is not None:
        return _client
    try:
        import openviking as ov  # type: ignore
        VIKING_DIR.mkdir(parents=True, exist_ok=True)
        c = ov.SyncOpenViking(path=str(VIKING_DIR))
        c.initialize()
        _client = c
        _available = True
        logger.info("OpenViking context database initialised at %s", VIKING_DIR)
        _ensure_l0_identity(c)
        return c
    except ImportError:
        _available = False
        logger.warning(
            "openviking not installed — falling back to SQLite/TF-IDF memory. "
            "Run: pip install openviking"
        )
        return None
    except Exception as e:
        _available = False
        logger.warning("OpenViking init failed (non-fatal): %s", e)
        return None


def _ensure_l0_identity(client) -> None:
    """Write the Legion identity abstract into L0 on first run."""
    uri = "viking://legion/identity"
    try:
        # Try reading — if it exists, skip writing
        existing = client.read(uri)
        if existing and len(existing) > 50:
            return
    except Exception:
        pass
    try:
        identity_text = (
            "# Legion — Bashara's Personal AI\n\n"
            "Legion is Bashara's personal AI assistant running on her Linux workstation "
            "(Ubuntu, RTX 3060 12GB, Python 3.13, ~/swarm-bot). \n"
            "Legion has full desktop access: shell execution, screenshot analysis, "
            "file read/write, GUI interaction.\n\n"
            "## Personality\n"
            "- Casual, direct, like a senior dev friend\n"
            "- Matches user's language (Indonesian ↔ English)\n"
            "- Never says 'As an AI...' — has full tool access and uses it\n"
            "- Cites sources inline with [Source: ...] format\n\n"
            "## Agent Roster\n"
            "vision, coding, debug, math, architect, analyst, computer, "
            "general, researcher, marketer, devops, pm, humanizer, reviewer\n\n"
            "## Tech Stack\n"
            "Next.js, TypeScript, Supabase, Python, PyTorch, LiteLLM, aiogram3, "
            "Midtrans, aiosqlite, Ollama (local), Groq, Cerebras, Gemini, OpenRouter"
        )
        client.add_resource(path=identity_text, uri=uri)
        logger.info("OpenViking L0 identity abstract written")
    except Exception as e:
        logger.debug("L0 identity write skipped: %s", e)


# ── Async wrappers ─────────────────────────────────────────────────────────

async def _run_sync(fn, *args, **kwargs):
    """Run a sync openviking call in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ── Public API ─────────────────────────────────────────────────────────────

def is_available() -> bool:
    """Return True if OpenViking is installed and initialised."""
    return _get_client_sync() is not None


async def save_interaction_to_l1(
    user_id: str,
    user_message: str,
    assistant_reply: str,
    session_id: Optional[str] = None,
) -> None:
    """
    Persist a conversation turn into the L1 per-user session context.
    URI: viking://legion/users/{user_id}/sessions/{session_id}

    L1 is the 'overview' tier — it accumulates session turns and gets
    automatically summarised by OpenViking to keep context lean.
    """
    client = _get_client_sync()
    if client is None:
        return
    try:
        sid = session_id or datetime.now().strftime("%Y%m%d")
        uri = f"viking://legion/users/{user_id}/sessions/{sid}"
        ts = datetime.now().strftime("%H:%M:%S")
        turn_text = (
            f"[{ts}] User: {user_message[:500]}\n"
            f"[{ts}] Legion: {assistant_reply[:800]}\n"
        )
        await _run_sync(client.add_resource, path=turn_text, uri=uri)
    except Exception as e:
        logger.debug("save_interaction_to_l1 failed (non-fatal): %s", e)


async def auto_extract_facts(
    user_id: str,
    user_message: str,
    assistant_reply: str,
) -> None:
    """
    Extract and persist long-term facts / preferences from an interaction
    into a permanent L2 'facts' node for the user.

    Heuristic: only save if the reply contains a solution, URL, code block,
    or a user preference signal — same as the old auto_save_interaction() logic.
    """
    import re
    worth_saving_patterns = [
        r"https?://",
        r"/[a-z_]+/[a-z_]+",
        r"```",
        r"arXiv",
        r"\bfix\b|\bsolved\b|\bworkaround\b",
        r"\bremember\b|\bdon't forget\b|\bimportant\b",
    ]
    if len(assistant_reply) < 200:
        return
    if not any(re.search(p, assistant_reply, re.IGNORECASE) for p in worth_saving_patterns):
        return

    client = _get_client_sync()
    if client is None:
        return
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        uri = f"viking://legion/users/{user_id}/history/{date_str}"
        combined = f"Q: {user_message[:300]}\nA: {assistant_reply[:700]}"
        await _run_sync(client.add_resource, path=combined, uri=uri)
        logger.debug("auto_extract_facts: saved to L2 %s", uri)
    except Exception as e:
        logger.debug("auto_extract_facts failed (non-fatal): %s", e)


async def semantic_search(
    query: str,
    user_id: Optional[str] = None,
    top_k: int = 5,
    score_threshold: float = 0.15,
) -> list[dict]:
    """
    Semantic search across all user context using OpenViking's
    Directory Recursive Retrieval strategy.

    Returns list of {uri, score, snippet} dicts, sorted by score.
    Falls back to [] if OpenViking is unavailable.
    """
    client = _get_client_sync()
    if client is None:
        return []
    try:
        target = f"viking://legion/users/{user_id}" if user_id else "viking://legion"
        results = await _run_sync(client.find, query, target_uri=target)
        out = []
        for r in results.resources:
            if r.score < score_threshold:
                continue
            try:
                snippet = await _run_sync(client.read, r.uri)
                snippet = (snippet or "")[:400]
            except Exception:
                snippet = r.uri
            out.append({"uri": r.uri, "score": r.score, "snippet": snippet})
        return sorted(out, key=lambda x: x["score"], reverse=True)[:top_k]
    except Exception as e:
        logger.debug("semantic_search failed (non-fatal): %s", e)
        return []


async def build_viking_context(
    query: str,
    user_id: Optional[str] = None,
    include_l0: bool = True,
    include_l1: bool = True,
    include_l2: bool = True,
    max_chars: int = 2000,
) -> str:
    """
    Build a complete tiered context block to inject into the system prompt.

    Tier loading order:
      L0 — Legion identity abstract (always, tiny, ~200 chars)
      L1 — Current session overview for user_id (compact, auto-summarised)
      L2 — Semantic search results for the query (only high-scoring hits)

    Returns an empty string if OpenViking is unavailable (caller uses fallback).
    """
    client = _get_client_sync()
    if client is None:
        return ""

    parts: list[str] = []
    used_chars = 0

    # ── L0: Identity abstract ────────────────────────────────────────────
    if include_l0:
        try:
            abstract = await _run_sync(client.abstract, "viking://legion/identity")
            if abstract and len(abstract) > 10:
                l0_block = f"[L0 — Identity]\n{abstract[:400]}"
                parts.append(l0_block)
                used_chars += len(l0_block)
        except Exception:
            pass

    # ── L1: Session overview ─────────────────────────────────────────────
    if include_l1 and user_id and used_chars < max_chars:
        try:
            sid = datetime.now().strftime("%Y%m%d")
            uri = f"viking://legion/users/{user_id}/sessions/{sid}"
            overview = await _run_sync(client.overview, uri)
            if overview and len(overview) > 20:
                remaining = max_chars - used_chars
                l1_block = f"[L1 — Session Context]\n{overview[:min(800, remaining)]}"
                parts.append(l1_block)
                used_chars += len(l1_block)
        except Exception:
            pass

    # ── L2: Semantic search ──────────────────────────────────────────────
    if include_l2 and used_chars < max_chars:
        try:
            hits = await semantic_search(
                query,
                user_id=user_id,
                top_k=3,
                score_threshold=0.20,
            )
            if hits:
                lines = ["[L2 — Relevant Context]"]
                for h in hits:
                    remaining = max_chars - used_chars - len("\n".join(lines))
                    if remaining < 50:
                        break
                    snippet = h["snippet"][:min(300, remaining)]
                    lines.append(f"• (score={h['score']:.2f}) {snippet}")
                l2_block = "\n".join(lines)
                parts.append(l2_block)
                used_chars += len(l2_block)
        except Exception:
            pass

    if not parts:
        return ""

    return (
        "[VIKING CONTEXT — tiered memory from OpenViking]\n\n"
        + "\n\n".join(parts)
        + "\n[end viking context]"
    )


async def get_l0_abstract() -> str:
    """Return the Legion identity abstract (L0). Used for /start and /models commands."""
    client = _get_client_sync()
    if client is None:
        return ""
    try:
        return (await _run_sync(client.abstract, "viking://legion/identity")) or ""
    except Exception:
        return ""


async def init_viking_db() -> None:
    """
    Called from main.py on_startup(). Warms up the client so the first
    user request doesn't pay the initialisation cost.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _get_client_sync)
    if _available:
        logger.info("✅ OpenViking context database ready at %s", VIKING_DIR)
    else:
        logger.info("ℹ️ OpenViking not available — using SQLite/TF-IDF fallback")
