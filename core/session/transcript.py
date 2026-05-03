"""Session transcript store — SQLite-backed persistent transcript for all sessions.

Persists every conversation turn (user + assistant) to SQLite so sessions can be
resumed or audited later. File path: `data/session_transcripts.db`.

Schema:
    session_transcripts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,  -- 'user' or 'assistant'
        content TEXT NOT NULL,
        model_used TEXT,
        timestamp REAL NOT NULL
    )
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "session_transcripts.db")
_STORE: SessionTranscriptStore | None = None
_init_lock = asyncio.Lock()


def _ensure_db_dir() -> None:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)


class SessionTranscriptStore:
    """SQLite-backed transcript store using aiosqlite."""

    def __init__(self) -> None:
        self._db_path = _DB_PATH
        self._initialized = False

    async def init(self) -> None:
        """Create tables if they don't exist. Idempotent."""
        if self._initialized:
            return
        async with _init_lock:
            if self._initialized:
                return
            _ensure_db_dir()
            try:
                import aiosqlite

                async with aiosqlite.connect(self._db_path) as db:
                    await db.execute("""
                        CREATE TABLE IF NOT EXISTS session_transcripts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            thread_id TEXT,
                            user_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            model_used TEXT,
                            timestamp REAL NOT NULL
                        )
                    """)
                    await db.execute(
                        "CREATE INDEX IF NOT EXISTS idx_transcript_user_ts ON session_transcripts(user_id, timestamp)"
                    )
                    await db.commit()
                self._initialized = True
                logger.info("SessionTranscriptStore initialized at %s", self._db_path)
            except Exception as exc:
                logger.warning("SessionTranscriptStore init failed (non-fatal): %s", exc)

    async def save_turn(
        self,
        thread_id: str | None,
        user_id: str,
        role: str,
        content: str,
        model_used: str | None = None,
    ) -> None:
        """Persist a single conversation turn. Idempotent — errors are logged, not raised."""
        if not self._initialized:
            await self.init()
        try:
            import aiosqlite

            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """
                    INSERT INTO session_transcripts
                        (thread_id, user_id, role, content, model_used, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, user_id, role, content[:8000], model_used, datetime.now().timestamp()),
                )
                await db.commit()
        except Exception as exc:
            logger.debug("Transcript save_turn failed (non-fatal): %s", exc)

    async def get_transcript(
        self,
        thread_id: str,
        limit: int = 100,
    ) -> list[dict]:
        """Retrieve transcript for a thread."""
        if not self._initialized:
            await self.init()
        try:
            import aiosqlite

            async with aiosqlite.connect(self._db_path) as db, db.execute(
                """
                    SELECT thread_id, user_id, role, content, model_used, timestamp
                    FROM session_transcripts
                    WHERE thread_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                    """,
                (thread_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {
                    "thread_id": r[0],
                    "user_id": r[1],
                    "role": r[2],
                    "content": r[3],
                    "model_used": r[4],
                    "timestamp": r[5],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.debug("Transcript get_transcript failed (non-fatal): %s", exc)
            return []

    async def get_recent(self, user_id: str, limit: int = 50) -> list[dict]:
        """Get most recent turns for a user across all threads."""
        if not self._initialized:
            await self.init()
        try:
            import aiosqlite

            async with aiosqlite.connect(self._db_path) as db, db.execute(
                """
                    SELECT thread_id, user_id, role, content, model_used, timestamp
                    FROM session_transcripts
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                (user_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
            return list(
                reversed(
                    [
                        {
                            "thread_id": r[0],
                            "user_id": r[1],
                            "role": r[2],
                            "content": r[3],
                            "model_used": r[4],
                            "timestamp": r[5],
                        }
                        for r in rows
                    ]
                )
            )
        except Exception as exc:
            logger.debug("Transcript get_recent failed (non-fatal): %s", exc)
            return []

    async def list_threads(self) -> list[str]:
        """Return all distinct thread_ids."""
        if not self._initialized:
            await self.init()
        try:
            import aiosqlite

            async with aiosqlite.connect(self._db_path) as db:
                async with db.execute(
                    "SELECT DISTINCT thread_id FROM session_transcripts WHERE thread_id IS NOT NULL ORDER BY thread_id"
                ) as cursor:
                    rows = await cursor.fetchall()
            return [r[0] for r in rows if r[0]]
        except Exception as exc:
            logger.debug("Transcript list_threads failed (non-fatal): %s", exc)
            return []

    async def delete_thread(self, thread_id: str) -> None:
        """Delete all turns for a thread."""
        if not self._initialized:
            await self.init()
        try:
            import aiosqlite

            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    "DELETE FROM session_transcripts WHERE thread_id = ?",
                    (thread_id,),
                )
                await db.commit()
            logger.info("Deleted transcript for thread %s", thread_id)
        except Exception as exc:
            logger.debug("Transcript delete_thread failed (non-fatal): %s", exc)


def get_transcript_store() -> SessionTranscriptStore:
    """Get the module-level singleton."""
    global _STORE
    if _STORE is None:
        _STORE = SessionTranscriptStore()
    return _STORE
