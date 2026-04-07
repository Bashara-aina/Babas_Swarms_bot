"""Autonomous plain-text message handling for Legion v6."""

from __future__ import annotations

import html as html_mod
import logging

from aiogram.types import Message

from core.autonomous_router import SKILL_PATTERNS, AutonomousRouter
from .shared import _execute_chat, _run_agent_loop, is_allowed

logger = logging.getLogger(__name__)


async def handle_plain_message(
    msg: Message,
    auto_router: AutonomousRouter,
) -> None:
    """Handle non-command plain text and route autonomously."""
    if not is_allowed(msg):
        return

    user_msg = (msg.text or "").strip()
    if not user_msg or user_msg.startswith("/"):
        return

    skill_match = auto_router.analyze(user_msg)
    logger.info(
        "[AutoRouter] '%s...' -> %s (%s%%)",
        user_msg[:50],
        skill_match.skill_name,
        int(skill_match.confidence * 100),
    )

    handler_key = SKILL_PATTERNS.get(skill_match.skill_name, {}).get("handler", "chat")

    try:
        if handler_key == "chat" or skill_match.confidence < 0.4:
            await _execute_chat(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "memory_recall":
            from llm_client import memory

            if memory is not None:
                memories = await memory.search(user_msg, limit=8)
                if memories:
                    mem_context = "\n".join(
                        f"[{str(m.get('created_at', ''))[:10]}] {str(m.get('content', ''))[:300]}"
                        for m in memories[:5]
                    )
                    enriched = (
                        f"{user_msg}\n\n[Memory search results found — use these to answer]:\n{mem_context}"
                    )
                    await _execute_chat(msg, enriched)
                    auto_router.record_performance(skill_match.skill_name, True)
                    return
            await _execute_chat(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "/do":
            await _run_agent_loop(msg, user_msg)
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "/run":
            await _execute_chat(msg, user_msg, forced_agent="coding")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "/think":
            await _execute_chat(msg, user_msg, forced_agent="think")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "/swarm":
            await _execute_chat(msg, user_msg, forced_agent="architect")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "/research":
            await _execute_chat(msg, user_msg, forced_agent="researcher")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        if handler_key == "/cmd":
            from llm_client import run_shell_command

            output = await run_shell_command(user_msg)
            await msg.answer(f"<pre>{html_mod.escape(output[:3800])}</pre>", parse_mode="HTML")
            auto_router.record_performance(skill_match.skill_name, True)
            return

        await _execute_chat(msg, user_msg)
        auto_router.record_performance(skill_match.skill_name, True)
    except Exception as exc:
        auto_router.record_performance(skill_match.skill_name, False)
        await msg.answer(f"autonomous routing error: <code>{html_mod.escape(str(exc)[:350])}</code>", parse_mode="HTML")
