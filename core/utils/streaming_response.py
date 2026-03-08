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
        # Check provider health and apply proactive fallback
        effective_model = await self._select_healthy_provider(model, chat_id)
        
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
            None, self._produce_chunks, effective_model, task, agent_key, queue, loop, chat_id
        )

        # Consume queue and edit message
        full_text = await self._consume_and_edit(msg, label, queue)

        await producer  # Ensure thread is done

        # Final clean edit without thinking indicator
        await self._safe_edit(msg, f"{label}\n\n{full_text}")
        return full_text

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _select_healthy_provider(self, model: str, chat_id: int) -> str:
        """Check provider health and proactively fallback if unavailable.
        
        Args:
            model: Requested model string
            chat_id: Telegram chat ID for status updates
            
        Returns:
            Model string to use (original or fallback)
        """
        try:
            from core.reliability.provider_health import check_provider_health
            
            # Extract provider name
            provider = model.split("/")[0] if "/" in model else "unknown"
            
            # Check health
            status = check_provider_health(provider)
            
            if status == "unavailable":
                # Circuit breaker open — immediately fallback
                logger.warning(
                    "Provider '%s' circuit open, using fallback for chat %d",
                    provider, chat_id
                )
                await self.bot.send_message(
                    chat_id,
                    f"⚠️ <b>{provider}</b> is temporarily unavailable (rate limited).\n"
                    f"Using local Ollama model instead…",
                    parse_mode="HTML",
                )
                return "ollama_chat/qwen3.5:35b"
            
            elif status == "degraded":
                # Recently rate-limited but usable — warn user
                logger.info(
                    "Provider '%s' degraded (recent rate limit) for chat %d",
                    provider, chat_id
                )
                await self.bot.send_message(
                    chat_id,
                    f"⚠️ <b>{provider}</b> was recently rate limited.\n"
                    f"Proceeding with caution…",
                    parse_mode="HTML",
                )
            
        except Exception as exc:
            logger.debug("Provider health check skipped: %s", exc)
        
        return model

    def _produce_chunks(
        self,
        model: str,
        task: str,
        agent_key: str,
        queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        chat_id: int,
    ) -> None:
        """Synchronous producer: run in thread executor.

        CRITICAL FIX: Check circuit breaker INSIDE retry loop to immediately abort
        when provider becomes unavailable mid-retry.
        """
        import time as _time
        
        # Apply request throttling before starting
        self._apply_throttle_sync(model, loop)
        
        max_retries = 5
        current_model = model
        
        for attempt in range(max_retries + 1):
            # ✅ CRITICAL FIX: Check circuit breaker at START of each retry attempt
            try:
                from core.reliability.provider_health import check_provider_health
                provider = current_model.split("/")[0] if "/" in current_model else "unknown"
                status = check_provider_health(provider)
                
                if status == "unavailable" and provider != "ollama" and "ollama" not in provider:
                    # Circuit breaker open — skip ALL remaining retries, go straight to Ollama
                    logger.warning(
                        "Circuit breaker open for '%s' at retry attempt %d — switching to Ollama immediately",
                        provider, attempt
                    )
                    asyncio.run_coroutine_threadsafe(
                        queue.put(
                            "\n🔄 <b>Provider temporarily blocked (rate limited).</b>\n"
                            "Switching to local Ollama model immediately…\n\n"
                        ), 
                        loop
                    )
                    current_model = "ollama_chat/qwen3.5:35b"
                    # Don't break - continue with Ollama attempt
            except Exception as exc:
                logger.debug("Circuit check in retry loop failed: %s", exc)
            
            try:
                import core.interpreter_bridge as interpreter_bridge
                interpreter_bridge.configure_interpreter(current_model, agent_key)
                from interpreter import interpreter

                # FIXED: Pass display=False AND disable markdown display function
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
                exc_msg = str(exc)
                is_rate_limit = "RateLimitError" in exc_name or "429" in exc_msg
                
                # Skip display_markdown_message errors (Open Interpreter internal issue)
                if "display_markdown_message" in exc_msg:
                    logger.debug("Ignoring Open Interpreter display error: %s", exc)
                    continue  # Try again
                
                if is_rate_limit:
                    # Record rate limit for provider health tracking
                    self._record_rate_limit_sync(current_model, loop)
                
                if is_rate_limit and attempt < max_retries:
                    # Check if we should switch to Ollama immediately instead of retrying
                    try:
                        from core.reliability.provider_health import check_provider_health
                        provider = current_model.split("/")[0] if "/" in current_model else "unknown"
                        status = check_provider_health(provider)
                        
                        if status == "unavailable" and provider != "ollama" and "ollama" not in provider:
                            # Circuit just opened - switch to Ollama instead of retrying
                            logger.warning(
                                "Circuit breaker opened after rate limit — switching to Ollama instead of retry %d/%d",
                                attempt + 1, max_retries
                            )
                            asyncio.run_coroutine_threadsafe(
                                queue.put(
                                    "\n🔄 <b>Provider rate limited and circuit breaker activated.</b>\n"
                                    "Switching to local Ollama model…\n\n"
                                ), 
                                loop
                            )
                            current_model = "ollama_chat/qwen3.5:35b"
                            _time.sleep(1)  # Brief pause
                            continue  # Retry immediately with Ollama
                    except Exception:
                        pass
                    
                    # Normal exponential backoff: 3s, 6s, 12s, 24s, 48s
                    wait = (2 ** attempt) * 3
                    logger.warning(
                        "Rate limit on attempt %d/%d — retrying in %ds: %s",
                        attempt + 1, max_retries, wait, exc,
                    )
                    asyncio.run_coroutine_threadsafe(
                        queue.put(
                            f"\n⏳ Rate limited (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait}s…\n"
                        ), 
                        loop
                    )
                    _time.sleep(wait)
                    
                elif is_rate_limit and attempt == max_retries:
                    # Exhausted all retries — fallback to Ollama
                    logger.error(
                        "All %d retries exhausted for %s, falling back to local Ollama",
                        max_retries, current_model
                    )
                    asyncio.run_coroutine_threadsafe(
                        queue.put(
                            "\n🔄 <b>OpenRouter rate limit persists after all retries.</b>\n"
                            "Switching to local Ollama model for reliability…\n\n"
                        ), 
                        loop
                    )
                    current_model = "ollama_chat/qwen3.5:35b"
                    _time.sleep(2)
                    
                    try:
                        import core.interpreter_bridge as interpreter_bridge
                        interpreter_bridge.configure_interpreter(current_model, agent_key)
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
                        break  # Ollama succeeded
                        
                    except Exception as fallback_exc:
                        logger.error("Ollama fallback failed: %s", fallback_exc)
                        asyncio.run_coroutine_threadsafe(
                            queue.put(
                                f"\n❌ <b>Critical error:</b> Both OpenRouter and Ollama failed.\n"
                                f"OpenRouter: Rate limited\n"
                                f"Ollama: {fallback_exc}\n\n"
                                f"Please check system logs and ensure Ollama is running."
                            ), 
                            loop
                        )
                        break
                else:
                    # Non-rate-limit error
                    logger.error("Streaming producer error: %s", exc)
                    asyncio.run_coroutine_threadsafe(
                        queue.put(f"\n⚠️ <b>Error:</b> {exc_name}\n{exc_msg[:200]}\n"), 
                        loop
                    )
                    break
                    
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # sentinel

    def _apply_throttle_sync(self, model: str, loop: asyncio.AbstractEventLoop) -> None:
        """Apply request throttling in synchronous context (thread-safe).
        
        Args:
            model: Model string
            loop: Event loop for async calls
        """
        try:
            from core.reliability.request_throttle import RequestThrottle
            
            # Run async throttle in the event loop
            future = asyncio.run_coroutine_threadsafe(
                RequestThrottle.acquire(model, timeout=30.0),
                loop
            )
            acquired = future.result(timeout=35.0)
            
            if not acquired:
                logger.warning("Request throttle timeout for model: %s", model)
        except Exception as exc:
            logger.debug("Request throttle skipped: %s", exc)

    def _record_rate_limit_sync(self, model: str, loop: asyncio.AbstractEventLoop) -> None:
        """Record rate limit event in synchronous context (thread-safe).
        
        Args:
            model: Model string
            loop: Event loop (unused but kept for consistency)
        """
        try:
            from core.reliability.provider_health import record_rate_limit
            
            # Extract provider name
            provider = model.split("/")[0] if "/" in model else "unknown"
            record_rate_limit(provider)
        except Exception as exc:
            logger.debug("Rate limit recording skipped: %s", exc)

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
