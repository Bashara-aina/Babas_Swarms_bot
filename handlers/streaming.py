"""Streaming LLM response helpers — edits message progressively as tokens arrive.

Usage in any handler:
    from handlers.streaming import stream_chat
    await stream_chat(msg, task, agent_key="coding")
"""

from __future__ import annotations

import asyncio
import contextlib
import html as html_mod
import logging
import os

from aiogram.types import Message

logger = logging.getLogger(__name__)

_EDIT_INTERVAL = 0.8  # seconds between edits (avoid Telegram flood limits)
_STREAM_ENABLED = os.getenv("STREAM_RESPONSES", "true").lower() == "true"


async def stream_chat(
    msg: Message,
    task: str,
    agent_key: str | None = None,
    thread_id: str | None = None,
) -> None:
    """Stream a single-turn LLM response, editing the message as tokens arrive."""
    if not _STREAM_ENABLED:
        # Fall back to non-streaming
        from handlers.shared import _execute_chat

        await _execute_chat(msg, task, forced_agent=agent_key)
        return

    key = agent_key or "general"
    status_msg = await msg.answer("⚡ thinking…")

    accumulated = ""
    last_edit_time = 0.0
    model_used = key

    try:
        from agents import AGENT_MODELS
        from llm_client import call_llm

        model = AGENT_MODELS.get(key, AGENT_MODELS.get("general", "minimax-coding-plan/MiniMax-M3"))
        messages = [{"role": "user", "content": task}]

        stream = await call_llm(
            messages=messages,
            model=model,
            stream=True,
            temperature=0.7,
        )
        model_used = model

        async for chunk in stream:  # type: ignore[reportGeneralTypeIssues]
            delta = chunk.choices[0].delta.content or ""
            accumulated += delta

            now = asyncio.get_running_loop().time()
            if now - last_edit_time >= _EDIT_INTERVAL and accumulated.strip():
                try:
                    safe = html_mod.escape(accumulated[-3800:])  # keep last 3800 chars
                    await status_msg.edit_text(
                        f"<code>streaming…</code>\n{safe}",
                        parse_mode="HTML",
                    )
                    last_edit_time = now
                except Exception:
                    pass  # edit conflict is fine

        # Final edit with full response
        if accumulated.strip():
            from handlers.shared import send_chunked

            await status_msg.delete()
            await send_chunked(msg, accumulated, model_used=model_used)
        else:
            await status_msg.edit_text("❌ Empty response from model")

    except Exception as e:
        logger.error("Streaming error: %s", e)
        # Fall back gracefully
        with contextlib.suppress(Exception):
            await status_msg.delete()
        from handlers.shared import _execute_chat

        await _execute_chat(msg, task, forced_agent=key)
