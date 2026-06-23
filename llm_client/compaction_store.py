"""
Persistent Compaction Store — SQLite + FTS5.

Provides searchable, persistent storage for compaction summaries across all sessions.
Uses FTS5 for full-text search so old summaries are queryable via 6-layer memory.

Schema:
    CREATE TABLE compactions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key       TEXT UNIQUE NOT NULL,   -- MD5 of compacted window
        summary         TEXT NOT NULL,           -- LLM-generated summary
        message_count   INTEGER NOT NULL,       -- how many messages were condensed
        model_used      TEXT NOT NULL,          -- model that generated the summary
        session_id      TEXT,                   -- optional session identifier
        created_at      REAL NOT NULL,          -- unix timestamp
        chars_saved     INTEGER NOT NULL,       -- original_size - compacted_size
        original_size   INTEGER NOT NULL,
        compacted_size  INTEGER NOT NULL,
        topic_tags      TEXT,                   -- JSON array of auto-detected topics
        quality_score   REAL                    -- self-assessed quality 0-1
    );

    -- FTS5 virtual table for full-text search across summaries
    CREATE VIRTUAL TABLE compactions_fts USING fts5(
        summary,
        topic_tags,
        content='compactions',
        content_rowid='id'
    );

    -- Triggers to keep FTS in sync
    CREATE TRIGGER compactions_ai AFTER INSERT ON compactions BEGIN
        INSERT INTO compactions_fts(rowid, summary, topic_tags)
        VALUES (new.id, new.summary, new.topic_tags);
    END;
    CREATE TRIGGER compactions_ad AFTER DELETE ON compactions BEGIN
        INSERT INTO compactions_fts(compactions_fts, rowid, summary, topic_tags)
        VALUES ('delete', old.id, old.summary, old.topic_tags);
    END;
    CREATE TRIGGER compactions_au AFTER UPDATE ON compactions BEGIN
        INSERT INTO compactions_fts(compactions_fts, rowid, summary, topic_tags)
        VALUES ('delete', old.id, old.summary, old.topic_tags);
        INSERT INTO compactions_fts(rowid, summary, topic_tags)
        VALUES (new.id, new.summary, new.topic_tags);
    END;

    -- Index for fast session lookups
    CREATE INDEX idx_compactions_session ON compactions(session_id);
    CREATE INDEX idx_compactions_created ON compactions(created_at DESC);

Usage:
    from llm_client.compaction_store import CompactionStore
    store = CompactionStore()

    # Store a summary
    store.store(cache_key="abc123", summary="Fixed auth bug...", message_count=47,
                model_used="MiniMax-M3", chars_saved=45000, original_size=95000,
                compacted_size=50000, topic_tags=["bugfix", "auth"])

    # Search old summaries
    results = store.search("auth bug fix decisions")
    for row in results:
        print(row["summary"], row["created_at"])

    # Get recent compactions for a session
    recent = store.get_recent(session_id="abc", limit=10)

    # Deduplicate: check if this exact conversation window was already compacted
    existing = store.find_similar(cache_key="abc123")
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Path ──────────────────────────────────────────────────────────────────────

_DB_PATH = Path.cwd() / ".session_state" / "compactions.db"
_LOCK = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local connection."""
    path = os.environ.get("COMPACTION_STORE_PATH", str(_DB_PATH))
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB page cache
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS compactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key       TEXT UNIQUE NOT NULL,
    summary         TEXT NOT NULL,
    message_count   INTEGER NOT NULL,
    model_used      TEXT NOT NULL DEFAULT 'minimax-coding-plan/MiniMax-M3',
    session_id      TEXT,
    created_at      REAL NOT NULL,
    chars_saved     INTEGER NOT NULL DEFAULT 0,
    original_size   INTEGER NOT NULL DEFAULT 0,
    compacted_size  INTEGER NOT NULL DEFAULT 0,
    topic_tags      TEXT,
    quality_score   REAL,
    tool_names      TEXT,
    metadata_       TEXT
);

