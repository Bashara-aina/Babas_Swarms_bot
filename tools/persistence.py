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

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL,
                model TEXT,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                duration_ms INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_audit_ts
                ON audit_log(timestamp);

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                agent_key TEXT,
                context_json TEXT,
                status TEXT DEFAULT 'active',
                created_at REAL NOT NULL,
                last_active REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS instincts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                weight REAL DEFAULT 1.0,
                uses INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS response_cache (
                cache_key TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                agent TEXT NOT NULL,
                model TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
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


# ── Audit log ──────────────────────────────────────────────────────────────────

async def log_audit(
    action: str,
    detail: str,
    model: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
    duration_ms: int = 0,
    success: bool = True,
) -> None:
    """Write one audit row. Called from the audit hook."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO audit_log
               (timestamp, action, detail, model, tokens_in, tokens_out,
                duration_ms, success)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), action, detail, model or None,
             tokens_in, tokens_out, duration_ms, int(success)),
        )
        await db.commit()


async def get_audit_summary(hours: int = 24) -> dict[str, Any]:
    """Aggregate audit stats for the last *hours*."""
    cutoff = time.time() - hours * 3600
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # totals per action
        async with db.execute(
            """SELECT action, COUNT(*) as cnt,
                      SUM(tokens_in) as tin, SUM(tokens_out) as tout,
                      SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as errors
               FROM audit_log WHERE timestamp >= ?
               GROUP BY action ORDER BY cnt DESC""",
            (cutoff,),
        ) as cur:
            rows = [dict(r) for r in await cur.fetchall()]
        return {"hours": hours, "breakdown": rows}


async def get_audit_log(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent audit entries."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ── Sessions ───────────────────────────────────────────────────────────────────

async def save_session(
    session_id: str,
    name: str,
    thread_id: str,
    agent_key: str,
    context_json: str,
) -> None:
    """Persist a session snapshot."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO sessions
               (session_id, name, thread_id, agent_key, context_json,
                status, created_at, last_active)
               VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                 context_json=excluded.context_json,
                 last_active=excluded.last_active,
                 status='active'""",
            (session_id, name, thread_id, agent_key, context_json, now, now),
        )
        await db.commit()


async def resume_session(name_or_id: str) -> Optional[dict[str, Any]]:
    """Load a session by name or ID. Returns None if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM sessions
               WHERE (session_id = ? OR name = ?) AND status = 'active'
               ORDER BY last_active DESC LIMIT 1""",
            (name_or_id, name_or_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_sessions(limit: int = 20) -> list[dict[str, Any]]:
    """List all sessions ordered by last activity."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT session_id, name, thread_id, agent_key, status,
                      created_at, last_active
               FROM sessions ORDER BY last_active DESC LIMIT ?""",
            (limit,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def delete_session(name_or_id: str) -> bool:
    """Soft-delete a session. Returns True if a row was affected."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """UPDATE sessions SET status = 'deleted'
               WHERE session_id = ? OR name = ?""",
            (name_or_id, name_or_id),
        )
        await db.commit()
        return cur.rowcount > 0


# ── Instincts ──────────────────────────────────────────────────────────────────

async def add_instinct(
    category: str, content: str, source: str = "manual"
) -> int:
    """Insert a new instinct. Returns its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO instincts (category, content, source, created_at)
               VALUES (?, ?, ?, ?)""",
            (category, content, source, time.time()),
        )
        await db.commit()
        return cur.lastrowid  # type: ignore[return-value]


async def get_instincts(
    category: Optional[str] = None, limit: int = 30
) -> list[dict[str, Any]]:
    """Fetch instincts, optionally filtered by category."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category:
            sql = """SELECT * FROM instincts WHERE category = ?
                     ORDER BY weight DESC, uses DESC LIMIT ?"""
            params: tuple = (category, limit)
        else:
            sql = "SELECT * FROM instincts ORDER BY weight DESC, uses DESC LIMIT ?"
            params = (limit,)
        async with db.execute(sql, params) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def bump_instinct_use(instinct_id: int) -> None:
    """Increment the use counter for an instinct."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE instincts SET uses = uses + 1 WHERE id = ?",
            (instinct_id,),
        )
        await db.commit()


async def delete_instinct(instinct_id: int) -> bool:
    """Delete an instinct by ID. Returns True if removed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM instincts WHERE id = ?", (instinct_id,)
        )
        await db.commit()
        return cur.rowcount > 0


async def get_instinct_context(max_tokens: int = 300) -> str:
    """Build a prompt fragment from top instincts, capped at ~max_tokens chars.

    Uses a rough 1 token ≈ 4 chars heuristic.
    """
    instincts = await get_instincts(limit=50)
    if not instincts:
        return ""
    char_budget = max_tokens * 4
    lines: list[str] = []
    used = 0
    for inst in instincts:
        line = f"- [{inst['category']}] {inst['content']}"
        if used + len(line) > char_budget:
            break
        lines.append(line)
        used += len(line)
    if not lines:
        return ""
    return "## User Preferences & Learned Patterns\n" + "\n".join(lines) + "\n"


# ── Response cache ─────────────────────────────────────────────────────────────

async def cache_get(cache_key: str) -> Optional[str]:
    """Return cached response if it exists and hasn't expired."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT response FROM response_cache
               WHERE cache_key = ? AND expires_at > ?""",
            (cache_key, time.time()),
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def cache_set(
    cache_key: str,
    response: str,
    agent: str,
    model: str,
    tokens_used: int = 0,
    ttl: int = 86400,
) -> None:
    """Store a response in cache with TTL."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO response_cache
               (cache_key, response, agent, model, tokens_used,
                created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(cache_key) DO UPDATE SET
                 response=excluded.response,
                 expires_at=excluded.expires_at""",
            (cache_key, response, agent, model, tokens_used, now, now + ttl),
        )
        await db.commit()


async def cache_stats() -> dict[str, Any]:
    """Return cache hit/size statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN expires_at > ? THEN 1 ELSE 0 END) as active,
                      SUM(tokens_used) as tokens_saved
               FROM response_cache""",
            (time.time(),),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {"total": 0, "active": 0, "tokens_saved": 0}


async def cache_cleanup() -> int:
    """Remove expired cache entries. Returns count deleted."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM response_cache WHERE expires_at <= ?",
            (time.time(),),
        )
        await db.commit()
        return cur.rowcount
