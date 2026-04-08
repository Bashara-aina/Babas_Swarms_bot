"""Tier-3 Legion commands: simulate, screenpipe,, LiveKit, quick search/scrape."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed, send_chunked

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("jarvis"))
async def cmd_jarvis(msg: Message) -> None:
    """One-shot context bundle: memory, Screenpipe, WhatsApp, optional calendar → LLM plan (no sends)."""
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    goal = parts[1].strip() if len(parts) > 1 else ""
    if not goal:
        await msg.answer(
            "Usage: <code>/jarvis &lt;what you need&gt;</code>\n\n"
            "Gathers mem0+wiki+Screenpipe (if on), WhatsApp sidecar unread (if healthy), "
            "optional MCP WhatsApp/calendar when enabled in env — then synthesizes a plan. "
            "<b>Nothing is sent</b> automatically.",
            parse_mode="HTML",
        )
        return
    await msg.answer("Gathering context…", parse_mode="HTML")
    try:
        from core.jarvis_orchestrator import compose_jarvis_response, gather_jarvis_bundle

        uid = str(msg.from_user.id) if msg.from_user else "0"
        bundle = await gather_jarvis_bundle(goal, uid)
        text = await compose_jarvis_response(bundle)
        await send_chunked(msg, text)
    except Exception as exc:
        logger.exception("jarvis failed")
        await msg.answer(f"Jarvis error: {exc}", parse_mode="HTML")


@router.message(Command("simulate"))
async def cmd_simulate(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    q = parts[1].strip() if len(parts) > 1 else ""
    if not q:
        await msg.answer("Usage: /simulate &lt;question&gt;", parse_mode="HTML")
        return
    await msg.answer("Running MiroFish-style simulation…")
    try:
        from tools.simulation_tool import run_simulation

        res = await run_simulation(q)
        text = (
            f"<b>Prediction</b>\n{res.prediction}\n\n"
            f"<b>Confidence</b> {res.confidence_score:.2f}\n"
            f"<b>Dissent</b>\n" + "\n".join(res.dissenting_views)
        )
        await send_chunked(msg, text)
    except Exception as exc:
        logger.exception("simulate failed")
        await msg.answer(f"Simulate error: {exc}")


@router.message(Command("screenpipe_status"))
async def cmd_screenpipe_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    import os

    from tools.screenpipe_tool import get_screenpipe_tool

    sp = get_screenpipe_tool()
    en = sp.is_configured()
    lines = [
        f"Screenpipe enabled: {en}",
        f"URL: {sp.base_url}",
    ]
    if en:
        ctx = await sp.get_recent_activity(hours=2)
        lines.append("Sample query (2h):")
        lines.append(ctx[:3500] or "(empty)")
    await send_chunked(msg, "\n".join(lines))


