"""Audit logger — immutable action log for compliance.

Tracks all agent actions with:
- Who (user_id)
- What (action, agent, tool calls)
- When (timestamp)
- Outcome (success/failure, cost)

Stores to SQLite via aiosqlite (existing dependency).
Does NOT log user message content (privacy requirement).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default audit log path
AUDIT_DB_PATH = Path("data/audit.db")


@dataclass
class AuditEvent:
    """An immutable audit log entry."""

    event_id: str
    timestamp: float
    user_id: int
    session_id: str
    agent_name: str
    action_type: str  # "route", "execute", "tool_call", "error", "budget"
    success: bool
    cost_usd: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AuditLogger:
    """Compliance-grade audit logging.

    Writes to SQLite for persistence across bot restarts.
    Also keeps recent entries in memory for fast query.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or AUDIT_DB_PATH
        self._memory_log: List[AuditEvent] = []
        self._db_initialized = False

    async def _ensure_db(self) -> None:
        """Create audit table if it doesn't exist."""
        if self._db_initialized:
            return

        try:
            import aiosqlite

            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(str(self._db_path)) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        event_id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        user_id INTEGER NOT NULL,
                        session_id TEXT,
                        agent_name TEXT,
                        action_type TEXT,
                        success INTEGER,
                        cost_usd REAL DEFAULT 0,
                        model_used TEXT,
                        tokens_used INTEGER DEFAULT 0,
                        latency_ms INTEGER DEFAULT 0,
                        metadata TEXT
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                    ON audit_log(timestamp)
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_user
                    ON audit_log(user_id)
                """)
                await db.commit()

            self._db_initialized = True
            logger.info("Audit DB initialized: %s", self._db_path)
        except ImportError:
            logger.warning("aiosqlite not available — audit log in memory only")
            self._db_initialized = True
        except Exception as e:
            logger.error("Failed to init audit DB: %s", e)

    async def log(
        self,
        user_id: int,
        agent_name: str,
        action_type: str,
        success: bool,
        session_id: str = "",
        cost_usd: float = 0.0,
        model_used: str = "",
        tokens_used: int = 0,
        latency_ms: int = 0,
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """Record an audit event.

        Args:
            user_id: Telegram user ID.
            agent_name: Agent that performed the action.
            action_type: Type of action.
            success: Whether the action succeeded.
            session_id: Session identifier.
            cost_usd: Cost incurred.
            model_used: LLM model used.
            tokens_used: Total tokens consumed.
            latency_ms: Execution time in milliseconds.
            metadata: Additional context (no PII).

        Returns:
            The created AuditEvent.
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4())[:12],
            timestamp=time.time(),
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name,
            action_type=action_type,
            success=success,
            cost_usd=cost_usd,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

        # Store in memory
        self._memory_log.append(event)
        if len(self._memory_log) > 5000:
            self._memory_log = self._memory_log[-5000:]

        # Persist to SQLite
        await self._persist(event)

        return event

    async def _persist(self, event: AuditEvent) -> None:
        """Write event to SQLite."""
        await self._ensure_db()

        try:
            import aiosqlite

            async with aiosqlite.connect(str(self._db_path)) as db:
                await db.execute(
                    """INSERT INTO audit_log
                       (event_id, timestamp, user_id, session_id, agent_name,
                        action_type, success, cost_usd, model_used,
                        tokens_used, latency_ms, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.event_id,
                        event.timestamp,
                        event.user_id,
                        event.session_id,
                        event.agent_name,
                        event.action_type,
                        1 if event.success else 0,
                        event.cost_usd,
                        event.model_used,
                        event.tokens_used,
                        event.latency_ms,
                        json.dumps(event.metadata),
                    ),
                )
                await db.commit()
        except ImportError:
            pass  # No aiosqlite — memory-only mode
        except Exception as e:
            logger.error("Failed to persist audit event: %s", e)

    async def query(
        self,
        limit: int = 50,
        action_type: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Query recent audit events from memory.

        Args:
            limit: Max events to return.
            action_type: Filter by action type.
            agent_name: Filter by agent name.

        Returns:
            List of AuditEvents, newest first.
        """
        events = self._memory_log[:]

        if action_type:
            events = [e for e in events if e.action_type == action_type]
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]

        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_summary(self, hours: float = 24) -> Dict[str, Any]:
        """Get audit summary for the last N hours.

        Args:
            hours: Lookback period.

        Returns:
            Summary dict with counts and costs.
        """
        cutoff = time.time() - hours * 3600
        recent = [e for e in self._memory_log if e.timestamp >= cutoff]

        total_cost = sum(e.cost_usd for e in recent)
        success_count = sum(1 for e in recent if e.success)

        action_counts: Dict[str, int] = {}
        agent_counts: Dict[str, int] = {}

        for e in recent:
            action_counts[e.action_type] = action_counts.get(e.action_type, 0) + 1
            agent_counts[e.agent_name] = agent_counts.get(e.agent_name, 0) + 1

        return {
            "period_hours": hours,
            "total_events": len(recent),
            "success_count": success_count,
            "failure_count": len(recent) - success_count,
            "total_cost_usd": round(total_cost, 4),
            "by_action": action_counts,
            "by_agent": agent_counts,
        }

    def format_audit_html(self, events: List[AuditEvent]) -> str:
        """Format audit events as HTML for Telegram."""
        if not events:
            return "<b>No audit events found.</b>"

        lines = [f"<b>Audit Log</b> ({len(events)} events)\n"]

        for e in events[:20]:
            from datetime import datetime
            ts = datetime.fromtimestamp(e.timestamp).strftime("%m/%d %H:%M:%S")
            icon = "✅" if e.success else "❌"
            lines.append(
                f"{icon} <code>{ts}</code> "
                f"<b>{e.agent_name}</b> {e.action_type} "
                f"${e.cost_usd:.4f} {e.latency_ms}ms"
            )

        return "\n".join(lines)
