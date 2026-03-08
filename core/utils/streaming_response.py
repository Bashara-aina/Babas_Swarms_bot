# /home/newadmin/swarm-bot/streaming_response.py
"""Real-time streaming of LLM output to Telegram.

Open Interpreter yields chunks synchronously.  We run it in a thread-pool
executor and push chunks into an asyncio queue, while the main coroutine
consumes the queue and periodically edits the Telegram message.

Telegram edit rate-limit: ≈ 1 edit/second per chat.  We buffer for 0.6 s.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

# Minimum seconds between Telegram message edits
_EDIT_INTERVAL = 0.6
# Max chars before forcing an edit flush
_CHUNK_FLUSH_SIZE = 200
# Thinking placeholder text
_THINKING = "…"


class StreamingResponseManager:
    """Stream Open Interpreter output to a Telegram message in real-time.

    Usage::

        mgr = StreamingResponseManager(bot)
        text = await mgr.stream_task(chat_id, model, task, agent_key)
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def stream_task(
        self,
        chat_id: int,
        model: str,
        task: str,
        agent_key: str = "coding",
        header: str = "",
    ) -> str:
        """Execute a task with streaming output.

        Args:
            chat_id: Telegram chat id to send updates to.
            model: Model string (e.g. "zai/glm-4").
            task: Task text.
            agent_key: Agent identifier.
            header: HTML header shown above streamed content.

        Returns:
            Full concatenated response text.
        """
        # Placeholder message
        label = header or f"<b>🤖 {agent_key.upper()}</b>"
        msg = await self.bot.send_message(
            chat_id,
            f"{label}\n\n{_THINKING}",
            parse_mode="HTML",
        )

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        # Run OI in thread, push chunks to queue
        loop = asyncio.get_event_loop()
        producer = loop.run_in_executor(
            None, self._produce_chunks, model, task, agent_key, queue, loop
        )

        # Consume queue and edit message
        full_text = await self._consume_and_edit(msg, label, queue)

        await producer  # Ensure thread is done

        # Final clean edit without thinking indicator
        await self._safe_edit(msg, f"{label}\n\n{full_text}")
        return full_text

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _produce_chunks(
        self,
        model: str,
        task: str,
        agent_key: str,
        queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Synchronous producer: run in thread executor.

        Retries up to 2 times on RateLimitError with 3-second backoff.
        """
        import time as _time
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                import core.interpreter_bridge as interpreter_bridge
                interpreter_bridge.configure_interpreter(model, agent_key)
                from interpreter import interpreter

                for chunk in interpreter.chat(task, stream=True, display=False):
                    chunk_type = chunk.get("type", "")
                    content = chunk.get("content", "")
                    if not isinstance(content, str) or not content:
                        continue
                    if chunk_type == "message":
                        asyncio.run_coroutine_threadsafe(queue.put(content), loop)
                    elif chunk_type == "code":
                        asyncio.run_coroutine_threadsafe(
                            queue.put(f"\n```\n{content}\n```\n"), loop
                        )
                    elif chunk_type == "console":
                        asyncio.run_coroutine_threadsafe(
                            queue.put(f"\n<code>$ {content}</code>\n"), loop
                        )
                break  # Success — exit retry loop
            except Exception as exc:
                exc_name = type(exc).__name__
                is_rate_limit = "RateLimitError" in exc_name or "429" in str(exc)
                if is_rate_limit and attempt < max_retries:
                    wait = 3 * (attempt + 1)
                    logger.warning(
                        "Rate limit on attempt %d/%d — retrying in %ds: %s",
                        attempt + 1, max_retries, wait, exc,
                    )
                    asyncio.run_coroutine_threadsafe(
                        queue.put(f"\n⏳ Rate limited, retrying in {wait}s…"), loop
                    )
                    _time.sleep(wait)
                else:
                    logger.error("Streaming producer error: %s", exc)
                    asyncio.run_coroutine_threadsafe(
                        queue.put(f"\n⚠️ Stream error: {exc}"), loop
                    )
                    break
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # sentinel

    async def _consume_and_edit(
        self,
        msg: Any,
        label: str,
        queue: asyncio.Queue,
    ) -> str:
        """Consume queue and edit the message at most once per _EDIT_INTERVAL."""
        buffer = ""
        last_edit = time.monotonic()

        while True:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                # Still waiting for chunks — update "thinking" indicator
                dots = "." * (int(time.monotonic()) % 4)
                await self._safe_edit(msg, f"{label}\n\n{buffer or _THINKING}{dots}")
                continue

            if chunk is None:  # sentinel — producer finished
                break

            buffer += chunk

            now = time.monotonic()
            should_flush = (
                now - last_edit >= _EDIT_INTERVAL
                or len(buffer) - (len(buffer) - len(chunk)) >= _CHUNK_FLUSH_SIZE
            )
            if should_flush:
                await self._safe_edit(msg, f"{label}\n\n{buffer}")
                last_edit = now

        return buffer

    @staticmethod
    async def _safe_edit(msg: Any, text: str) -> None:
        """Edit message, silently ignore 'message not modified' errors."""
        try:
            # Truncate to Telegram's 4096-char message limit
            if len(text) > 4000:
                text = text[:3997] + "…"
            await msg.edit_text(text, parse_mode="HTML")
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                logger.debug("Edit failed: %s", exc)
        except Exception as exc:
            logger.debug("Edit failed: %s", exc)
