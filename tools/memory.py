"""
tools/memory.py — Persistent long-context memory for LegionSwarm.

Two-layer memory architecture:
  1. RAM layer   : CONVERSATION_HISTORY in agents.py (per-session, hot)
  2. Primary     : OpenViking L0/L1/L2 tiered context database (semantic,
                   cross-restart persistent, self-evolving)
  3. Fallback    : SQLite + TF-IDF cosine similarity (used when OpenViking
                   is not installed or unavailable)

Features:
  - add_memory()           : save a note with tags + source
  - search_memory()        : semantic (OpenViking) or TF-IDF similarity search
  - get_recent()           : last N memories
  - build_memory_context() : tiered context block (OpenViking) or compact
                             TF-IDF string — drop-in for system prompt injection
  - auto_save_interaction(): called after every /run or /do
  - export_to_obsidian()   : dump all notes as .md files

No threading — all async. Uses aiosqlite + openviking.
"""

from __future__ import annotations
import asyncio
import json
import logging
import math
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import aiosqlite
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "aiosqlite", "-q"])
    import aiosqlite

DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", Path.home() / ".legion_memory.db"))

# ── Schema ────────────────────────────────────────────────────────────────────
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    text     TEXT    NOT NULL,
    tags     TEXT    DEFAULT '',
    source   TEXT    DEFAULT 'manual',
    tfidf    TEXT    DEFAULT '{}',
    created  REAL    NOT NULL,
    accessed REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tags    ON memories(tags);