CREATE INDEX IF NOT EXISTS idx_compactions_session
    ON compactions(session_id);
CREATE INDEX IF NOT EXISTS idx_compactions_created
    ON compactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_compactions_cache_key
    ON compactions(cache_key);

CREATE VIRTUAL TABLE IF NOT EXISTS compactions_fts USING fts5(
    summary,
    topic_tags,
    content='compactions',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS compactions_ai
    AFTER INSERT ON compactions BEGIN
        INSERT INTO compactions_fts(rowid, summary, topic_tags)
        VALUES (new.id, new.summary, new.topic_tags);
    END;

CREATE TRIGGER IF NOT EXISTS compactions_ad
    AFTER DELETE ON compactions BEGIN
        INSERT INTO compactions_fts(compactions_fts, rowid, summary, topic_tags)
        VALUES ('delete', old.id, old.summary, old.topic_tags);
    END;

CREATE TRIGGER IF NOT EXISTS compactions_au
    AFTER UPDATE ON compactions BEGIN
        INSERT INTO compactions_fts(compactions_fts, rowid, summary, topic_tags)
        VALUES ('delete', old.id, old.summary, old.topic_tags);
        INSERT INTO compactions_fts(rowid, summary, topic_tags)
        VALUES (new.id, new.summary, new.topic_tags);
    END;
"""

_INITTED = False
_INIT_LOCK = threading.Lock()


def _ensure_schema() -> None:
    global _INITTED
    if _INITTED:
        return
    with _INIT_LOCK:
        if _INITTED:
            return
        try:
            conn = _get_conn()
            conn.executescript(_SCHEMA)
            conn.commit()
            _INITTED = True
            logger.debug("CompactionStore schema initialized at %s", _DB_PATH)
        except Exception as e:
            logger.warning("Failed to init compaction store schema: %s", e)


# ── CompactionStore ────────────────────────────────────────────────────────────


class CompactionStore:
    """Persistent, searchable compaction summary store."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            os.environ["COMPACTION_STORE_PATH"] = db_path
        _ensure_schema()

    # ── Store ──────────────────────────────────────────────────────────────────

    def store(
        self,
        cache_key: str,
        summary: str,
        message_count: int,
        model_used: str = "minimax-coding-plan/MiniMax-M3",
        session_id: Optional[str] = None,
        chars_saved: int = 0,
        original_size: int = 0,
        compacted_size: int = 0,
        topic_tags: Optional[list[str]] = None,
        quality_score: Optional[float] = None,
        tool_names: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """Store a compaction summary. Returns the row ID."""
        tags_json = json.dumps(topic_tags or [], ensure_ascii=False) if topic_tags else "[]"
        tool_names_json = json.dumps(tool_names or [], ensure_ascii=False) if tool_names else "[]"
        metadata_json = json.dumps(metadata or {}, default=str, ensure_ascii=False) if metadata else None

        with _LOCK:
            try:
                conn = _get_conn()
                cursor = conn.execute(
                    """
                    INSERT OR REPLACE INTO compactions
                    (cache_key, summary, message_count, model_used, session_id,
                     created_at, chars_saved, original_size, compacted_size,
                     topic_tags, quality_score, tool_names, metadata_)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cache_key,
                        summary,
                        message_count,
                        model_used,
                        session_id,
                        time.time(),
                        chars_saved,
                        original_size,
                        compacted_size,
                        tags_json,
                        quality_score,
                        tool_names_json,
                        metadata_json,
                    ),
                )
                conn.commit()
                return cursor.lastrowid or 0
            except Exception as e:
                logger.warning("Failed to store compaction: %s", e)
                return 0

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 10,
        session_id: Optional[str] = None,
    ) -> list[dict]:
        """Full-text search across compaction summaries."""
        if not query or not query.strip():
            return []

        # Escape FTS5 special chars and add prefix matching
        fts_query = " OR ".join(f'"{t}"*' for t in query.strip().split() if t)

        with _LOCK:
            try:
                conn = _get_conn()
                sql = """
                    SELECT c.*,
                           bm25(compactions_fts) as rank,
                           highlight(compactions_fts, 0, '[', ']') as summary_hi
                    FROM compactions_fts
                    JOIN compactions c ON c.id = compactions_fts.rowid
                    WHERE compactions_fts MATCH ?
                    AND (? IS NULL OR c.session_id = ?)
                    ORDER BY rank
                    LIMIT ?
                """
                cursor = conn.execute(sql, (fts_query, session_id, session_id, limit))
                cols = [d[0] for d in cursor.description]  # type: ignore[reportUnknownMemberType]
                rows = cursor.fetchall()
                return [dict(zip(cols, row)) for row in rows]
            except Exception as e:
                logger.warning("CompactionStore search failed: %s", e)
                return []

    def get_recent(
        self,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Get most recent compaction summaries."""
        with _LOCK:
            try:
                conn = _get_conn()
                if session_id:
                    cursor = conn.execute(
                        """
                        SELECT * FROM compactions
                        WHERE session_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                        """,
                        (session_id, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM compactions
                        ORDER BY created_at DESC
                        LIMIT ?
                        """,
                        (limit,),
                    )
                cols = [d[0] for d in cursor.description]  # type: ignore[reportUnknownMemberType]
                rows = cursor.fetchall()
                return [dict(zip(cols, row)) for row in rows]
            except Exception as e:
                logger.warning("CompactionStore get_recent failed: %s", e)
                return []

    def find_similar(
        self,
        cache_key: str,
        session_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Find if this exact conversation window was already compacted."""
        with _LOCK:
            try:
                conn = _get_conn()
                cursor = conn.execute(
                    """
                    SELECT * FROM compactions
                    WHERE cache_key = ? AND (? IS NULL OR session_id = ?)
                    LIMIT 1
                    """,
                    (cache_key, session_id, session_id),
                )
                row = cursor.fetchone()
                if row:
                    cols = [d[0] for d in cursor.description]  # type: ignore[reportUnknownMemberType]
                    return dict(zip(cols, row))
            except Exception as e:
                logger.warning("CompactionStore find_similar failed: %s", e)
        return None

    def get_context_for_compaction(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> str:
        """Get relevant compaction summaries as a formatted string for LLM context.

        This is called BEFORE generating a new summary to give the LLM
        historical context about what was already compacted and how.
        """
        rows = self.search(query=query, limit=limit, session_id=session_id)
        if not rows:
            return ""

        parts = ["[Prior compaction summaries for context:]"]
        for i, row in enumerate(rows, 1):
            tags = json.loads(row.get("topic_tags", "[]"))
            tags_str = ", ".join(tags) if tags else "general"
            created = datetime.fromtimestamp(row["created_at"], tz=timezone.utc)
            created_str = created.strftime("%Y-%m-%d %H:%M")
            parts.append(
                f"\n--- Prior Summary {i} ({created_str}, {tags_str}) ---"
                f"\n{row['summary'][:500]}"
                f"\n(condensed from {row['message_count']} messages, "
                f"saved {row['chars_saved']:,} chars)"
            )
        return "\n".join(parts)

    # ── Stats ───────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return store statistics."""
        with _LOCK:
            try:
                conn = _get_conn()
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        SUM(chars_saved) as total_chars_saved,
                        SUM(message_count) as total_messages,
                        MAX(created_at) as last_compact_at,
                        AVG(quality_score) as avg_quality
                    FROM compactions
                    """
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "total_compactions": row[0] or 0,
                        "total_chars_saved": row[1] or 0,
                        "total_messages_condensed": row[2] or 0,
                        "last_compact_at": row[3],
                        "avg_quality": row[4],
                    }
            except Exception as e:
                logger.warning("CompactionStore stats failed: %s", e)
        return {}


# ── Singleton ──────────────────────────────────────────────────────────────────

_store: Optional[CompactionStore] = None


def get_compaction_store() -> CompactionStore:
    """Get the singleton CompactionStore instance."""
    global _store
    if _store is None:
        _store = CompactionStore()
    return _store
