"""
core/temporal_graph.py
TemporalKnowledgeGraph — SQLite-backed knowledge graph for factual grounding.

Anti-hallucination pillar #3: KG validation stores verified facts and prevents
the model from contradicting its own previously confirmed knowledge.

Stores facts with subject, predicate, object, timestamp, and confidence.
Provides query and validation methods to cross-check LLM claims.

Usage:
    kg = TemporalKnowledgeGraph(":memory:")  # for testing
    kg = TemporalKnowledgeGraph("data/temporal_graph.db")  # for persistence
    kg.add_fact("Bashara", "lives_in", "Tokyo", "2026-04-21")
    results = kg.query("Bashara", "lives_in")
    kg.validate_fact("Bashara", "lives_in", "Tokyo")  # returns (True, confidence)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite


class TemporalKnowledgeGraph:
    """
    SQLite-backed temporal knowledge graph for fact storage and validation.

    Facts are stored as (subject, predicate, object, timestamp) quadruples
    with an optional confidence score. This enables:
    - Query by subject/predicate/object pattern
    - Validation against stored facts
    - Temporal reasoning (facts have timestamps)

    The graph uses SQLite for persistence and aiosqlite for async operations.
    """

    def __init__(self, db_path: str = "data/temporal_graph.db"):
        """
        Initialize the TemporalKnowledgeGraph.

        Args:
            db_path: Path to SQLite database file. Use ":memory:" for RAM-only.
        """
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None
        self._init_done = False

    async def _ensure_init(self) -> None:
        """Ensure database is initialized (create tables if needed)."""
        if self._init_done:
            return

        # Ensure parent directory exists
        db_dir = Path(self.db_path).parent
        if db_dir != Path(".") and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)

        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject)
        """)
        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate)
        """)
        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_timestamp ON facts(timestamp)
        """)

        await self._conn.commit()
        self._init_done = True

    async def _get_conn(self) -> aiosqlite.Connection:
        """Get connection, initializing if needed."""
        if self._conn is None:
            await self._ensure_init()
        return self._conn  # type: ignore

    def add_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        timestamp: str | None = None,
        confidence: float = 1.0,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """
        Add a fact to the knowledge graph (async, returns coroutine).

        Args:
            subject: The subject entity (e.g., "Bashara")
            predicate: The relationship (e.g., "lives_in")
            object: The object value (e.g., "Tokyo")
            timestamp: ISO timestamp when the fact is valid from (default: now)
            confidence: Confidence score 0.0-1.0 (default 1.0)
            source: Source document or agent that provided this fact
            metadata: Optional dict of additional properties

        Returns:
            Coroutine that resolves to the row ID of the inserted fact
        """
        async def _add() -> int:
            conn = await self._get_conn()
            ts = timestamp or datetime.now(UTC).isoformat()
            created = datetime.now(UTC).isoformat()
            meta_json = json.dumps(metadata) if metadata else None

            cursor = await conn.execute(
                """
                INSERT INTO facts (subject, predicate, object, timestamp, confidence, source, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (subject, predicate, object, ts, confidence, source, meta_json, created),
            )
            await conn.commit()
            return cursor.lastrowid or 0

        return _add()  # type: ignore[reportReturnType]

    def query(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query facts matching the given pattern (async, returns coroutine).

        Args:
            subject: Filter by subject (None = any)
            predicate: Filter by predicate (None = any)
            object: Filter by object (None = any)
            since: Only return facts since this ISO timestamp
            limit: Maximum number of results (default 100)

        Returns:
            Coroutine that resolves to list of fact dicts
        """
        async def _query() -> list[dict[str, Any]]:
            conn = await self._get_conn()

            conditions = []
            params: list[Any] = []

            if subject is not None:
                conditions.append("subject = ?")
                params.append(subject)
            if predicate is not None:
                conditions.append("predicate = ?")
                params.append(predicate)
            if object is not None:
                conditions.append("object = ?")
                params.append(object)
            if since is not None:
                conditions.append("timestamp >= ?")
                params.append(since)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cursor = await conn.execute(
                f"""
                SELECT id, subject, predicate, object, timestamp, confidence, source, metadata, created_at
                FROM facts
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                [*params, limit],
            )
            rows = await cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "subject": row["subject"],
                    "predicate": row["predicate"],
                    "object": row["object"],
                    "timestamp": row["timestamp"],
                    "confidence": row["confidence"],
                    "source": row["source"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

        return _query()  # type: ignore[reportReturnType]

    def validate_fact(
        self,
        subject: str,
        predicate: str,
        object: str | None = None,
        min_confidence: float = 0.7,
    ) -> tuple[bool, float]:
        """
        Validate whether a fact is stored in the KG with sufficient confidence.

        Returns (is_valid, max_confidence) where:
        - is_valid: True if fact exists with confidence >= min_confidence
        - max_confidence: Highest confidence among matching facts

        Args:
            subject: Subject to validate
            predicate: Predicate to validate
            object: Optional object to validate (None = check any object for this subject+predicate)
            min_confidence: Minimum confidence threshold (default 0.7)

        Returns:
            Coroutine that resolves to (bool, float) tuple
        """
        async def _validate() -> tuple[bool, float]:
            conn = await self._get_conn()

            if object is not None:
                cursor = await conn.execute(
                    """
                    SELECT MAX(confidence) as max_conf
                    FROM facts
                    WHERE subject = ? AND predicate = ? AND object = ? AND confidence >= ?
                    """,
                    (subject, predicate, object, min_confidence),
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT MAX(confidence) as max_conf
                    FROM facts
                    WHERE subject = ? AND predicate = ? AND confidence >= ?
                    """,
                    (subject, predicate, min_confidence),
                )

            row = await cursor.fetchone()
            if row is None or row["max_conf"] is None:
                return False, 0.0

            max_conf = float(row["max_conf"])
            return max_conf >= min_confidence, max_conf

        return _validate()  # type: ignore[reportReturnType]

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._init_done = False


# Sync wrapper for non-async contexts
def get_temporal_graph(db_path: str = "data/temporal_graph.db") -> TemporalKnowledgeGraph:
    """Get or create a TemporalKnowledgeGraph instance."""
    return TemporalKnowledgeGraph(db_path)
