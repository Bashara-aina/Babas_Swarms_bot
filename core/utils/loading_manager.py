"""Animated loading states with user cancellation capability.

Provides visual feedback during long operations with animated indicators
and cancellation buttons for better user control.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Tuple

from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)


class LoadingManager:
    """Manage animated loading indicators with cancellation."""

    @staticmethod
    async def show_progress(
        message: Message,
        task_name: str,
        bot: Bot,
    ) -> Tuple[Message, asyncio.Event]:
        """Show animated loading indicator with cancel button.
        
        Args:
            message: Original message from user
            task_name: Human-readable task description
            bot: Bot instance for sending messages
            
        Returns:
            Tuple of (status_message, cancel_event)
            Call cancel_event.set() when task completes
            
        Example:
            >>> status_msg, cancel = await LoadingManager.show_progress(
            ...     message, "Transcribing audio", bot
            ... )
            >>> try:
            ...     result = await long_operation()
            ...     cancel.set()
            ...     await status_msg.edit_text(f"✅ Done: {result}")
            ... except Exception as e:
            ...     cancel.set()
            ...     await status_msg.edit_text(f"❌ Error: {e}")
        """
        cancel_event = asyncio.Event()
        
        # Animation frames - hourglass effect
        frames = [
            f"⏳ {task_name}",
            f"⌛ {task_name}.",
            f"⏳ {task_name}..",
            f"⌛ {task_name}...",
        ]
        
        # Create cancel button
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Cancel", callback_data="loading:cancel")
        keyboard = builder.as_markup()
        
        # Send initial status message
        msg = await message.answer(
            frames[0],
            reply_markup=keyboard
        )
        
        # Background animation task
        async def _animate():
            """Cycle through animation frames until cancelled."""
            i = 0
            while not cancel_event.is_set():
                try:
                    await msg.edit_text(
                        frames[i % len(frames)],
                        reply_markup=keyboard
                    )
                    i += 1
                    await asyncio.sleep(0.5)
                except Exception as exc:
                    logger.debug("Animation frame update failed: %s", exc)
                    break
        
        # Start animation in background
        asyncio.create_task(_animate())
        
        return msg, cancel_event

    @staticmethod
    async def show_steps(
        message: Message,
        steps: list[str],
        bot: Bot,
    ) -> Message:
        """Show multi-step progress indicator.
        
        Args:
            message: Original message
            steps: List of step descriptions
            bot: Bot instance
            
        Returns:
            Status message that can be updated
            
        Example:
            >>> status = await LoadingManager.show_steps(
            ...     message, [
            ...         "Downloading file",
            ...         "Extracting text", 
            ...         "Analyzing content",
            ...         "Generating summary",
            ...     ], bot
            ... )
            >>> await LoadingManager.update_step(status, 1, "✅")
            >>> await LoadingManager.update_step(status, 2, "⏳")
        """
        lines = ["📋 <b>Progress</b>\n"]
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}️⃣ {step}... ⏳")
        
        text = "\n".join(lines)
        return await message.answer(text, parse_mode="HTML")

    @staticmethod
    async def update_step(
        status_msg: Message,
        step_index: int,
        state: str,
        steps: list[str] | None = None,
    ) -> None:
        """Update specific step status.
        
        Args:
            status_msg: Status message from show_steps()
            step_index: 0-based index of step to update
            state: "✅" (done), "⏳" (in progress), "❌" (failed)
            steps: Optional list of step descriptions (if not stored)
        """
        if not steps:
            # Try to extract from existing message
            return
        
        lines = ["📋 <b>Progress</b>\n"]
        for i, step in enumerate(steps):
            if i == step_index:
                icon = state
            elif i < step_index:
                icon = "✅"
            else:
                icon = "⏳"
            lines.append(f"{i+1}️⃣ {step}... {icon}")
        
        try:
            await status_msg.edit_text("\n".join(lines), parse_mode="HTML")
        except Exception as exc:
            logger.debug("Step update failed: %s", exc)
