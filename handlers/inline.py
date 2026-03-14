"""Inline bot mode — @LegionBot <query> works inside any Telegram chat."""
from __future__ import annotations

import hashlib
import logging

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

import llm_client

logger = logging.getLogger(__name__)
router = Router()

_INLINE_MAX_CHARS = 3800


@router.inline_query()
async def handle_inline_query(query: InlineQuery) -> None:
    """Handle @LegionBot <text> inline queries from any chat."""
    text = query.query.strip()

    if not text:
        await query.answer(
            results=[],
            switch_pm_text="Type a question after @LegionBot…",
            switch_pm_parameter="start",
            cache_time=1,
        )
        return

    try:
        response, model_used = await llm_client.chat(text, agent_key="general")
    except Exception as e:
        response = f"❌ Error: {str(e)[:200]}"
        model_used = "error"

    # Truncate for inline result
    if len(response) > _INLINE_MAX_CHARS:
        response = response[:_INLINE_MAX_CHARS] + "\n\n…<i>(open bot for full answer)</i>"

    provider = model_used.split("/")[0].upper() if model_used else "AI"
    result_id = hashlib.md5(text.encode()).hexdigest()[:8]

    result = InlineQueryResultArticle(
        id=result_id,
        title=text[:50] + ("…" if len(text) > 50 else ""),
        description=response[:100] + "…",
        input_message_content=InputTextMessageContent(
            message_text=f"<b>Q:</b> {text}\n\n{response}\n\n<i>via @LegionBot [{provider}]</i>",
            parse_mode="HTML",
        ),
    )

    await query.answer(
        results=[result],
        cache_time=30,
        is_personal=True,
    )
    logger.info("Inline query answered: %s", text[:60])
