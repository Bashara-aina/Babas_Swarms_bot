"""data/self_improvement_buffer.py — Store recent learnings for self_report."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).parent / "memory.db"


def _sync_get_recent_learnings(n: int = 10) -> list[str]:
    """Synchronous helper to retrieve recent learnings from memory.db."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        cursor = conn.cursor()

        # Try learning_logs table
        cursor.execute(
            """
            SELECT content FROM learning_logs
            ORDER BY created_at DESC LIMIT ?
            """,
            (n,),
        )
        rows = cursor.fetchall()
        conn.close()

        if rows:
            return [row[0] for row in rows if row[0]]

        # Fallback: try a generic key-value learning store
        try:
            conn = sqlite3.connect(_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT value FROM kv_store
                WHERE key LIKE '%learning%'
                ORDER BY created_at DESC LIMIT ?
                """,
                (n,),
            )
            rows = cursor.fetchall()
            conn.close()
            if rows:
                learnings = []
                for row in rows:
                    try:
                        val = json.loads(row[0])
                        if isinstance(val, str):
                            learnings.append(val)
                        elif isinstance(val, list):
                            learnings.extend(val)
                    except Exception:
                        learnings.append(row[0])
                return learnings
        except Exception:
            pass

        return []

    except Exception:
        return []


async def get_recent_learnings(n: int = 10) -> list[str]:
    """Retrieve the N most recent learning entries from memory.db."""
    return await asyncio.to_thread(_sync_get_recent_learnings, n)


def _sync_log_learning(content: str) -> None:
    """Synchronous helper to log a learning entry to memory.db."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        cursor.execute(
            "INSERT INTO learning_logs (content) VALUES (?)",
            (content,),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


async def log_learning(content: str) -> None:
    """Log a learning entry to memory.db."""
    await asyncio.to_thread(_sync_log_learning, content)
