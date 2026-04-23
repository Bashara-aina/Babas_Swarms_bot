"""
Session manager — wires mneme session continuity into startup/shutdown.
Injected into main.py on_startup and on_shutdown.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def on_startup_resume() -> str:
    """Called at bot startup — returns session resume block for system prompt."""
    try:
        from tools.mneme_session import build_session_resume_block, get_current_task
        task = get_current_task()
        if task.get("task"):
            logger.info("Resuming interrupted task: %s", task["task"])
        return build_session_resume_block()
    except Exception as e:
        logger.warning("session resume failed (non-fatal): %s", e)
        return ""


async def on_shutdown_checkpoint(summary: str = "Bot shutdown") -> None:
    """Called at bot shutdown — archives current session."""
    try:
        from tools.mneme_session import complete_current_task, get_current_task
        task = get_current_task()
        if task.get("task") and task.get("status") == "in_progress":
            complete_current_task(f"Interrupted at shutdown: {summary}")
            logger.info("Session checkpointed on shutdown")
    except Exception as e:
        logger.warning("session checkpoint failed: %s", e)
