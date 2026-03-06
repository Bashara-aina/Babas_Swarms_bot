# /home/newadmin/swarm-bot/streaming_response.py
"""Real-time streaming response manager for Telegram."""

from __future__ import annotations
import time
import logging
from typing import AsyncGenerator

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class StreamingResponseManager:
    """Stream LLM outputs in real-time to Telegram (like ChatGPT)."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.min_update_interval = 0.8  # seconds
        self.min_chunk_size = 80  # characters

    async def stream_response(
        self,
        chat_id: int,
        generator: AsyncGenerator[str, None],
        agent: str,
        initial_msg: str = None,
    ) -> str:
        """Stream chunks as they arrive from LLM.

        Args:
            chat_id: Telegram chat ID
            generator: Async generator yielding text chunks
            agent: Agent name for display
            initial_msg: Optional initial message

        Returns:
            Final complete response text
        """
        # Send initial thinking message
        message = await self.bot.send_message(
            chat_id,
            initial_msg or f"<b>{agent.upper()}</b> is thinking...",
            parse_mode="HTML",
        )

        buffer = ""
        last_update = time.time()
        error_count = 0
        max_errors = 3

        try:
            async for chunk in generator:
                buffer += chunk
                now = time.time()

                # Update conditions: enough time passed OR buffer is large
                should_update = (
                    now - last_update > self.min_update_interval
                    or len(buffer) > self.min_chunk_size * 10
                )

                if should_update:
                    try:
                        await message.edit_text(
                            f"<b>{agent.upper()}</b>\n\n{buffer[:4000]}",
                            parse_mode="HTML",
                        )
                        last_update = now
                        error_count = 0  # Reset on success
                    except TelegramBadRequest as e:
                        # Message unchanged or too frequent updates
                        if "message is not modified" not in str(e).lower():
                            logger.warning(f"Stream update failed: {e}")
                            error_count += 1
                            if error_count >= max_errors:
                                logger.error("Too many stream errors, stopping updates")
                                break

            # Final update with complete response
            try:
                await message.edit_text(
                    f"<b>{agent.upper()}</b>\n\n{buffer}\n\n✅ <i>Done</i>",
                    parse_mode="HTML",
                )
            except TelegramBadRequest:
                # If final edit fails, send new message
                await self.bot.send_message(
                    chat_id,
                    f"<b>{agent.upper()}</b>\n\n{buffer}\n\n✅ <i>Done</i>",
                    parse_mode="HTML",
                )

            return buffer

        except Exception as exc:
            logger.exception(f"Streaming error: {exc}")
            await message.edit_text(
                f"<b>{agent.upper()}</b>\n\n{buffer}\n\n❌ <i>Error: {exc}</i>",
                parse_mode="HTML",
            )
            return buffer

    async def stream_with_status(
        self,
        chat_id: int,
        generator: AsyncGenerator[str, None],
        agent: str,
        show_typing: bool = True,
    ) -> str:
        """Stream with typing indicator.

        Args:
            chat_id: Telegram chat ID
            generator: Async generator
            agent: Agent name
            show_typing: Show typing indicator

        Returns:
            Final response
        """
        if show_typing:
            await self.bot.send_chat_action(chat_id, "typing")

        return await self.stream_response(chat_id, generator, agent)
