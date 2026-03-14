"""Session state management — save/resume sessions with agent context.

Persists session state including:
- Conversation thread history
- Agent routing decisions
- Cost tracking per session
- User context variables

Storage: SQLite via aiosqlite (existing dependency).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SESSION_DB_PATH = Path("data/sessions.db")


@dataclass
class Session:
    """A saveable session with agent context."""

    session_id: str
    user_id: int
    chat_id: int
    name: str
    created_at: float
    last_active: float
    status: str = "active"  # active, saved, archived

    # Thread context (from agents.py ACTIVE_THREADS)
    thread_id: Optional[str] = None
    thread_history: List[Dict[str, Any]] = field(default_factory=list)

    # Routing history for this session
    routing_decisions: List[Dict[str, Any]] = field(default_factory=list)

    # Cost tracking
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    task_count: int = 0

    # User context (preferences, project info)
    context_vars: Dict[str, Any] = field(default_factory=dict)

    # Tags for organization
    tags: List[str] = field(default_factory=list)


class SessionManager:
    """Manage session lifecycle: create, save, resume, list.

    Persists to SQLite for durability across bot restarts.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or SESSION_DB_PATH
        self._active_sessions: Dict[int, Session] = {}  # user_id → Session
        self._db_initialized = False

    async def _ensure_db(self) -> None:
        """Create sessions table if it doesn't exist."""
        if self._db_initialized:
            return

        try:
            import aiosqlite

            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(str(self._db_path)) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        chat_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        last_active REAL NOT NULL,
                        status TEXT DEFAULT 'saved',
                        thread_id TEXT,
                        thread_history TEXT,
                        routing_decisions TEXT,
                        total_cost_usd REAL DEFAULT 0,
                        total_tokens INTEGER DEFAULT 0,
                        task_count INTEGER DEFAULT 0,
                        context_vars TEXT,
                        tags TEXT
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_user
                    ON sessions(user_id)
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_name
                    ON sessions(user_id, name)
                """)
                await db.commit()

            self._db_initialized = True
            logger.info("Sessions DB initialized: %s", self._db_path)
        except ImportError:
            logger.warning("aiosqlite not available — sessions in memory only")
            self._db_initialized = True
        except Exception as e:
            logger.error("Failed to init sessions DB: %s", e)

    def get_or_create_session(
        self,
        user_id: int,
        chat_id: int,
        thread_id: Optional[str] = None,
    ) -> Session:
        """Get the active session for a user, or create a new one."""
        if user_id in self._active_sessions:
            session = self._active_sessions[user_id]
            session.last_active = time.time()
            return session

        session = Session(
            session_id=str(uuid.uuid4())[:12],
            user_id=user_id,
            chat_id=chat_id,
            name=f"session_{int(time.time())}",
            created_at=time.time(),
            last_active=time.time(),
            thread_id=thread_id,
        )
        self._active_sessions[user_id] = session
        return session

    def get_active_session(self, user_id: int) -> Optional[Session]:
        """Get the current active session for a user."""
        return self._active_sessions.get(user_id)

    def track_task(
        self,
        user_id: int,
        agent_name: str,
        model: str,
        cost_usd: float,
        tokens: int,
        routing_decision: Optional[Dict] = None,
    ) -> None:
        """Track a task execution within the active session."""
        session = self._active_sessions.get(user_id)
        if not session:
            return

        session.total_cost_usd += cost_usd
        session.total_tokens += tokens
        session.task_count += 1
        session.last_active = time.time()

        if routing_decision:
            session.routing_decisions.append(routing_decision)
            # Keep last 100 routing decisions per session
            if len(session.routing_decisions) > 100:
                session.routing_decisions = session.routing_decisions[-100:]

    async def save_session(
        self,
        user_id: int,
        name: Optional[str] = None,
    ) -> Optional[Session]:
        """Save the active session to persistent storage.

        Args:
            user_id: Telegram user ID.
            name: Optional name for the session.

        Returns:
            The saved Session, or None if no active session.
        """
        session = self._active_sessions.get(user_id)
        if not session:
            return None

        if name:
            session.name = name
        session.status = "saved"
        session.last_active = time.time()

        # Capture thread history from agents.py
        try:
            from agents import get_thread_context
            if session.thread_id:
                thread_ctx = get_thread_context(session.thread_id)
                session.thread_history = thread_ctx or []
        except Exception:
            pass

        await self._persist_session(session)
        return session

    async def resume_session(
        self,
        user_id: int,
        name: str,
    ) -> Optional[Session]:
        """Resume a previously saved session.

        Args:
            user_id: Telegram user ID.
            name: Session name to resume.

        Returns:
            The resumed Session, or None if not found.
        """
        session = await self._load_session(user_id, name)
        if not session:
            return None

        session.status = "active"
        session.last_active = time.time()
        self._active_sessions[user_id] = session

        # Restore thread context
        if session.thread_id and session.thread_history:
            try:
                from agents import ACTIVE_THREADS
                ACTIVE_THREADS[session.thread_id] = session.thread_history
            except Exception:
                pass

        return session

    async def list_sessions(
        self,
        user_id: int,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List saved sessions for a user.

        Returns:
            List of session summary dicts.
        """
        await self._ensure_db()
        sessions = []

        try:
            import aiosqlite

            async with aiosqlite.connect(str(self._db_path)) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """SELECT session_id, name, created_at, last_active,
                              status, total_cost_usd, total_tokens, task_count, tags
                       FROM sessions
                       WHERE user_id = ?
                       ORDER BY last_active DESC
                       LIMIT ?""",
                    (user_id, limit),
                )
                rows = await cursor.fetchall()

                for row in rows:
                    sessions.append({
                        "session_id": row["session_id"],
                        "name": row["name"],
                        "created_at": row["created_at"],
                        "last_active": row["last_active"],
                        "status": row["status"],
                        "total_cost_usd": row["total_cost_usd"],
                        "total_tokens": row["total_tokens"],
                        "task_count": row["task_count"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                    })
        except ImportError:
            pass
        except Exception as e:
            logger.error("Failed to list sessions: %s", e)

        return sessions

    async def delete_session(self, user_id: int, name: str) -> bool:
        """Delete a saved session."""
        await self._ensure_db()

        try:
            import aiosqlite

            async with aiosqlite.connect(str(self._db_path)) as db:
                cursor = await db.execute(
                    "DELETE FROM sessions WHERE user_id = ? AND name = ?",
                    (user_id, name),
                )
                await db.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("Failed to delete session: %s", e)
            return False

    async def _persist_session(self, session: Session) -> None:
        """Write session to SQLite."""
        await self._ensure_db()

        try:
            import aiosqlite

            async with aiosqlite.connect(str(self._db_path)) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO sessions
                       (session_id, user_id, chat_id, name, created_at,
                        last_active, status, thread_id, thread_history,
                        routing_decisions, total_cost_usd, total_tokens,
                        task_count, context_vars, tags)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session.session_id,
                        session.user_id,
                        session.chat_id,
                        session.name,
                        session.created_at,
                        session.last_active,
                        session.status,
                        session.thread_id,
                        json.dumps(session.thread_history[-50:]),  # Keep last 50
                        json.dumps(session.routing_decisions[-50:]),
                        session.total_cost_usd,
                        session.total_tokens,
                        session.task_count,
                        json.dumps(session.context_vars),
                        json.dumps(session.tags),
                    ),
                )
                await db.commit()
        except ImportError:
            pass
        except Exception as e:
            logger.error("Failed to persist session: %s", e)

    async def _load_session(
        self,
        user_id: int,
        name: str,
    ) -> Optional[Session]:
        """Load session from SQLite."""
        await self._ensure_db()

        try:
            import aiosqlite

            async with aiosqlite.connect(str(self._db_path)) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """SELECT * FROM sessions
                       WHERE user_id = ? AND name = ?""",
                    (user_id, name),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                return Session(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    chat_id=row["chat_id"],
                    name=row["name"],
                    created_at=row["created_at"],
                    last_active=row["last_active"],
                    status=row["status"],
                    thread_id=row["thread_id"],
                    thread_history=json.loads(row["thread_history"]) if row["thread_history"] else [],
                    routing_decisions=json.loads(row["routing_decisions"]) if row["routing_decisions"] else [],
                    total_cost_usd=row["total_cost_usd"],
                    total_tokens=row["total_tokens"],
                    task_count=row["task_count"],
                    context_vars=json.loads(row["context_vars"]) if row["context_vars"] else {},
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                )
        except ImportError:
            return None
        except Exception as e:
            logger.error("Failed to load session: %s", e)
            return None

    def format_sessions_html(self, sessions: List[Dict[str, Any]]) -> str:
        """Format session list as HTML for Telegram."""
        if not sessions:
            return "<b>No saved sessions.</b>"

        lines = [f"<b>Saved Sessions</b> ({len(sessions)})\n"]

        for s in sessions:
            from datetime import datetime
            ts = datetime.fromtimestamp(s["last_active"]).strftime("%m/%d %H:%M")
            status_icon = {"active": "🟢", "saved": "💾", "archived": "📦"}.get(
                s["status"], "⚪"
            )
            lines.append(
                f"{status_icon} <b>{s['name']}</b>\n"
                f"   {ts} | {s['task_count']} tasks | "
                f"${s['total_cost_usd']:.4f} | "
                f"{s['total_tokens']:,} tokens"
            )

        lines.append(
            "\n<i>Resume: /resume &lt;name&gt;</i>"
        )
        return "\n".join(lines)
