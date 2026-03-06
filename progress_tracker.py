# /home/newadmin/swarm-bot/progress_tracker.py
"""Task progress tracking and visualization for Telegram."""

from __future__ import annotations
import time
import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup

import telegram_ui

logger = logging.getLogger(__name__)


class TaskProgressTracker:
    """Track and display multi-step task progress with visual indicators."""

    def __init__(self, bot: Bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.message = None
        self.message_id: Optional[int] = None
        self.current_step = 0
        self.total_steps = 0
        self.task_id = str(int(time.time()))
        self.start_time = time.time()
        self.last_update = 0
        self.min_update_interval = 0.5  # seconds

    async def start(self, task_description: str, total_steps: int):
        """Initialize progress tracking.

        Args:
            task_description: Human-readable task name
            total_steps: Total number of steps
        """
        self.total_steps = total_steps
        self.start_time = time.time()

        self.message = await self.bot.send_message(
            self.chat_id,
            f"🚀 <b>Starting:</b> {task_description}\n\n"
            f"Progress: 0/{total_steps}\n"
            f"[{self._render_progress_bar()}]",
            parse_mode="HTML",
        )
        self.message_id = self.message.message_id

    async def update(self, step: int, description: str, can_pause: bool = False):
        """Update progress.

        Args:
            step: Current step number (1-indexed)
            description: What's happening now
            can_pause: Whether task can be paused
        """
        if not self.message:
            logger.warning("Progress tracker not started")
            return

        self.current_step = step
        now = time.time()

        # Rate limit updates
        if now - self.last_update < self.min_update_interval:
            return

        progress_bar = self._render_progress_bar()
        percentage = int((step / self.total_steps) * 100)
        elapsed = int(now - self.start_time)

        try:
            await self.message.edit_text(
                f"{progress_bar}\n\n"
                f"<b>Step {step}/{self.total_steps}</b> ({percentage}%)\n"
                f"{description}\n\n"
                f"<i>Elapsed: {elapsed}s</i>",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.task_progress(
                    self.task_id, step, self.total_steps, can_pause
                ),
            )
            self.last_update = now
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                logger.warning(f"Progress update failed: {e}")

    async def complete(self, summary: str, show_stats: bool = True):
        """Mark task as complete.

        Args:
            summary: Final result summary
            show_stats: Show timing statistics
        """
        if not self.message:
            return

        elapsed = int(time.time() - self.start_time)
        stats = f"\n<i>Completed in {elapsed}s</i>" if show_stats else ""

        try:
            await self.message.edit_text(
                f"✅ <b>Task Complete!</b>\n\n{summary}{stats}", parse_mode="HTML"
            )
        except TelegramBadRequest:
            # If edit fails, send new message
            await self.bot.send_message(
                self.chat_id,
                f"✅ <b>Task Complete!</b>\n\n{summary}{stats}",
                parse_mode="HTML",
            )

    async def fail(self, error: str):
        """Mark task as failed.

        Args:
            error: Error message
        """
        if not self.message:
            return

        try:
            await self.message.edit_text(
                f"❌ <b>Task Failed</b>\n\n{error}", parse_mode="HTML"
            )
        except TelegramBadRequest:
            await self.bot.send_message(
                self.chat_id, f"❌ <b>Task Failed</b>\n\n{error}", parse_mode="HTML"
            )

    def _render_progress_bar(self, length: int = 10) -> str:
        """Render visual progress bar.

        Args:
            length: Bar length in characters

        Returns:
            Progress bar string like [████░░░░░░]
        """
        if self.total_steps == 0:
            return "[" + "░" * length + "]"

        filled = int((self.current_step / self.total_steps) * length)
        filled = max(0, min(filled, length))  # Clamp to valid range
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"

    def get_elapsed_time(self) -> float:
        """Get elapsed time since start.

        Returns:
            Elapsed seconds
        """
        return time.time() - self.start_time
