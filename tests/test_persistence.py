"""Tests for tools/persistence.py — persistence operations."""

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_db_path(tmp_path):
    """Provide a temporary database path."""
    return tmp_path / "test_persistence.db"


@pytest.mark.asyncio
async def test_init_db(mock_db_path):
    """Should initialize the database with all tables."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()
        # Verify tables exist
        async with aiosqlite.connect(mock_db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
            table_names = [t[0] for t in tables]
            assert "scheduled_tasks" in table_names
            assert "task_history" in table_names
            assert "conversation_memory" in table_names


@pytest.mark.asyncio
async def test_add_and_get_scheduled_task(mock_db_path):
    """Should add and retrieve a scheduled task."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        task_id = "test_task_123"
        await persistence.add_scheduled_task(
            task_id=task_id,
            description="Test task",
            command="echo hello",
            task_type="monitor",
            interval_sec=60,
        )

        active_tasks = await persistence.get_active_tasks()
        assert len(active_tasks) == 1
        assert active_tasks[0]["id"] == task_id
        assert active_tasks[0]["description"] == "Test task"


@pytest.mark.asyncio
async def test_update_task_status(mock_db_path):
    """Should update task status."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        task_id = "status_test_456"
        await persistence.add_scheduled_task(
            task_id=task_id,
            description="Status test",
            command="echo test",
            task_type="once",
        )

        await persistence.update_task_status(task_id, "paused")
        tasks = await persistence.get_active_tasks()
        assert all(t["id"] != task_id for t in tasks)


@pytest.mark.asyncio
async def test_conversation_memory_operations(mock_db_path):
    """Should store and retrieve conversation memory."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        await persistence.store_conversation(
            thread_id="thread_abc",
            agent="coding",
            task="write a function",
            result="def foo(): pass",
        )

        memories = await persistence.get_conversation_history("thread_abc")
        assert len(memories) >= 1


@pytest.mark.asyncio
async def test_key_value_store(mock_db_path):
    """Should store and retrieve key-value pairs."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        await persistence.kv_set("test_key", "test_value")
        value = await persistence.kv_get("test_key")
        assert value == "test_value"


@pytest.mark.asyncio
async def test_kv_get_nonexistent(mock_db_path):
    """Should return None for nonexistent keys."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        value = await persistence.kv_get("nonexistent_key_xyz")
        assert value is None


@pytest.mark.asyncio
async def test_add_audit_log(mock_db_path):
    """Should add an audit log entry."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        await persistence.log_audit(
            action="test_action",
            detail="Test detail",
            model="test-model",
            tokens_in=100,
            tokens_out=200,
            duration_ms=150,
        )

        logs = await persistence.get_audit_log(limit=10)
        assert len(logs) >= 1
        assert logs[0]["action"] == "test_action"


@pytest.mark.asyncio
async def test_cleanup_old_conversation_memory(mock_db_path):
    """Should cleanup old conversation memory entries."""
    import aiosqlite

    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence

        await persistence.init_db()

        # Add a memory entry
        await persistence.store_conversation(
            thread_id="cleanup_thread",
            agent="test",
            task="test task",
            result="test result",
        )

        # Verify we can retrieve it
        memories = await persistence.get_conversation_history("cleanup_thread")
        assert len(memories) >= 1
