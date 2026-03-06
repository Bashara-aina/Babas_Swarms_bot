"""Real-time streaming response manager for Telegram bot.

Provides live feedback during LLM generation, similar to ChatGPT's streaming experience.
Users see responses appear in real-time instead of waiting for complete generation.
"""

from __future__ import annotations
import time
import logging
from typing import AsyncGenerator

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class StreamingResponseManager:
    """Manage real-time streaming of LLM responses to Telegram."""

    def __init__(self, bot: Bot):
        """Initialize streaming manager.
        
        Args:
            bot: Telegram Bot instance
        """
        self.bot = bot
        self.update_interval = 0.8  # Update every 0.8 seconds
        self.min_chunk_size = 80  # Min characters before updating

    async def stream_response(
        self,
        chat_id: int,
        generator: AsyncGenerator[str, None],
        agent: str,
    ) -> str:
        """Stream LLM output chunks in real-time to Telegram.
        
        Args:
            chat_id: Telegram chat ID
            generator: Async generator yielding text chunks
            agent: Agent name for formatting
            
        Returns:
            Complete response text
        """
        # Initial thinking message
        message = await self.bot.send_message(
            chat_id,
            f"<b>{agent.upper()}</b> is thinking...",
            parse_mode="HTML",
        )

        buffer = ""
        last_update = time.time()
        update_count = 0
        complete_response = ""

        try:
            async for chunk in generator:
                buffer += chunk
                complete_response += chunk

                # Update when enough time passed or buffer is large
                should_update = (
                    time.time() - last_update > self.update_interval
                    or len(buffer) > self.min_chunk_size
                )

                if should_update:
                    try:
                        # Format with progress indicator
                        display_text = self._format_streaming_text(buffer, agent, is_complete=False)
                        
                        await message.edit_text(
                            display_text,
                            parse_mode="HTML",
                        )
                        last_update = time.time()
                        update_count += 1
                        
                    except TelegramBadRequest as e:
                        # Message unchanged or too frequent updates
                        if "message is not modified" not in str(e).lower():
                            logger.warning(f"Telegram update error: {e}")
                    except Exception as e:
                        logger.error(f"Streaming update error: {e}")

            # Final update with complete response
            final_text = self._format_streaming_text(complete_response, agent, is_complete=True)
            try:
                await message.edit_text(
                    final_text,
                    parse_mode="HTML",
                )
            except TelegramBadRequest:
                # Already up to date
                pass

            logger.info(f"Streaming complete: {update_count} updates, {len(complete_response)} chars")
            return complete_response

        except Exception as exc:
            error_text = f"<b>{agent.upper()}</b>\n\n❌ Error during streaming: {exc}"
            try:
                await message.edit_text(error_text, parse_mode="HTML")
            except Exception:
                pass
            raise

    def _format_streaming_text(self, text: str, agent: str, is_complete: bool) -> str:
        """Format text for streaming display.
        
        Args:
            text: Current response text
            agent: Agent name
            is_complete: Whether streaming is complete
            
        Returns:
            Formatted HTML text
        """
        # Truncate if too long (Telegram limit is 4096 chars)
        max_length = 3800
        if len(text) > max_length:
            text = text[:max_length] + "...\n\n<i>(truncated, see full response above)</i>"

        # Add status indicator
        if is_complete:
            status = "✅"
        else:
            status = "⚡"

        formatted = f"<b>{agent.upper()}</b> {status}\n\n{text}"
        
        return formatted

    async def stream_with_progress(
        self,
        chat_id: int,
        generator: AsyncGenerator[str, None],
        agent: str,
        task_description: str,
    ) -> str:
        """Stream response with task progress tracking.
        
        Args:
            chat_id: Telegram chat ID
            generator: Async generator yielding text chunks
            agent: Agent name
            task_description: Brief task description
            
        Returns:
            Complete response text
        """
        message = await self.bot.send_message(
            chat_id,
            f"🚀 <b>Starting:</b> {task_description}\n\n"
            f"<b>Agent:</b> {agent}\n"
            f"<b>Status:</b> Initializing...",
            parse_mode="HTML",
        )

        buffer = ""
        last_update = time.time()
        char_count = 0
        start_time = time.time()

        try:
            async for chunk in generator:
                buffer += chunk
                char_count += len(chunk)

                if time.time() - last_update > self.update_interval:
                    elapsed = time.time() - start_time
                    try:
                        status_text = (
                            f"🚀 <b>Task:</b> {task_description}\n\n"
                            f"<b>Agent:</b> {agent}\n"
                            f"<b>Status:</b> Generating ({char_count} chars)\n"
                            f"<b>Elapsed:</b> {elapsed:.1f}s\n\n"
                            f"<pre>{buffer[:500]}...</pre>"
                        )
                        await message.edit_text(status_text, parse_mode="HTML")
                        last_update = time.time()
                    except TelegramBadRequest:
                        pass

            # Complete
            duration = time.time() - start_time
            final_text = (
                f"✅ <b>Complete:</b> {task_description}\n\n"
                f"<b>Agent:</b> {agent}\n"
                f"<b>Duration:</b> {duration:.1f}s\n"
                f"<b>Output:</b> {len(buffer)} characters\n\n"
                f"<i>See full response below:</i>"
            )
            await message.edit_text(final_text, parse_mode="HTML")

            # Send full response in chunks
            await self.bot.send_message(
                chat_id,
                f"<pre>{buffer[:4000]}</pre>",
                parse_mode="HTML",
            )

            return buffer

        except Exception as exc:
            await message.edit_text(
                f"❌ <b>Error:</b> {task_description}\n\n{exc}",
                parse_mode="HTML",
            )
            raise
