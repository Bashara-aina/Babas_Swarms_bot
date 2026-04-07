"""Local MemoryOS-style hierarchical memory sidecar."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MEMORYOS_STORAGE = Path(os.path.expanduser("~/.legion/memoryos"))
MEMORYOS_STORAGE.mkdir(parents=True, exist_ok=True)
DB_PATH = MEMORYOS_STORAGE / "memoryos.sqlite3"


@dataclass
class _MemoryOSRecord:
    user_id: str
    kind: str
    content: str
    created_at: float
    access_count: int = 0
    metadata_json: str = "{}"


class LocalMemoryOS:
    """Minimal local MemoryOS-compatible tiered memory store."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_memory_items_user_kind ON memory_items(user_id, kind, created_at DESC);
            """
        )
        conn.commit()
        conn.close()

    def add_memory(self, user_input: str, agent_response: str) -> None:
        conn = self._conn()
        now = time.time()
        entries = [
            _MemoryOSRecord(self.user_id, "hot", f"U: {user_input}\nA: {agent_response}", now),
            _MemoryOSRecord(self.user_id, "warm", agent_response[:1200], now),
        ]
        conn.executemany(
            "INSERT INTO memory_items (user_id, kind, content, created_at, access_count, metadata_json) VALUES (?, ?, ?, ?, ?, ?)",
            [(r.user_id, r.kind, r.content, r.created_at, r.access_count, r.metadata_json) for r in entries],
        )
        conn.commit()
        conn.close()

    def retrieve(self, query: str) -> dict[str, Any]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM memory_items WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (self.user_id,),
        ).fetchall()
        conn.close()
        q = query.lower()
        relevant: list[str] = []
        for row in rows:
            content = str(row["content"])
            if any(token and token in content.lower() for token in q.split()[:8]):
                relevant.append(f"[{row['kind']}] {content}")
        if not relevant:
            relevant = [f"[{row['kind']}] {row['content']}" for row in rows[:5]]
        return {"context": "\n".join(relevant[:10]), "count": len(relevant)}

    def get_stats(self) -> dict[str, Any]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT kind, COUNT(*) AS cnt, AVG(access_count) AS avg_access FROM memory_items WHERE user_id = ? GROUP BY kind",
            (self.user_id,),
        ).fetchall()
        conn.close()
        return {str(r["kind"]): {"count": int(r["cnt"]), "avg_access": round(float(r["avg_access"] or 0), 2)} for r in rows}


_mos_instance: LocalMemoryOS | None = None


def get_memoryos(user_id: str = "bashara") -> LocalMemoryOS:
    """Return a local MemoryOS-compatible instance."""
    global _mos_instance
    if _mos_instance is None or _mos_instance.user_id != user_id:
        _mos_instance = LocalMemoryOS(user_id=user_id)
        logger.info("MemoryOS initialized (local fallback)")
    return _mos_instance


async def mos_add_conversation(user_msg: str, assistant_msg: str, user_id: str = "bashara") -> None:
    """Store a conversation pair in MemoryOS."""
    try:
        mos = get_memoryos(user_id)
        await asyncio.to_thread(mos.add_memory, user_msg, assistant_msg)
    except Exception as exc:
        logger.warning("mos_add_conversation failed: %s", exc)


async def mos_retrieve_context(query: str, user_id: str = "bashara") -> str:
    """Retrieve relevant long-term context from MemoryOS."""
    try:
        mos = get_memoryos(user_id)
        result = await asyncio.to_thread(mos.retrieve, query)
        return str(result.get("context", "") or "")
    except Exception as exc:
        logger.warning("mos_retrieve_context failed: %s", exc)
        return ""


async def mos_get_stats(user_id: str = "bashara") -> dict[str, Any]:
    """Return MemoryOS tier statistics."""
    try:
        mos = get_memoryos(user_id)
        return await asyncio.to_thread(mos.get_stats)
    except Exception as exc:
        return {"error": str(exc)}