"""


async def _init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()


# ── TF-IDF helpers (fallback when OpenViking unavailable) ─────────────────────
STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "be", "was", "are", "with",
    "this", "that", "from", "by", "as", "i", "you", "we", "they",
    "yang", "di", "ke", "dari", "dan", "atau", "ini", "itu",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def _tfidf_vector(text: str) -> dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in counts.items()}


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    if not vec_a or not vec_b:
        return 0.0
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[w] * vec_b[w] for w in common)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── CRUD ──────────────────────────────────────────────────────────────────────
async def add_memory(
    text: str,
    tags: list[str] | None = None,
    source: str = "manual",
) -> int:
    """
    Save a note to persistent memory.
    Writes to both SQLite (for /recall, /memories commands) and
    OpenViking L2 history (for semantic retrieval).
    Returns the SQLite row id.
    """
    await _init_db()
    now = time.time()
    tags_str = ",".join(tags or [])
    vec = _tfidf_vector(text)
    tfidf_json = json.dumps(vec)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO memories (text, tags, source, tfidf, created, accessed) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (text, tags_str, source, tfidf_json, now, now),
        )
        await db.commit()
        memory_id = cursor.lastrowid
    logger.info("Memory saved: id=%d tags=%s source=%s", memory_id, tags_str, source)

    # Also write to OpenViking L2 for semantic retrieval
    try:
        from tools.viking_context import auto_extract_facts
        # Use a synthetic user_id='manual' for manually added memories
        await auto_extract_facts("manual", f"[{source}] {tags_str}", text)
    except Exception:
        pass

    return memory_id


async def search_memory(query: str, top_k: int = 5, user_id: Optional[str] = None) -> list[dict]:
    """
    Semantic search via OpenViking (primary) or TF-IDF cosine (fallback).
    Returns list of dicts: {id, text, tags, source, score, created}
    """
    # ── Try OpenViking semantic search first ──────────────────────────────
    try:
        from tools.viking_context import semantic_search, is_available
        if is_available():
            hits = await semantic_search(query, user_id=user_id, top_k=top_k)
            if hits:
                # Convert to same format as TF-IDF results
                return [
                    {
                        "id": 0,
                        "text": h["snippet"],
                        "tags": h["uri"],
                        "source": "openviking",
                        "score": h["score"],
                        "created": time.time(),
                    }
                    for h in hits
                ]
    except Exception as e:
        logger.debug("OpenViking search failed, falling back to TF-IDF: %s", e)

    # ── TF-IDF fallback ───────────────────────────────────────────────────
    await _init_db()
    query_vec = _tfidf_vector(query)
    if not query_vec:
        return await get_recent(top_k)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, text, tags, source, tfidf, created FROM memories ORDER BY created DESC LIMIT 200"
        ) as cursor:
            rows = await cursor.fetchall()

    scored = []
    for row in rows:
        try:
            vec = json.loads(row["tfidf"])
        except Exception:
            vec = {}
        score = _cosine_similarity(query_vec, vec)
        scored.append({
            "id": row["id"],
            "text": row["text"],
            "tags": row["tags"],
            "source": row["source"],
            "score": score,
            "created": row["created"],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    results = [r for r in scored[:top_k] if r["score"] > 0.01]

    if results:
        ids = [str(r["id"]) for r in results]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                f"UPDATE memories SET accessed = ? WHERE id IN ({','.join(ids)})",
                (time.time(),),
            )
            await db.commit()

    return results


async def get_recent(n: int = 10) -> list[dict]:
    """Return the N most recently added memories."""
    await _init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, text, tags, source, created FROM memories ORDER BY created DESC LIMIT ?",
            (n,),
        ) as cursor:
            rows = await cursor.fetchall()
    return [
        {"id": r["id"], "text": r["text"], "tags": r["tags"],
         "source": r["source"], "created": r["created"]}
        for r in rows
    ]


async def delete_memory(memory_id: int) -> bool:
    """Delete a memory by ID."""
    await _init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        await db.commit()
    logger.info("Memory deleted: id=%d", memory_id)
    return True


async def count_memories() -> int:
    await _init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM memories") as cursor:
            row = await cursor.fetchone()
    return row[0] if row else 0


# ── Context injection helper ──────────────────────────────────────────────────
async def build_memory_context(query: str, top_k: int = 3, user_id: Optional[str] = None) -> str:
    """
    Build a context block to inject into a system prompt.

    Primary path: OpenViking tiered context (L0 + L1 + L2 semantic hits)
    Fallback path: TF-IDF cosine search over SQLite memories

    Keeps total output under ~2000 chars.
    """
    # ── Primary: OpenViking tiered context ───────────────────────────────
    try:
        from tools.viking_context import build_viking_context, is_available
        if is_available():
            ctx = await build_viking_context(
                query=query,
                user_id=user_id,
                max_chars=2000,
            )
            if ctx:
                return ctx
    except Exception as e:
        logger.debug("build_viking_context failed, using TF-IDF fallback: %s", e)

    # ── Fallback: TF-IDF SQLite search ───────────────────────────────────
    results = await search_memory(query, top_k=top_k, user_id=user_id)
    if not results:
        return ""

    lines = ["[MEMORY CONTEXT — relevant notes from your second brain:]", ""]
    for r in results:
        created = datetime.fromtimestamp(r["created"]).strftime("%Y-%m-%d")
        tags = f" [{r['tags']}]" if r["tags"] else ""
        snippet = r["text"][:400].replace("\n", " ")
        if len(r["text"]) > 400:
            snippet += "..."
        lines.append(f"• ({created}{tags}) {snippet}")

    lines.append("[end memory context]")
    return "\n".join(lines)


async def auto_save_interaction(
    user_message: str,
    assistant_reply: str,
    source: str = "conversation",
    user_id: Optional[str] = None,
) -> None:
    """
    Decide if the interaction is worth remembering, then save it.
    Writes to both SQLite and OpenViking L1/L2.
    """
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
    worth_saving = any(
        re.search(pat, assistant_reply, re.IGNORECASE)
        for pat in worth_saving_patterns
    )
    if not worth_saving:
        return

    combined = f"Q: {user_message[:200]}\nA: {assistant_reply[:600]}"
    tags = [source]
    if "arxiv" in assistant_reply.lower() or "paper" in user_message.lower():
        tags.append("research")
    if any(kw in user_message.lower() for kw in ["pytorch", "cuda", "workernet", "ikea"]):
        tags.append("ml")
    if any(kw in user_message.lower() for kw in ["nextjs", "supabase", "typescript", "react"]):
        tags.append("webdev")
    if "fix" in assistant_reply.lower() or "debug" in user_message.lower():
        tags.append("fix")

    # Save to SQLite (for /recall, /memories commands)
    await add_memory(combined, tags=tags, source=source)

    # Also save to OpenViking L1 (session) and L2 (fact extraction)
    if user_id:
        try:
            from tools.viking_context import save_interaction_to_l1, auto_extract_facts
            await save_interaction_to_l1(user_id, user_message, assistant_reply)
            await auto_extract_facts(user_id, user_message, assistant_reply)
        except Exception as e:
            logger.debug("OpenViking save skipped (non-fatal): %s", e)

    logger.debug("Auto-saved interaction to memory (tags=%s)", tags)


# ── Obsidian export ───────────────────────────────────────────────────────────
async def export_to_obsidian(vault_path: str | Path) -> int:
    """
    Export all SQLite memories as .md files to an Obsidian vault directory.
    Returns count of files written.
    """
    vault = Path(vault_path)
    vault.mkdir(parents=True, exist_ok=True)

    await _init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, text, tags, source, created FROM memories ORDER BY created DESC"
        ) as cursor:
            rows = await cursor.fetchall()

    count = 0
    for row in rows:
        created = datetime.fromtimestamp(row["created"]).strftime("%Y-%m-%d %H:%M")
        safe_title = re.sub(r"[^\w\s-]", "", row["text"][:50]).strip().replace(" ", "-")
        filename = vault / f"memory-{row['id']:04d}-{safe_title[:30]}.md"
        tags_list = [t for t in row["tags"].split(",") if t]
        tags_yaml = "\n".join(f"  - {t}" for t in tags_list)
        content = (
            f"---\n"
            f"id: {row['id']}\n"
            f"source: {row['source']}\n"
            f"created: {created}\n"
            f"tags:\n{tags_yaml or '  - untagged'}\n"
            f"---\n\n"
            f"{row['text']}\n"
        )
        filename.write_text(content, encoding="utf-8")
        count += 1

    logger.info("Exported %d memories to %s", count, vault)
    return count


# ── Format helpers (for Telegram display) ────────────────────────────────────
def format_memory_result(r: dict, show_score: bool = False) -> str:
    created = datetime.fromtimestamp(r["created"]).strftime("%Y-%m-%d")
    tags = f" <i>[{r['tags']}]</i>" if r.get("tags") else ""
    score_str = f" <i>(score: {r['score']:.2f})</i>" if show_score and "score" in r else ""
    text_preview = r["text"][:300].replace("<", "&lt;").replace(">", "&gt;")
    if len(r["text"]) > 300:
        text_preview += "..."
    return (
        f"<b>#{r['id']}</b>{tags} <code>{created}</code>{score_str}\n"
        f"{text_preview}"
    )


# ── Init alias (called from main.py) ─────────────────────────────────────────
async def init_memory_db() -> None:
    """Init SQLite schema and warm up OpenViking client."""
    await _init_db()
    try:
        from tools.viking_context import init_viking_db
        await init_viking_db()
    except Exception as e:
        logger.debug("OpenViking warmup skipped: %s", e)
