"""OpenMemory: explainable local memory with sector-based decay scoring."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OPEN_MEMORY_ROOT = Path(os.path.expanduser("~/.legion/open_memory"))
OPEN_MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH = OPEN_MEMORY_ROOT / "memories.db"

SECTOR_EPISODIC = "episodic"
SECTOR_SEMANTIC = "semantic"
SECTOR_PROCEDURAL = "procedural"
SECTOR_CORE = "core"

DECAY_DAYS = float(os.getenv("MEMORY_DECAY_DAYS", "30"))
HALF_LIFE_SECONDS = max(1.0, DECAY_DAYS * 24.0 * 3600.0)


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            sector TEXT NOT NULL,
            importance REAL DEFAULT 1.0,
            created_at REAL NOT NULL,
            last_accessed REAL NOT NULL,
            access_count INTEGER DEFAULT 0,
            metadata_json TEXT DEFAULT '{}'
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_user_sector ON memories(user_id, sector, created_at DESC)")
    conn.commit()
    return conn


async def om_store(
    user_id: str,
    content: str,
    sector: str = SECTOR_EPISODIC,
    importance: float = 1.0,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Store a memory in OpenMemory."""
    def _store() -> int:
        conn = _get_db()
        now = time.time()
        cur = conn.execute(
            "INSERT INTO memories (user_id, content, sector, importance, created_at, last_accessed, access_count, metadata_json) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (user_id, content, sector, importance, now, now, json.dumps(metadata or {}, ensure_ascii=False)),
        )
        conn.commit()
        row_id = int(cur.lastrowid)
        conn.close()
        return row_id

    return await asyncio.to_thread(_store)


def _decay_score(created_at: float, importance: float, access_count: int) -> float:
    age = max(0.0, time.time() - created_at)
    decay = math.exp(-age / HALF_LIFE_SECONDS)
    return (importance * 0.7 + min(access_count, 20) * 0.05 + decay * 0.3)


async def om_search(user_id: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search OpenMemory using lexical overlap and decay scoring."""
    q_tokens = {token for token in query.lower().split() if len(token) > 2}

    def _search() -> list[dict[str, Any]]:
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC LIMIT 500",
            (user_id,),
        ).fetchall()
        conn.close()

        results: list[dict[str, Any]] = []
        for row in rows:
            content = str(row["content"])
            content_tokens = set(content.lower().split())
            overlap = len(q_tokens & content_tokens)
            semantic_score = overlap / max(1, len(q_tokens))
            decay = _decay_score(float(row["created_at"]), float(row["importance"] or 1.0), int(row["access_count"] or 0))
            final_score = (semantic_score * 0.7) + (decay * 0.3)
            reason = (
                f"semantic={semantic_score:.2f}, "
                f"decay={decay:.2f}, "
                f"sector={row['sector']}, "
                f"accessed={row['access_count']}x"
            )
            results.append({
                "id": row["id"],
                "content": content,
                "sector": row["sector"],
                "score": round(final_score, 3),
                "decay_score": round(decay, 3),
                "semantic_score": round(semantic_score, 3),
                "reason": reason,
                "metadata": json.loads(row["metadata_json"] or "{}"),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    results = await asyncio.to_thread(_search)

    async def _update_access(ids: list[int]) -> None:
        def _update() -> None:
            conn = _get_db()
            now = time.time()
            conn.executemany(
                "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                [(now, mid) for mid in ids],
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(_update)

    if results:
        asyncio.create_task(_update_access([int(item["id"]) for item in results]))
    return results


async def om_delete(memory_id: int) -> None:
    """Delete a memory by ID."""
    def _delete() -> None:
        conn = _get_db()
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()

    await asyncio.to_thread(_delete)


async def om_stats(user_id: str) -> dict[str, Any]:
    """Return OpenMemory statistics by sector."""
    def _stats() -> dict[str, Any]:
        conn = _get_db()
        rows = conn.execute(
            """
            SELECT sector, COUNT(*) as cnt, AVG(importance) as avg_imp, AVG(access_count) as avg_access
            FROM memories WHERE user_id = ?
            GROUP BY sector
            """,
            (user_id,),
        ).fetchall()
        conn.close()
        return {
            r["sector"]: {
                "count": r["cnt"],
                "avg_importance": round(r["avg_imp"] or 0, 2),
                "avg_accesses": round(r["avg_access"] or 0, 1),
            }
            for r in rows
        }

    return await asyncio.to_thread(_stats)


def build_om_context(results: list[dict[str, Any]], max_chars: int = 2000) -> str:
    """Format OpenMemory results into a prompt block."""
    if not results:
        return ""
    lines = ["[OpenMemory — local recall (why each was retrieved):]"]
    total = 0
    for item in results:
        line = f"• [{item['sector']}] {item['content']} (why: {item['reason']})"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    lines.append("[End OpenMemory context]")
    return "\n".join(lines)
