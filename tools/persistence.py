"""persistence.py — Async SQLite wrapper for Legion.

Stores: scheduled tasks, task history, conversation memory, KV store.
All operations are async via aiosqlite.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

try:
    import aiosqlite
except ImportError:
    import subprocess, sys
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "aiosqlite", "--break-system-packages", "-q"],
        check=False,
    )
    import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "legion.db"


async def init_db() -> None:
    """Create all tables on first run. Safe to call multiple times."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                command TEXT NOT NULL,
                task_type TEXT NOT NULL,
                interval_sec INTEGER DEFAULT 0,
                next_run REAL NOT NULL,
                last_run REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                alert_condition TEXT DEFAULT '',
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                executed_at REAL NOT NULL,
                result TEXT,
                success INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS conversation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                task TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_conv_thread
                ON conversation_memory(thread_id);

            CREATE TABLE IF NOT EXISTS key_value_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at REAL
            );
        """)
        await db.commit()
    logger.info("Database initialized: %s", DB_PATH)


# ── Scheduled tasks ──────────────────────────────────────────────────────────

async def add_scheduled_task(
    task_id: str,
    description: str,
    command: str,
    task_type: str,
    interval_sec: int = 0,
    next_run: float = 0,
    alert_condition: str = "",
) -> None:
    """Insert a new scheduled task."""
    now = time.time()
    if next_run == 0:
        next_run = now
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO scheduled_tasks
               (id, description, command, task_type, interval_sec,
                next_run, status, alert_condition, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
            (task_id, description, command, task_type,
             interval_sec, next_run, alert_condition, now),
        )
        await db.commit()


async def get_active_tasks() -> list[dict[str, Any]]:
    """Get all active scheduled tasks."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM scheduled_tasks WHERE status = 'active'"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_task_status(task_id: str, status: str) -> None:
    """Update a task's status (active, paused, completed, cancelled)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduled_tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        await db.commit()


async def update_task_last_run(task_id: str) -> None:
    """Update last_run timestamp for a task."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduled_tasks SET last_run = ? WHERE id = ?",
            (now, task_id),
        )
        await db.commit()


async def record_task_execution(
    task_id: str, result: str, success: bool = True
) -> None:
    """Record a task execution in history."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO task_history (task_id, executed_at, result, success)
               VALUES (?, ?, ?, ?)""",
            (task_id, time.time(), result[:2000], int(success)),
        )
        await db.commit()


async def get_task_history(task_id: str, limit: int = 10) -> list[dict]:
    """Get recent execution history for a task."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM task_history WHERE task_id = ?
               ORDER BY executed_at DESC LIMIT ?""",
            (task_id, limit),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_all_tasks() -> list[dict[str, Any]]:
    """Get all tasks regardless of status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM scheduled_tasks ORDER BY created_at DESC"
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


# ── Conversation memory ──────────────────────────────────────────────────────

async def store_conversation(
    thread_id: str, agent: str, task: str, result: str
) -> None:
    """Store a conversation turn."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO conversation_memory
               (thread_id, agent, task, result, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (thread_id, agent, task, result[:1000], time.time()),
        )
        await db.commit()


async def get_conversation_history(
    thread_id: str, limit: int = 10
) -> list[dict]:
    """Get recent conversation history for a thread."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM conversation_memory
               WHERE thread_id = ? ORDER BY created_at DESC LIMIT ?""",
            (thread_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in reversed(rows)]


async def get_all_threads() -> list[dict]:
    """Get all thread IDs with counts and last activity."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT thread_id, COUNT(*) as turns,
                      MAX(created_at) as last_active
               FROM conversation_memory
               GROUP BY thread_id
               ORDER BY last_active DESC"""
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


# ── Key-value store ──────────────────────────────────────────────────────────

async def kv_set(key: str, value: str) -> None:
    """Set a key-value pair."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO key_value_store (key, value, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=?, updated_at=?""",
            (key, value, time.time(), value, time.time()),
        )
        await db.commit()


async def kv_get(key: str) -> Optional[str]:
    """Get a value by key."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM key_value_store WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def kv_delete(key: str) -> None:
    """Delete a key-value pair."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM key_value_store WHERE key = ?", (key,)
        )
        await db.commit()
