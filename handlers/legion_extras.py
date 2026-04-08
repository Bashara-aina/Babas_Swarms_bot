"""Tier-3 Legion commands: simulate, screenpipe, MCP, LiveKit, quick search/scrape."""

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


@router.message(Command("mcp_status"))
async def cmd_mcp_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from core.mcp_client import format_mcp_status, load_mcp_config, try_list_tools_stdio

    await msg.answer(format_mcp_status(), parse_mode="HTML")
    cfg = load_mcp_config()
    for s in cfg.get("servers") or []:
        if not isinstance(s, dict) or not s.get("enabled"):
            continue
        tools = await try_list_tools_stdio(s)
        if tools:
            await msg.answer("Tools: " + ", ".join(tools[:30]))


@router.message(Command("voice_room"))
async def cmd_voice_room(msg: Message) -> None:
    if not is_allowed(msg):
        return
    from agents.voice_agent import voice_stack_summary
    from bridges.livekit_bridge import build_room_token, livekit_status_message, meet_join_url

    await msg.answer(voice_stack_summary() + "\n\n" + livekit_status_message())
    parts = (msg.text or "").split(maxsplit=1)
    room = parts[1].strip() if len(parts) > 1 else "legion"
    tok = build_room_token(identity=str(msg.from_user.id), room=room)
    if tok:
        await msg.answer(f"Room <code>{room}</code> token (short):\n<code>{tok[:80]}…</code>", parse_mode="HTML")
        join = meet_join_url(tok, room=room)
        if join:
            await msg.answer(f"<a href=\"{join}\">Open voice room (browser)</a>", parse_mode="HTML")


@router.message(Command("voice"))
async def cmd_voice(msg: Message) -> None:
    """Alias for /voice_room — spec name /voice."""
    await cmd_voice_room(msg)


@router.message(Command("websearch"))
async def cmd_websearch(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    q = parts[1].strip() if len(parts) > 1 else ""
    if not q:
        await msg.answer("Usage: /websearch &lt;query&gt;", parse_mode="HTML")
        return
    from tools.search_tool import web_search

    out = await web_search(q)
    await send_chunked(msg, out or "No results (set TAVILY_API_KEY or check query).")


@router.message(Command("quickscrape"))
async def cmd_quickscrape(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    url = parts[1].strip() if len(parts) > 1 else ""
    if not url.startswith("http"):
        await msg.answer("Usage: /quickscrape https://…", parse_mode="HTML")
        return
    from tools.scraper_tool import scrape_url

    out = await scrape_url(url)
    await send_chunked(msg, out[:4000] if out else "Empty.")
