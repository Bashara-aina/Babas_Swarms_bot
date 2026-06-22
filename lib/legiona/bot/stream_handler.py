"""
lib/legiona/bot/stream_handler.py
Legiona bot streaming — aiogram 3.24 native with progressive edit.
Uses send_message (initial) + edit_message_text (per-chunk) with
rate limiting to prevent Telegram flood waits.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable
from typing import Any

import httpx

from lib.legiona.minimax_client import (
    MINIMAX_BASE_URL,
    MINIMAX_MODEL,
    PRESET_CODING,
    PRESET_CREATIVE,
    PRESET_RESEARCH,
)
from lib.legiona.observability.cost_log import log_usage

_logger = logging.getLogger(__name__)

STREAMING_CHUNK_SIZE = int(os.getenv("TELEGRAM_STREAMING_CHUNK_SIZE", "350"))
TELEGRAM_EDIT_INTERVAL = float(os.getenv("TELEGRAM_EDIT_INTERVAL", "0.8"))  # seconds between edits
MAX_TELEGRAM_EDITS_PER_MESSAGE = 25  # hard limit before final send


# ── SSE Streaming from MiniMax ────────────────────────────────────────────────

async def stream_response(
    messages: list[dict[str, Any]],
    on_chunk: Callable[[str], None],
    preset: str = "coding",
    model: str | None = None,
    verbose: bool = False,
) -> str:
    """
    Stream M3 responses via SSE, invoking `on_chunk` for each delta.

    Args:
        messages: OpenAI-style message list
        on_chunk: Sync callback invoked with each text delta
        preset: "coding" | "research" | "creative"
        model: Override model string
        verbose: Log reasoning deltas

    Returns:
        Full accumulated response string
    """
    api_key = os.getenv("OPENCODE_GO_API_KEY", "")
    if not api_key:
        raise ValueError("OPENCODE_GO_API_KEY not set")

    model_str = model or MINIMAX_MODEL
    preset_map = {
        "coding": PRESET_CODING,
        "research": PRESET_RESEARCH,
        "creative": PRESET_CREATIVE,
    }
    params = preset_map.get(preset, PRESET_CODING)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_str,
        "messages": messages,
        "stream": True,
        "extra_body": {"reasoning_split": False},
        **params,
    }

    accumulated = ""
    full_response = ""
    captured_usage: dict[str, Any] | None = None

    async with httpx.AsyncClient(timeout=120.0) as client, client.stream(
        "POST", f"{MINIMAX_BASE_URL}/chat/completions", json=payload, headers=headers
    ) as resp:
        if resp.status_code != 200:
            body = await resp.aread()
            raise RuntimeError(f"MiniMax streaming error {resp.status_code}: {body.decode()}")

        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            data = line[6:].strip()
            if data == "[DONE]":
                break

            try:
                import json as _json

                event = _json.loads(data)
            except Exception:
                continue

            # Capture usage from the final event before [DONE]
            if (usage := event.get("usage")) and isinstance(usage, dict):
                captured_usage = usage

            choice = event.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            content_delta = delta.get("content", "")
            reasoning_delta = delta.get("reasoning", "") or delta.get("thinking", "")

            if content_delta:
                accumulated += content_delta
                full_response += content_delta
                if len(accumulated) >= STREAMING_CHUNK_SIZE:
                    on_chunk(accumulated)
                    accumulated = ""

            if reasoning_delta and verbose:
                _logger.debug("[legiona:stream] reasoning: %s", reasoning_delta[:120])

    if accumulated:
        on_chunk(accumulated)

    # Log token usage for cost tracking
    if captured_usage:
        log_usage(
            prompt_tokens=captured_usage.get("prompt_tokens", 0),
            completion_tokens=captured_usage.get("completion_tokens", 0),
            cached_tokens=captured_usage.get("cached_tokens", 0),
        )

    return full_response


# ── Telegram streaming ─────────────────────────────────────────────────────────

_aiogram_available = False
_Bot = None
_TelegramSender: Any = None


def _check_aiogram() -> bool:
    """Lazy import of aiogram — only needed for Telegram streaming."""
    global _aiogram_available, _Bot, _TelegramSender
    if _aiogram_available:
        return True
    try:
        import aiogram
        from aiogram import Bot
        from aiogram.methods import EditMessageText, SendMessage

        _Bot = Bot
        _TelegramSender = _TelegramSenderImpl
        _aiogram_available = True
        return True
    except ImportError:
        return False


class _TelegramSenderImpl:
    """
    Progressive Telegram message sender.
    Sends initial message, then edits with accumulated text at EDIT_INTERVAL.
    Throttles edits to stay under Telegram flood limits.
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: int,
        initial_text: str = "...",
        parse_mode: str = "HTML",
    ):
        from aiogram import Bot

        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.parse_mode = parse_mode
        self.msg_id: int | None = None
        self._accumulated = initial_text
        self._edit_count = 0
        self._last_edit_time = 0.0
        self._closed = False

        # Send initial placeholder
        self.msg_id = self._sync_send(initial_text)

    def _sync_send(self, text: str) -> int:
        """Send message synchronously — used in __init__ before event loop is running."""
        from aiogram.methods import SendMessage

        return self._sync_call(SendMessage(chat_id=self.chat_id, text=text, parse_mode=self.parse_mode))

    def _sync_call(self, method: Any) -> Any:
        """Execute a Telegram API method synchronously."""

        return asyncio.run(self.bot.session.execute(method))

    def _throttled_edit(self, text: str) -> bool:
        """
        Edit message with throttle. Returns True if edit was performed.
        Respects TELEGRAM_EDIT_INTERVAL between edits.
        """
        if self._closed or self._edit_count >= MAX_TELEGRAM_EDITS_PER_MESSAGE:
            return False

        now = time.monotonic()
        elapsed = now - self._last_edit_time
        if elapsed < TELEGRAM_EDIT_INTERVAL:
            return False  # skip this edit, wait for next chunk

        from aiogram.methods import EditMessageText

        self._sync_call(
            EditMessageText(
                chat_id=self.chat_id,
                message_id=self.msg_id,
                text=text,
                parse_mode=self.parse_mode,
            )
        )
        self._last_edit_time = time.monotonic()
        self._edit_count += 1
        return True

    def on_chunk(self, chunk: str) -> None:
        """Called by stream_response with each text delta."""
        if self._closed:
            return
        self._accumulated += chunk
        self._throttled_edit(self._accumulated)

    def close(self, final_text: str | None = None) -> None:
        """Finalize message — send final accumulated text."""
        if self._closed:
            return
        self._closed = True
        final = final_text if final_text is not None else self._accumulated
        if self._edit_count >= MAX_TELEGRAM_EDITS_PER_MESSAGE:
            # Already at limit — no more edits possible, message has best effort
            return
        from aiogram.methods import EditMessageText

        try:
            self._sync_call(
                EditMessageText(
                    chat_id=self.chat_id,
                    message_id=self.msg_id,
                    text=final,
                    parse_mode=self.parse_mode,
                )
            )
        except Exception as exc:
            _logger.warning("[TelegramSender] final edit failed: %s", exc)


