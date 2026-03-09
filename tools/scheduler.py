"""scheduler.py — Background task scheduler for Legion.

Manages recurring monitors, one-time scheduled tasks, and alert conditions.
Persists to SQLite so tasks survive bot restarts.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from aiogram import Bot

from tools import persistence

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages background asyncio tasks with SQLite persistence."""

    def __init__(self, bot: Bot, user_id: int):
        self._bot = bot
        self._user_id = user_id
        self._running: dict[str, asyncio.Task] = {}  # task_id → asyncio.Task

    async def start(self) -> None:
        """Load all active tasks from DB and start them."""
        tasks = await persistence.get_active_tasks()
        for task in tasks:
            self._schedule(task)
        if tasks:
            logger.info("Scheduler loaded %d active tasks", len(tasks))

    async def add_monitor(
        self,
        description: str,
        command: str,
        interval_sec: int,
        alert_condition: str = "",
    ) -> str:
        """Add a recurring monitoring task. Returns task_id."""
        task_id = uuid.uuid4().hex[:8]
        await persistence.add_scheduled_task(
            task_id=task_id,
            description=description,
            command=command,
            task_type="monitor",
            interval_sec=interval_sec,
            alert_condition=alert_condition,
        )
        task_dict = {
            "id": task_id,
            "description": description,
            "command": command,
            "task_type": "monitor",
            "interval_sec": interval_sec,
            "alert_condition": alert_condition,
        }
        self._schedule(task_dict)
        return task_id

    async def add_scheduled(
        self,
        description: str,
        command: str,
        run_at: float,
    ) -> str:
        """Add a one-time scheduled task. run_at is a unix timestamp."""
        task_id = uuid.uuid4().hex[:8]
        await persistence.add_scheduled_task(
            task_id=task_id,
            description=description,
            command=command,
            task_type="once",
            next_run=run_at,
        )
        task_dict = {
            "id": task_id,
            "description": description,
            "command": command,
            "task_type": "once",
            "next_run": run_at,
        }
        self._schedule(task_dict)
        return task_id

    async def cancel(self, task_id: str) -> str:
        """Cancel a running task."""
        if task_id in self._running:
            self._running[task_id].cancel()
            del self._running[task_id]
        await persistence.update_task_status(task_id, "cancelled")
        return f"cancelled task: {task_id}"

    async def list_tasks(self) -> str:
        """HTML-formatted list of all tasks."""
        tasks = await persistence.get_all_tasks()
        if not tasks:
            return "No scheduled tasks. Use <code>/monitor</code> or <code>/schedule</code> to add one."

        lines = ["<b>📋 Scheduled Tasks</b>\n"]
        for t in tasks:
            status_icon = {
                "active": "🟢", "paused": "⏸", "cancelled": "❌", "completed": "✅",
            }.get(t["status"], "⚪")

            tid = t["id"]
            desc = t["description"][:50]
            ttype = t["task_type"]

            if ttype == "monitor":
                interval = t.get("interval_sec", 0)
                interval_str = _format_interval(interval)
                lines.append(f"  {status_icon} <code>{tid}</code> {desc}")
                lines.append(f"    ↻ every {interval_str} | {t['status']}")
            elif ttype == "once":
                next_run = t.get("next_run", 0)
                when = datetime.fromtimestamp(next_run).strftime("%m/%d %H:%M")
                lines.append(f"  {status_icon} <code>{tid}</code> {desc}")
                lines.append(f"    ⏰ at {when} | {t['status']}")

            last = t.get("last_run", 0)
            if last:
                last_str = datetime.fromtimestamp(last).strftime("%m/%d %H:%M")
                lines.append(f"    last: {last_str}")

            has_alert = t.get("alert_condition", "")
            if has_alert:
                lines.append(f"    🔔 alert: <code>{has_alert[:40]}</code>")
            lines.append("")

        running = len(self._running)
        lines.append(f"<i>{running} running | /cancel &lt;id&gt; to stop</i>")
        return "\n".join(lines)

    def _schedule(self, task: dict) -> None:
        """Create an asyncio.Task for a scheduled item."""
        task_id = task["id"]
        task_type = task.get("task_type", "monitor")

        if task_id in self._running:
            self._running[task_id].cancel()

        if task_type == "monitor":
            coro = self._monitor_loop(task)
        elif task_type == "once":
            coro = self._once_task(task)
        else:
            logger.warning("Unknown task type: %s", task_type)
            return

        self._running[task_id] = asyncio.create_task(coro)
        logger.info("Scheduled task %s (%s)", task_id, task_type)

    async def _monitor_loop(self, task: dict) -> None:
        """Recurring execution loop."""
        task_id = task["id"]
        interval = task.get("interval_sec", 60)
        command = task["command"]
        alert_cond = task.get("alert_condition", "")

        try:
            while True:
                try:
                    result = await _run_command(command)
                    await persistence.update_task_last_run(task_id)
                    await persistence.record_task_execution(
                        task_id, result, success=True
                    )

                    # Check alert condition
                    if alert_cond:
                        should_alert = _eval_condition(alert_cond, result)
                        if should_alert:
                            await self._notify(
                                f"🔔 <b>Alert: {task['description']}</b>\n\n"
                                f"<pre>{result[:2000]}</pre>"
                            )
                except Exception as e:
                    logger.error("Monitor %s error: %s", task_id, e)
                    await persistence.record_task_execution(
                        task_id, str(e), success=False
                    )

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Monitor %s cancelled", task_id)

    async def _once_task(self, task: dict) -> None:
        """One-time delayed task."""
        task_id = task["id"]
        run_at = task.get("next_run", 0)
        delay = max(0, run_at - time.time())

        try:
            if delay > 0:
                await asyncio.sleep(delay)

            result = await _run_command(task["command"])
            await persistence.update_task_last_run(task_id)
            await persistence.record_task_execution(task_id, result, success=True)
            await persistence.update_task_status(task_id, "completed")

            await self._notify(
                f"✅ <b>Scheduled task done:</b> {task['description']}\n\n"
                f"<pre>{result[:2000]}</pre>"
            )
        except asyncio.CancelledError:
            logger.info("Scheduled task %s cancelled", task_id)
        except Exception as e:
            await persistence.record_task_execution(task_id, str(e), success=False)
            await self._notify(
                f"❌ <b>Task failed:</b> {task['description']}\n"
                f"<code>{e}</code>"
            )

        if task_id in self._running:
            del self._running[task_id]

    async def _notify(self, text: str) -> None:
        """Send notification to user via Telegram."""
        try:
            await self._bot.send_message(
                self._user_id, text, parse_mode="HTML"
            )
        except Exception as e:
            logger.error("Failed to send notification: %s", e)

    def shutdown(self) -> None:
        """Cancel all running tasks."""
        for task_id, task in self._running.items():
            task.cancel()
        self._running.clear()
        logger.info("Scheduler shutdown — all tasks cancelled")


def _format_interval(seconds: int) -> str:
    """Format seconds into a human-readable interval string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    elif seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h{m}m" if m else f"{h}h"
    else:
        return f"{seconds // 86400}d"


def _eval_condition(condition: str, result: str) -> bool:
    """Safely evaluate an alert condition against command output.

    The condition has access to `result` (the command output string)
    and `output` (alias for result).
    """
    try:
        return bool(eval(condition, {"__builtins__": {}}, {
            "result": result,
            "output": result,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "re": re,
        }))
    except Exception as e:
        logger.warning("Alert condition eval failed: %s — %s", condition, e)
        return False


async def _run_command(command: str) -> str:
    """Run a shell command and return output."""
    from computer_agent import run_shell
    return await run_shell(command, timeout=30)
