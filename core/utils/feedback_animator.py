"""Micro-animations and feedback for user actions.

Provides satisfying visual feedback through animations,
toasts, and confirmation sequences.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)


class FeedbackAnimator:
    """Animated feedback for user actions."""

    @staticmethod
    async def success_animation(
        bot: Bot,
        chat_id: int,
        action: str,
        details: str = "",
    ) -> None:
        """Show success with smooth animation.
        
        Args:
            bot: Bot instance
            chat_id: Chat to send to
            action: Action description ("Thread switched", "File saved")
            details: Optional additional details
            
        Example:
            >>> await FeedbackAnimator.success_animation(
            ...     bot, chat_id,
            ...     action="Thread switched",
            ...     details="📌 Now working in: <b>pytorch_debug</b>"
            ... )
        """
        # Animation sequence
        frames = [
            f"⏳ {action}...",
            f"✅ {action}",
            f"✨ {action} ✨",
        ]
        
        # Send first frame
        msg = await bot.send_message(chat_id, frames[0])
        
        # Animate through frames
        for frame in frames[1:]:
            await asyncio.sleep(0.3)
            try:
                await msg.edit_text(frame)
            except Exception as exc:
                logger.debug("Animation frame failed: %s", exc)
                pass
        
        # Show final state with details
        if details:
            await asyncio.sleep(0.5)
            try:
                await msg.edit_text(
                    f"✅ <b>{action}</b>\n\n{details}",
                    parse_mode="HTML"
                )
            except Exception as exc:
                logger.debug("Final frame failed: %s", exc)

    @staticmethod
    async def show_toast(
        bot: Bot,
        chat_id: int,
        message: str,
        duration: float = 2.0,
        icon: str = "ℹ️",
    ) -> None:
        """Show temporary notification that auto-deletes.
        
        Args:
            bot: Bot instance
            chat_id: Chat to send to
            message: Toast message
            duration: Seconds before auto-delete (default 2.0)
            icon: Emoji icon (default "ℹ️")
            
        Example:
            >>> await FeedbackAnimator.show_toast(
            ...     bot, chat_id,
            ...     message="Copied to clipboard",
            ...     duration=1.5,
            ...     icon="📋"
            ... )
        """
        msg = await bot.send_message(chat_id, f"{icon} {message}")
        await asyncio.sleep(duration)
        try:
            await msg.delete()
        except Exception as exc:
            logger.debug("Toast deletion failed: %s", exc)

    @staticmethod
    async def progress_bar(
        message: Message,
        percent: int,
        label: str = "Progress",
    ) -> Message:
        """Show progress bar.
        
        Args:
            message: Message to reply to
            percent: Progress percentage (0-100)
            label: Progress label
            
        Returns:
            Status message for updates
            
        Example:
            >>> status = await FeedbackAnimator.progress_bar(message, 0, "Uploading")
            >>> for i in range(0, 101, 10):
            ...     await asyncio.sleep(0.5)
            ...     await FeedbackAnimator.update_progress_bar(status, i, "Uploading")
        """
        bar_length = 10
        filled = int((percent / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        text = f"📊 <b>{label}</b>\n\n{bar} {percent}%"
        
        return await message.answer(text, parse_mode="HTML")

    @staticmethod
    async def update_progress_bar(
        status_msg: Message,
        percent: int,
        label: str = "Progress",
    ) -> None:
        """Update progress bar.
        
        Args:
            status_msg: Status message from progress_bar()
            percent: New progress percentage (0-100)
            label: Progress label
        """
        bar_length = 10
        filled = int((percent / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        text = f"📊 <b>{label}</b>\n\n{bar} {percent}%"
        
        try:
            await status_msg.edit_text(text, parse_mode="HTML")
        except Exception as exc:
            logger.debug("Progress bar update failed: %s", exc)

    @staticmethod
    async def typing_indicator(
        bot: Bot,
        chat_id: int,
        duration: float = 3.0,
    ) -> None:
        """Show typing indicator for specified duration.
        
        Args:
            bot: Bot instance
            chat_id: Chat ID
            duration: Seconds to show typing (default 3.0)
            
        Example:
            >>> await FeedbackAnimator.typing_indicator(bot, chat_id, 2.0)
            >>> # Bot shows "typing..." for 2 seconds
        """
        try:
            await bot.send_chat_action(chat_id, "typing")
            await asyncio.sleep(duration)
        except Exception as exc:
            logger.debug("Typing indicator failed: %s", exc)

    @staticmethod
    async def celebration(
        bot: Bot,
        chat_id: int,
        achievement: str,
    ) -> None:
        """Show celebration animation for milestone.
        
        Args:
            bot: Bot instance
            chat_id: Chat ID
            achievement: Achievement description
            
        Example:
            >>> await FeedbackAnimator.celebration(
            ...     bot, chat_id,
            ...     achievement="100th message in this thread!"
            ... )
        """
        frames = [
            f"🎉 {achievement}",
            f"🎊 {achievement} 🎊",
            f"✨ {achievement} ✨",
            f"🎉 {achievement} 🎉",
        ]
        
        msg = await bot.send_message(chat_id, frames[0])
        
        for frame in frames[1:]:
            await asyncio.sleep(0.4)
            try:
                await msg.edit_text(frame)
            except Exception:
                break
