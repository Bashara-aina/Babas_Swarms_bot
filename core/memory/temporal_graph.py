"""Temporal knowledge graph memory — async aiosqlite backend."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

GRAPH_DB = Path.home() / ".legionswarm" / "memory" / "temporal_graph.db"


class TemporalKnowledgeGraph:
    """Bi-temporal graph-like fact store backed by aiosqlite."""

    def __init__(self) -> None:
        GRAPH_DB.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = str(GRAPH_DB)
        self._initialized = False

    async def _get_conn(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self._db_path)
        if not self._initialized:
            await self._init_db(conn)
            self._initialized = True
        return conn

    async def _init_db(self, conn: aiosqlite.Connection) -> None:
        await conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                entity_type TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER REFERENCES entities(id),
                predicate TEXT NOT NULL,
                object_text TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                valid_from TEXT DEFAULT (datetime('now')),
                valid_until TEXT,
                source TEXT,
                UNIQUE(subject_id, predicate, object_text, valid_until)
            );
            CREATE INDEX IF NOT EXISTS idx_rel_subject ON relationships(subject_id);
            CREATE INDEX IF NOT EXISTS idx_rel_pred ON relationships(predicate);
            """
        )
        await conn.commit()
        await self._seed_user(conn)

    async def _seed_user(self, conn: aiosqlite.Connection) -> None:
        try:
            await self._ensure_entity(conn, "Bashara", "person")
            await self._ensure_entity(conn, "LegionSwarm", "system")
            await self._ensure_entity(conn, "RTX 3060", "hardware")
            known = [
                ("Bashara", "lives_in", "Tokyo, Japan"),
                ("Bashara", "uses_system", "LegionSwarm"),
                ("Bashara", "studies", "Data Science / AI"),
                ("Bashara", "uses_hardware", "RTX 3060 12GB"),
                ("LegionSwarm", "runs_on", "Ubuntu 22.04"),
                ("LegionSwarm", "uses_local_model", "gemma4:e4b"),
            ]
            for subject, predicate, obj in known:
                await self._add_fact_inner(conn, subject, predicate, obj, confidence=1.0, source="seed")
        except Exception:
            pass

    async def _ensure_entity(self, conn: aiosqlite.Connection, name: str, entity_type: str = "general") -> int:
        await conn.execute(
            "INSERT OR IGNORE INTO entities (name, entity_type) VALUES (?, ?)",
            (name, entity_type),
        )
        await conn.commit()
        async with conn.execute("SELECT id FROM entities WHERE name = ?", (name,)) as cursor:
            row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def _add_fact_inner(
        self,
        conn: aiosqlite.Connection,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "conversation",
    ) -> None:
        subject_id = await self._ensure_entity(conn, subject)
        await conn.execute(
            """
            UPDATE relationships
            SET valid_until = datetime('now')
            WHERE subject_id = ?
              AND predicate = ?
              AND valid_until IS NULL
              AND object_text != ?
            """,
            (subject_id, predicate, obj),
        )
        await conn.execute(
            """
            INSERT OR IGNORE INTO relationships
            (subject_id, predicate, object_text, confidence, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (subject_id, predicate, obj, confidence, source),
        )
        await conn.commit()

    async def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "conversation",
    ) -> None:
        conn = await self._get_conn()
        try:
            await self._add_fact_inner(conn, subject, predicate, obj, confidence, source)
        finally:
            await conn.close()

    async def get_current_facts(self, subject: str) -> list[dict]:
        conn = await self._get_conn()
        try:
            async with conn.execute("SELECT id FROM entities WHERE name = ?", (subject,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                return []
            async with conn.execute(
                """
                SELECT predicate, object_text, confidence, valid_from
                FROM relationships
                WHERE subject_id = ? AND valid_until IS NULL
                ORDER BY confidence DESC
                """,
                (row[0],),
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {"predicate": r[0], "object": r[1], "confidence": r[2], "since": r[3]}
                for r in rows
            ]
        finally:
            await conn.close()

    async def get_history(self, subject: str, predicate: str) -> list[dict]:
        conn = await self._get_conn()
        try:
            async with conn.execute("SELECT id FROM entities WHERE name = ?", (subject,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                return []
            async with conn.execute(
                """
                SELECT object_text, valid_from, valid_until, confidence
                FROM relationships
                WHERE subject_id = ? AND predicate = ?
                ORDER BY valid_from ASC
                """,
                (row[0], predicate),
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {"value": r[0], "from": r[1], "until": r[2] or "now", "confidence": r[3]}
                for r in rows
            ]
        finally:
            await conn.close()

    def to_prompt_block(self) -> str:
        """Sync wrapper for prompt injection — runs async under the hood."""
        try:
            loop = asyncio.get_running_loop()
            future = asyncio.ensure_future(self._to_prompt_block_async())
            if loop.is_running():
                return self._to_prompt_block_sync_fallback()
            return loop.run_until_complete(future)
        except RuntimeError:
            return self._to_prompt_block_sync_fallback()

    def _to_prompt_block_sync_fallback(self) -> str:
        """Minimal sync fallback when called from within a running event loop."""
        import sqlite3
        try:
            conn = sqlite3.connect(self._db_path)
            row = conn.execute("SELECT id FROM entities WHERE name = ?", ("Bashara",)).fetchone()
            if not row:
                conn.close()
                return ""
            rows = conn.execute(
                "SELECT predicate, object_text FROM relationships WHERE subject_id = ? AND valid_until IS NULL",
                (row[0],),
            ).fetchall()
            conn.close()
            if not rows:
                return ""
            lines = ["[KNOWLEDGE GRAPH — verified facts about user]"]
            for r in rows:
                lines.append(f"  Bashara {r[0].replace('_', ' ')} {r[1]}")
            return "\n".join(lines)
        except Exception:
            return ""

    async def _to_prompt_block_async(self) -> str:
        facts = await self.get_current_facts("Bashara")
        if not facts:
            return ""
        lines = ["[KNOWLEDGE GRAPH — verified facts about user]"]
        for fact in facts:
            lines.append(f"  Bashara {fact['predicate'].replace('_', ' ')} {fact['object']}")
        return "\n".join(lines)
