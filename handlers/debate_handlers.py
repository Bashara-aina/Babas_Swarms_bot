"""handlers/debate_handlers.py — /debate and /opinion commands for Legion.

Routes: /debate <topic>  → Legion debates the topic with evidence
        /opinion <thing> → Legion gives its honest opinion
"""
from __future__ import annotations

import html
import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()

ALLOWED_USER_ID: int = int((os.getenv("ALLOWED_USER_ID") or os.getenv("BASHARA_TELEGRAM_ID") or "0").strip().split(",")[0])


async def _require_owner(message: Message) -> bool:
    """Return True if allowed; send rejection and return False otherwise."""
    try:
        from handlers.shared import ALLOWED_USER_ID as _uid  # type: ignore[attr-defined]
        allowed = _uid
    except Exception:
        allowed = ALLOWED_USER_ID
    if message.from_user and message.from_user.id == allowed:
        return True
    await message.answer("<b>Unauthorized.</b>", parse_mode="HTML")
    return False


async def _split_and_send(message: Message, text: str) -> None:
    """Send text chunked at 4000 chars."""
    try:
        from handlers.shared import split_and_send  # type: ignore[attr-defined]
        await split_and_send(message, text)
        return
    except Exception:
        pass
    chunk_size = 4000
    for i in range(0, len(text), chunk_size):
        await message.answer(text[i : i + chunk_size], parse_mode="HTML")


@router.message(Command("debate"))
async def cmd_debate(message: Message) -> None:
    """Debate a topic — Legion takes a position and defends it with evidence."""
    if not await _require_owner(message):
        return

    topic = (message.text or "").removeprefix("/debate").strip()
    if not topic:
        await message.answer(
            "<b>Usage:</b> <code>/debate &lt;topic&gt;</code>\n"
            "Example: <code>/debate AI will take all jobs</code>",
            parse_mode="HTML",
        )
        return

    safe_topic = html.escape(topic)
    thinking = await message.answer(
        f"<i>Thinking about: {safe_topic}...</i>", parse_mode="HTML"
    )

    try:
        from core.debate_engine import build_debate_instruction  # type: ignore[attr-defined]
        from llm_client import chat  # type: ignore[attr-defined]

        # Load beliefs for context
        beliefs: dict = {}
        try:
            import json
            from pathlib import Path
            beliefs_path = Path("data/beliefs.json")
            if beliefs_path.exists():
                beliefs = json.loads(beliefs_path.read_text(encoding="utf-8"))
        except Exception as _e:
            logger.warning("Failed to load beliefs.json: %s", _e)

        debate_block = build_debate_instruction(topic, beliefs)

        system_prompt = (
            "You are Legion, Bashara's permanent AI coworker. "
            "You debate with evidence and genuine intellectual conviction. "
            "You do NOT just validate the user — you push back when you have a strong position. "
            "Be direct, precise, and use concrete examples or data where possible. "
            f"\n\n{debate_block}"
        )

        response = await chat(
            messages=[{"role": "user", "content": f"Debate this: {topic}"}],
            system=system_prompt,
            agent_key="debate",
        )

        await thinking.delete()
        await _split_and_send(message, response)

    except Exception as exc:
        logger.exception("Debate handler error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        try:
            await thinking.delete()
        except Exception:
            pass
        await message.answer(
            f"<b>Debate error:</b> <code>{safe_err}</code>", parse_mode="HTML"
        )


@router.message(Command("opinion"))
async def cmd_opinion(message: Message) -> None:
    """Get Legion's honest opinion on something."""
    if not await _require_owner(message):
        return

    subject = (message.text or "").removeprefix("/opinion").strip()
    if not subject:
        await message.answer(
            "<b>Usage:</b> <code>/opinion &lt;thing&gt;</code>\n"
            "Example: <code>/opinion using TypeScript for everything</code>",
            parse_mode="HTML",
        )
        return

    safe_subject = html.escape(subject)
    thinking = await message.answer(
        f"<i>Forming opinion on: {safe_subject}...</i>", parse_mode="HTML"
    )

    try:
        from llm_client import chat  # type: ignore[attr-defined]

        system_prompt = (
            "You are Legion, Bashara's permanent AI coworker and trusted intellectual partner. "
            "Give your genuine, direct opinion. Do not hedge excessively. "
            "If you have a strong view, state it clearly and explain why. "
            "Use data, analogies, or personal reasoning. Never start with agreement or flattery. "
            "Match Bashara's language (Indonesian or English)."
        )

        response = await chat(
            messages=[{"role": "user", "content": f"What is your honest opinion on: {subject}"}],
            system=system_prompt,
            agent_key="debate",
        )

        await thinking.delete()
        await _split_and_send(message, response)

    except Exception as exc:
        logger.exception("Opinion handler error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        try:
            await thinking.delete()
        except Exception:
            pass
        await message.answer(
            f"<b>Opinion error:</b> <code>{safe_err}</code>", parse_mode="HTML"
        )
