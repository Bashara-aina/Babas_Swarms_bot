# /home/newadmin/swarm-bot/progress_tracker.py
"""Task progress tracking with live Telegram message updates.

Edits a single message to show a progress bar and current step description,
so the user always knows what's happening during multi-step workflows.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


@dataclass
class ProgressStep:
    """One step in a tracked task."""
    description: str
    agent: str = ""
    result: str = ""
    done: bool = False


class TaskProgressTracker:
    """Display real-time progress for multi-step tasks.

    Usage::

        async with TaskProgressTracker(bot, chat_id, "Deploy WorkerNet", 4) as t:
            await t.step(1, "Analysing codebase", "debug")
            ...
            await t.done("All steps complete!")
    """

    _BAR_WIDTH = 10
    _EDIT_COOLDOWN = 1.0   # min seconds between edits

    def __init__(
        self,
        bot: Bot,
        chat_id: int,
        title: str,
        total_steps: int,
    ) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.title = title
        self.total_steps = total_steps
        self._current = 0
        self._msg: Any = None
        self._last_edit = 0.0
        self._steps: list[ProgressStep] = []

    # ── Context manager ────────────────────────────────────────────────────────

    async def __aenter__(self) -> "TaskProgressTracker":
        self._msg = await self.bot.send_message(
            self.chat_id,
            self._render(0, "Starting…"),
            parse_mode="HTML",
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        pass  # Final state is set by caller via done()

    # ── Public API ─────────────────────────────────────────────────────────────

    async def step(self, step: int, description: str, agent: str = "") -> None:
        """Advance to a step and update the progress message.

        Args:
            step: 1-based step number.
            description: Short description shown in the bar.
            agent: Agent name shown as sub-label.
        """
        self._current = step
        label = f"<b>{agent.upper()}</b> · {description}" if agent else description
        await self._edit(self._render(step, label))

    async def step_done(self, step: int, result_preview: str = "") -> None:
        """Mark a step as complete with optional result snippet."""
        snippet = result_preview.strip().replace("\n", " ")[:80]
        suffix = f" — <i>{snippet}</i>" if snippet else ""
        label = f"Step {step} done{suffix}"
        await self._edit(self._render(step, label, done=True))

    async def done(self, summary: str = "") -> None:
        """Mark the whole task as complete."""
        bar = "█" * self._BAR_WIDTH
        msg = (
            f"<b>✅ {self.title}</b>\n\n"
            f"[{bar}] 100%\n\n"
            + (summary or "All steps complete.")
        )
        await self._edit(msg, force=True)

    async def failed(self, reason: str) -> None:
        """Mark the task as failed."""
        pct = int(self._current / self.total_steps * 100) if self.total_steps else 0
        bar = self._progress_bar(self._current)
        msg = (
            f"<b>🔴 {self.title}</b>\n\n"
            f"[{bar}] {pct}%\n\n"
            f"<b>Failed at step {self._current}:</b>\n"
            f"<code>{reason[:300]}</code>"
        )
        await self._edit(msg, force=True)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _render(self, step: int, description: str, done: bool = False) -> str:
        bar = self._progress_bar(step)
        pct = int(step / self.total_steps * 100) if self.total_steps else 0
        icon = "✅" if done else "⚙️"
        return (
            f"<b>{icon} {self.title}</b>\n\n"
            f"[{bar}] {pct}% · {step}/{self.total_steps}\n\n"
            f"{description}"
        )

    def _progress_bar(self, step: int) -> str:
        filled = int(step / self.total_steps * self._BAR_WIDTH) if self.total_steps else 0
        return "█" * filled + "░" * (self._BAR_WIDTH - filled)

    async def _edit(self, text: str, force: bool = False) -> None:
        if self._msg is None:
            return
        now = time.monotonic()
        if not force and now - self._last_edit < self._EDIT_COOLDOWN:
            return
        try:
            await self._msg.edit_text(text, parse_mode="HTML")
            self._last_edit = now
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                logger.debug("Progress edit failed: %s", exc)
        except Exception as exc:
            logger.debug("Progress edit error: %s", exc)


def render_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Standalone progress bar renderer (for use outside tracker).

    Args:
        current: Current value.
        total: Max value.
        width: Bar width in characters.

    Returns:
        e.g. "████░░░░░░ 40%"
    """
    if total <= 0:
        return "░" * width + " 0%"
    filled = int(current / total * width)
    pct = int(current / total * 100)
    return "█" * filled + "░" * (width - filled) + f" {pct}%"
