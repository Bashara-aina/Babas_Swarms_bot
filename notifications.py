# /home/newadmin/swarm-bot/notifications.py
"""Proactive notification system for important events."""

from __future__ import annotations
import logging
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)


class NotificationManager:
    """Proactive notifications for important events and alerts."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_rate_limit_approaching(
        self, user_id: int, model: str, usage: int, limit: int
    ):
        """Warn before hitting rate limit.

        Args:
            user_id: Telegram user ID
            model: Model name
            usage: Current usage count
            limit: Usage limit
        """
        percentage = (usage / limit) * 100

        await self.bot.send_message(
            user_id,
            f"⚠️ <b>Rate Limit Alert</b>\n\n"
            f"<b>Model:</b> <code>{model}</code>\n"
            f"<b>Usage:</b> {usage}/{limit} ({percentage:.0f}%)\n\n"
            f"<i>Consider using alternative models to avoid hitting limits.</i>",
            parse_mode="HTML",
        )

    async def notify_task_complete(
        self, user_id: int, task: str, duration: float, result_summary: str = None
    ):
        """Notify when long task finishes.

        Args:
            user_id: Telegram user ID
            task: Task description
            duration: Duration in seconds
            result_summary: Optional result summary
        """
        message = f"✅ <b>Task Complete!</b>\n\n{task}\n\n"
        if result_summary:
            message += f"{result_summary}\n\n"
        message += f"<i>Completed in {duration:.1f}s</i>"

        await self.bot.send_message(user_id, message, parse_mode="HTML")

    async def notify_error_pattern(
        self, user_id: int, error_type: str, count: int, suggestion: str = None
    ):
        """Alert on recurring errors.

        Args:
            user_id: Telegram user ID
            error_type: Type of error
            count: Number of occurrences
            suggestion: Optional fix suggestion
        """
        message = (
            f"🔴 <b>Pattern Detected</b>\n\n"
            f"You've encountered <b>{error_type}</b> {count} times recently.\n\n"
        )
        if suggestion:
            message += f"<b>Suggestion:</b> {suggestion}\n\n"
        message += "<i>Consider reviewing the root cause.</i>"

        await self.bot.send_message(user_id, message, parse_mode="HTML")

    async def notify_monitor_alert(
        self, user_id: int, monitor_name: str, status: str, details: str = None
    ):
        """Send monitoring alert.

        Args:
            user_id: Telegram user ID
            monitor_name: Monitor identifier
            status: Alert status
            details: Optional details
        """
        from formatters import ResponseFormatter

        message = ResponseFormatter.format_monitor_alert(monitor_name, status, details)
        await self.bot.send_message(user_id, message, parse_mode="HTML")

    async def notify_system_status(
        self, user_id: int, status: str, message: str = None
    ):
        """Notify about system status changes.

        Args:
            user_id: Telegram user ID
            status: Status level (info, warning, error)
            message: Status message
        """
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}
        icon = icons.get(status.lower(), "🔔")

        await self.bot.send_message(
            user_id,
            f"{icon} <b>System Status</b>\n\n{message or 'Status update'}",
            parse_mode="HTML",
        )

    async def notify_agent_switch(
        self, user_id: int, from_agent: str, to_agent: str, reason: str
    ):
        """Notify when agent auto-switches.

        Args:
            user_id: Telegram user ID
            from_agent: Original agent
            to_agent: New agent
            reason: Reason for switch
        """
        await self.bot.send_message(
            user_id,
            f"🔄 <b>Agent Switch</b>\n\n"
            f"<b>From:</b> {from_agent}\n"
            f"<b>To:</b> {to_agent}\n"
            f"<b>Reason:</b> {reason}",
            parse_mode="HTML",
        )

    async def notify_cache_hit(
        self, user_id: int, query: str, saved_time: float, show_notification: bool = False
    ):
        """Optionally notify on cache hits (for transparency).

        Args:
            user_id: Telegram user ID
            query: Query that hit cache
            saved_time: Time saved in seconds
            show_notification: Whether to actually send (default: False for silent)
        """
        if not show_notification:
            logger.info(f"Cache hit for user {user_id}, saved {saved_time:.1f}s")
            return

        await self.bot.send_message(
            user_id,
            f"⚡ <b>Instant Answer</b> (from cache)\n\n"
            f"<i>Saved {saved_time:.1f}s by reusing previous result</i>",
            parse_mode="HTML",
        )

    async def notify_feedback_request(
        self, user_id: int, response_id: str, agent: str
    ):
        """Request feedback on a response.

        Args:
            user_id: Telegram user ID
            response_id: Response identifier
            agent: Agent that generated response
        """
        import telegram_ui

        await self.bot.send_message(
            user_id,
            f"<i>How was this {agent} response?</i>",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.feedback_buttons(response_id),
        )
