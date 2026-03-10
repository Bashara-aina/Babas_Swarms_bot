"""memory.py — Second brain / searchable knowledge base for Legion.

Uses SQLite + TF-IDF cosine similarity for semantic search.
Stores notes, tags, sources with timestamps.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import aiosqlite
except ImportError:
    import subprocess, sys
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "aiosqlite", "--break-system-packages", "-q"],
        check=False,
    )
    import aiosqlite

from tools.persistence import DB_PATH


# ── Schema ──────────────────────────────────────────────────────────────────

async def init_memory_db() -> None:
    """Create memory table if not exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS memory_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                tags TEXT DEFAULT '',
                source TEXT DEFAULT 'manual',
                word_vector TEXT DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_source ON memory_notes(source);
        """)
        await db.commit()
    logger.info("Memory DB initialized")


# ── TF-IDF helpers ──────────────────────────────────────────────────────────

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "and", "but", "or", "if", "this",
    "that", "these", "those", "it", "its", "i", "me", "my", "we", "our",
    "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
}


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer: lowercase, alphanumeric only, remove stop words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) > 1]


def _word_freq(text: str) -> dict[str, int]:
    return dict(Counter(_tokenize(text)))


def _cosine_sim(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Cosine similarity between two word-frequency vectors."""
    common = set(vec_a.keys()) & set(vec_b.keys())
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Core operations ─────────────────────────────────────────────────────────

async def add_memory(
    text: str,
    tags: Optional[list[str]] = None,
    source: str = "manual",
) -> int:
    """Store a note in the knowledge base. Returns note ID."""
    await init_memory_db()
    tags_str = ",".join(tags) if tags else ""
    vec = json.dumps(_word_freq(text))
    now = time.time()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO memory_notes (text, tags, source, word_vector, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (text, tags_str, source, vec, now),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def search_memory(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """TF-IDF cosine similarity search across all notes."""
    await init_memory_db()
    query_vec = _word_freq(query)
    if not query_vec:
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memory_notes ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()

    # Score each note
    scored = []
    for row in rows:
        row_dict = dict(row)
        try:
            note_vec = json.loads(row_dict.get("word_vector", "{}"))
        except (json.JSONDecodeError, TypeError):
            note_vec = {}
        sim = _cosine_sim(query_vec, note_vec)

        # Boost if query words appear in tags
        tags = row_dict.get("tags", "")
        tag_boost = sum(0.1 for w in _tokenize(query) if w in tags.lower())
        sim += tag_boost

        if sim > 0:
            scored.append((sim, row_dict))

    # Sort by similarity, return top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, note in scored[:top_k]:
        results.append({
            "id": note["id"],
            "text": note["text"],
            "tags": note["tags"],
            "source": note["source"],
            "created_at": note["created_at"],
            "relevance": round(sim, 3),
        })
    return results


async def get_recent_memories(limit: int = 10) -> list[dict[str, Any]]:
    """Get the N most recent memories."""
    await init_memory_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM memory_notes ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def link_memories(note_id: int) -> list[dict[str, Any]]:
    """Find notes semantically similar to the given note."""
    await init_memory_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memory_notes WHERE id = ?", (note_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return []
            target = dict(row)

    # Search using the note's text as query
    results = await search_memory(target["text"], top_k=6)
    # Exclude self
    return [r for r in results if r["id"] != note_id]


async def export_to_obsidian(vault_path: str) -> str:
    """Export all memories as .md files to an Obsidian vault directory."""
    await init_memory_db()
    vault = Path(vault_path)
    vault.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memory_notes ORDER BY created_at") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return "No memories to export."

    exported = 0
    for row in rows:
        note = dict(row)
        note_id = note["id"]
        tags = note.get("tags", "")
        source = note.get("source", "manual")
        text = note.get("text", "")
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(note["created_at"]))

        # Generate filename
        first_line = text.split("\n")[0][:60].strip()
        safe_name = re.sub(r"[^\w\s-]", "", first_line).strip().replace(" ", "_") or f"note_{note_id}"
        filename = f"{safe_name}.md"

        # Build markdown
        lines = [
            f"# {first_line}",
            "",
            f"**Source:** {source}  ",
            f"**Date:** {ts}  ",
        ]
        if tags:
            tag_links = " ".join(f"#{t.strip()}" for t in tags.split(",") if t.strip())
            lines.append(f"**Tags:** {tag_links}  ")
        lines += ["", "---", "", text]

        # Find linked notes
        linked = await link_memories(note_id)
        if linked:
            lines += ["", "## Related Notes", ""]
            for ln in linked[:3]:
                ln_first = ln["text"].split("\n")[0][:50]
                ln_safe = re.sub(r"[^\w\s-]", "", ln_first).strip().replace(" ", "_")
                lines.append(f"- [[{ln_safe}]] (relevance: {ln['relevance']})")

        (vault / filename).write_text("\n".join(lines), encoding="utf-8")
        exported += 1

    return f"Exported {exported} notes to {vault_path}"


async def auto_save_research(paper_analysis: str, paper_id: str = "") -> int:
    """Auto-save a paper analysis result to memory."""
    tags = ["arxiv", "research"]
    if paper_id:
        tags.append(paper_id)
    return await add_memory(paper_analysis, tags=tags, source="arxiv")