async def stream_to_telegram(
    messages: list[dict[str, Any]],
    bot_token: str,
    chat_id: int,
    preset: str = "coding",
    parse_mode: str = "HTML",
) -> str:
    """
    Stream M3 response directly to a Telegram chat.
    Sends initial placeholder, then progressively edits the message.

    Args:
        messages: OpenAI-style message list
        bot_token: Telegram bot token
        chat_id: Target chat ID
        preset: "coding" | "research" | "creative"
        parse_mode: "HTML" or "MarkdownV2"

    Returns:
        Final full response string
    """
    if not _check_aiogram():
        raise RuntimeError("aiogram 3.24+ required for Telegram streaming")

    sender = _TelegramSender(bot_token=bot_token, chat_id=chat_id, parse_mode=parse_mode)

    def chunk_callback(chunk: str) -> None:
        sender.on_chunk(chunk)

    try:
        result = await stream_response(
            messages,
            on_chunk=chunk_callback,
            preset=preset,
        )
    finally:
        sender.close()

    return result


# ── CLI / debug streamer ──────────────────────────────────────────────────────

async def stream_print(messages: list[dict[str, Any]], preset: str = "coding") -> str:
    """
    Stream response to stdout for CLI / debugging.
    Prints each chunk as it arrives, returns full response on completion.
    """
    chunks: list[str] = []

    def printer(text: str) -> None:
        print(text, end="", flush=True)
        chunks.append(text)

    result = await stream_response(messages, on_chunk=printer, preset=preset)
    return result
