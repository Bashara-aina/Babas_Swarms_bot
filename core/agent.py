"""Core agent command handlers extracted from handlers/ai.py.

This module contains the implementations for /run and /think commands,
extracted to allow better separation of concerns and easier testing.
"""

from __future__ import annotations

import asyncio
import contextlib
import html as html_mod
from typing import TYPE_CHECKING

from aiogram.types import Message

if TYPE_CHECKING:
    pass


async def cmd_think_impl(
    msg: Message,
    raw: str,
    is_allowed_fn: callable,
    keep_typing_fn: callable,
    send_chunked_fn: callable,
) -> None:
    """Execute the /think command with layered extended thinking.

    Args:
        msg: The Telegram message object.
        raw: The raw command arguments string.
        is_allowed_fn: Callable to check if user is allowed.
        keep_typing_fn: Callable to keep the typing indicator active.
        send_chunked_fn: Callable to send chunked messages.
    """
    if not is_allowed_fn(msg):
        return
    if not raw:
        await msg.answer(
            "usage: <code>/think [--depth=3] [--branches=5] &lt;hard question&gt;</code>\n"
            "runs layered extended thinking with adversarial critique + synthesis",
            parse_mode="HTML",
        )
        return

    depth = 3
    branches = 5
    tokens = raw.split()
    query_tokens: list[str] = []
    for token in tokens:
        if token.startswith("--depth="):
            with contextlib.suppress(Exception):
                depth = max(2, min(6, int(token.split("=", 1)[1])))
            continue
        if token.startswith("--branches="):
            with contextlib.suppress(Exception):
                branches = max(3, min(8, int(token.split("=", 1)[1])))
            continue
        query_tokens.append(token)

    query = " ".join(query_tokens).strip()
    if not query:
        await msg.answer(
            "usage: <code>/think [--depth=3] [--branches=5] &lt;hard question&gt;</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(
        f"🧠 starting layered deep think… (depth={depth}, branches={branches})",
        parse_mode="HTML",
    )
    typing_task = asyncio.create_task(keep_typing_fn(msg))

    async def _progress(text: str) -> None:
        safe = html_mod.escape(text)
        with contextlib.suppress(Exception):
            await status_msg.edit_text(safe, parse_mode="HTML")
            with contextlib.suppress(Exception):
                await msg.answer(f"<i>{safe}</i>", parse_mode="HTML")

    try:
        from llm_client import _call_model
        from tools.deep_think import format_think_result, run_deep_think

        async def _llm_call(model: str, system_prompt: str, user_prompt: str) -> str:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            resp = await _call_model(model=model, messages=messages, max_tokens=2200, temperature=0.7)
            return (resp.choices[0].message.content or "").strip()

        result = await run_deep_think(
            question=query,
            llm_call=_llm_call,
            progress_fn=_progress,
            depth=depth,
            branches=branches,
        )
        rendered = format_think_result(result)
        with contextlib.suppress(Exception):
            await status_msg.delete()
        await send_chunked_fn(msg, rendered, model_used=f"think/deep:d{depth}:b{branches}")
    except Exception as e:
        await status_msg.edit_text(
            f"deep think error: <code>{html_mod.escape(str(e)[:380])}</code>",
            parse_mode="HTML",
        )
    finally:
        typing_task.cancel()


async def cmd_run_impl(
    msg: Message,
    task: str,
    is_allowed_fn: callable,
    execute_chat_fn: callable,
) -> None:
    """Execute the /run command for LLM chat only (no computer access).

    Args:
        msg: The Telegram message object.
        task: The task description.
        is_allowed_fn: Callable to check if user is allowed.
        execute_chat_fn: Callable to execute the chat with a forced agent.
    """
    if not is_allowed_fn(msg):
        return
    if not task:
        await msg.answer(
            "usage: <code>/run &lt;task&gt;</code>  — LLM chat only, no computer access\n"
            "for full computer control use <code>/do &lt;task&gt;</code>",
            parse_mode="HTML",
        )
        return
    await execute_chat_fn(msg, task, forced_agent="general")
