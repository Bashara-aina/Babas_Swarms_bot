"""data/message_count.py — Track daily message count for self_report."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).parent / "conversation.db"


def load_message_count(days: int = 1) -> int:
    """Load message count for the last N days from conversation.db."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        cursor = conn.cursor()

        # Get count of messages in last N days
        cursor.execute(
            """
            SELECT COUNT(*) FROM conversation_history
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            """,
            (days,),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        # Fallback: try legacy messages table
        try:
            conn = sqlite3.connect(_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE 1=1")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0


def increment_message_count() -> None:
    """Increment the message counter (called by message handler)."""
    # This is called from the message processing path
    pass
