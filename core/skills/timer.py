"""core/skills/timer.py — Real async timer skill that sends Telegram messages.

FIX: The old _timer_handler in productivity.py was a stub that just returned
a confirmation string without scheduling anything. This module provides a
working implementation using asyncio.create_task.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

# Global bot reference (set from main.py on_startup)
_bot_instance: Optional["Bot"] = None


def set_bot(bot: "Bot") -> None:
    """Called by main.py on_startup to provide bot access."""
    global _bot_instance
    _bot_instance = bot


async def execute(
    user_id: int,
    duration_seconds: int,
    reminder_text: str,
) -> str:
    """Set a real async timer that sends a Telegram message when done.

    Args:
        user_id: Telegram user ID to send the reminder to.
        duration_seconds: How long to wait before sending the reminder.
        reminder_text: The message to send when the timer expires.

    Returns:
        Confirmation string indicating the timer was set.
    """
    if duration_seconds <= 0:
        return "⚠️ Timer duration must be positive."
    if duration_seconds > 7200:
        return "⚠️ Timer cannot exceed 2 hours (7200 seconds)."

    if _bot_instance is None:
        logger.error("Timer: bot instance not set (call set_bot first)")
        return "❌ Timer service not initialized."

    bot = _bot_instance

    async def send_reminder() -> None:
        """Background task that sleeps and then sends the reminder."""
        try:
            await asyncio.sleep(duration_seconds)
            await bot.send_message(
                chat_id=user_id,
                text=f"⏰ Timer! {reminder_text}",
            )
            logger.info("Timer reminder sent to user %d", user_id)
        except Exception as e:
            logger.error("Timer failed for user %d: %e", user_id, e)

    # Create the background task - it runs independently of the handler
    asyncio.create_task(send_reminder())

    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    if minutes > 0 and seconds > 0:
        return f"✅ Timer set for {minutes} min {seconds} sec. I'll ping you when done."
    elif minutes > 0:
        return f"✅ Timer set for {minutes} minute(s). I'll ping you when done."
    else:
        return f"✅ Timer set for {seconds} second(s). I'll ping you when done."


def parse_timer_request(text: str) -> tuple[int, str]:
    """Parse a timer request text and extract duration and label.

    Handles formats like:
    - "set timer 5 min for meeting"
    - "timer 30 seconds"
    - "ingetin gw 10 menit"

    Returns:
        Tuple of (duration_seconds, reminder_text).
    """
    text_lower = text.lower()

    # Extract minutes
    minutes_match = re.search(r"(\d+)\s*(?:min|minute|menit|m)", text_lower)
    minutes = int(minutes_match.group(1)) if minutes_match else 0

    # Extract seconds
    seconds_match = re.search(r"(\d+)\s*(?:sec|second|detik|s)\b", text_lower)
    seconds = int(seconds_match.group(1)) if seconds_match else 0

    # Extract hours
    hours_match = re.search(r"(\d+)\s*(?:hour|jam|h)\b", text_lower)
    hours = int(hours_match.group(1)) if hours_match else 0

    total_seconds = minutes * 60 + seconds + hours * 3600

    # Default to 5 minutes if no duration found
    if total_seconds == 0:
        total_seconds = 300

    # Extract reminder label
    # Look for patterns like "for X" or "called X" or just use "Timer"
    label_match = re.search(
        r"(?:for|called|named|judul|pake)\s+['\"]?([\w\s]+?)['\"]?(?:\s*$|\s+but)",
        text,
        re.IGNORECASE,
    )
    if label_match:
        label = label_match.group(1).strip().strip("'\"")
    else:
        label = "Timer"

    return total_seconds, label


async def handle_timer_message(text: str, user_id: int) -> str:
    """Main entry point for the timer skill handler.

    Parses the user message, extracts timer parameters, and schedules
    the reminder.

    Args:
        text: The user's message requesting a timer.
        user_id: The Telegram user ID.

    Returns:
        Confirmation message indicating the timer was set.
    """
    duration_seconds, reminder_text = parse_timer_request(text)
    return await execute(user_id, duration_seconds, reminder_text)
