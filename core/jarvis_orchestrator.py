"""
Jarvis-style context bundle: memory + Screenpipe + WhatsApp (sidecar/MCP) + optional calendar.

Produces a single assistant-facing brief for Legion; does not send messages or run shell.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def _memory_layer(query: str, user_id: str) -> str:
    if os.getenv("LEGION_JARVIS_MEMORY", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from core.legion_memory_facade import get_memory_facade

        return await get_memory_facade().contextual_snapshot(query, user_id) or ""
    except Exception as exc:
        logger.debug("jarvis memory layer: %s", exc)
        return ""


async def _screenpipe_layer(query: str) -> str:
    if os.getenv("SCREENPIPE_ENABLED", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    if os.getenv("LEGION_JARVIS_SCREENPIPE", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from tools.screenpipe_tool import get_screenpipe_tool

        sp = get_screenpipe_tool()
        if not sp.is_configured():
            return ""
        return await sp.search(
            query,
            limit=int(os.getenv("LEGION_JARVIS_SCREENPIPE_LIMIT", "5")),
            hours_back=int(os.getenv("LEGION_JARVIS_SCREENPIPE_HOURS", "4")),
        )
    except Exception as exc:
        logger.debug("jarvis screenpipe: %s", exc)
        return ""


async def _whatsapp_sidecar_layer(limit: int) -> str:
    if os.getenv("LEGION_JARVIS_WHATSAPP", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from bridges.whatsapp_bridge import WhatsAppBridge

        b = WhatsAppBridge()
        if not await b._is_healthy():
            return ""
        msgs = await b.get_unread(limit=limit)
        if not msgs:
            return ""
        lines: list[str] = ["## WHATSAPP (sidecar — unread / recent)"]
        for m in msgs[:limit]:
            if not isinstance(m, dict):
                continue
            who = m.get("from") or m.get("chatId") or m.get("author") or "?"
            body = (m.get("body") or m.get("text") or m.get("message") or "")[:500]
            lines.append(f"- **{who}**: {body}")
        return "\n".join(lines)
    except Exception as exc:
        logger.debug("jarvis wa sidecar: %s", exc)
        return ""


async def _whatsapp_mcp_layer(limit: int) -> str:
    if os.getenv("LEGION_JARVIS_MCP_WHATSAPP", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    try:
        from core.mcp_client import MCPClient

        raw = await MCPClient().read_whatsapp_messages(limit=limit)
        if not (raw or "").strip():
            return ""
        return f"## WHATSAPP (MCP)\n{raw.strip()[:4000]}"
    except Exception as exc:
        logger.debug("jarvis wa mcp: %s", exc)
        return ""


async def _calendar_layer() -> str:
    if os.getenv("LEGION_JARVIS_CALENDAR", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    try:
        from core.mcp_client import MCPClient

        return await asyncio.wait_for(
            MCPClient().get_calendar_events(days_ahead=int(os.getenv("LEGION_JARVIS_CALENDAR_DAYS", "3"))),
            timeout=float(os.getenv("LEGION_JARVIS_CALENDAR_TIMEOUT_SEC", "2.5")),
        )
    except Exception as exc:
        logger.debug("jarvis calendar: %s", exc)
        return ""


def _emotion_hint() -> str:
    if os.getenv("LEGION_JARVIS_EMOTION", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from core.emotion_tracker import emotion_prompt_block

        return (emotion_prompt_block() or "").strip()
    except Exception:
        return ""


async def gather_jarvis_bundle(user_goal: str, user_id: str) -> dict[str, Any]:
    """
    Collect parallel context slices for one user turn.

    Returns keys: goal, memory, screenpipe, whatsapp, calendar, emotion (strings).
    """
    goal = (user_goal or "").strip()
    uid = str(user_id or "").strip()
    wa_limit = int(os.getenv("LEGION_JARVIS_WA_LIMIT", "12"))

    memory_f, sp_f, wa_sc, wa_mcp, cal_f = await asyncio.gather(
        _memory_layer(goal, uid),
        _screenpipe_layer(goal or "error terminal code"),
        _whatsapp_sidecar_layer(wa_limit),
        _whatsapp_mcp_layer(wa_limit),
        _calendar_layer(),
        return_exceptions=True,
    )

    def _safe(x: Any) -> str:
        if isinstance(x, BaseException):
            logger.debug("jarvis gather subtask: %s", x)
            return ""
        return str(x or "")

    cal_text = _safe(cal_f)
    cal_block = f"## CALENDAR\n{cal_text}" if cal_text.strip() else ""

    wa_sc_text = _safe(wa_sc)
    wa_mcp_text = _safe(wa_mcp)
    whatsapp_combined = "\n\n".join(t for t in (wa_sc_text, wa_mcp_text) if t.strip())

    return {
        "goal": goal,
        "memory": _safe(memory_f),
        "screenpipe": _safe(sp_f),
        "whatsapp": whatsapp_combined,
        "calendar": cal_block,
        "emotion": _emotion_hint(),
    }


async def compose_jarvis_response(bundle: dict[str, Any]) -> str:
    """Turn bundle into a Telegram-safe Legion message (no sends)."""
    sections: list[str] = []
    if bundle.get("emotion"):
        sections.append(bundle["emotion"])
    if bundle.get("memory"):
        sections.append(bundle["memory"])
    if bundle.get("screenpipe"):
        sections.append(bundle["screenpipe"])
    if bundle.get("whatsapp"):
        sections.append(bundle["whatsapp"])
    if bundle.get("calendar"):
        sections.append(bundle["calendar"])

    context = "\n\n".join(sections)[:14000]
    goal = bundle.get("goal") or "(no goal text)"

    from llm_client import wiki_raw_completion

    model = os.getenv("LEGION_JARVIS_MODEL", "groq/llama-3.3-70b-versatile")
    prompt = f"""User goal (Bashara):
{goal}

Context gathered from Legion sensors (may be partial or empty):
{context or "(no extra context retrieved)"}

Write a single Telegram message for Bashara with these sections (use clear headings):

## Situation
2–4 sentences: what you infer from context + goal.

## Suggested actions
Numbered list: concrete next steps (e.g. fix error path, research library, check Supabase, draft guest reply). Mention tools: /research, /do, /screen, wiki, MCP when relevant.

## Draft reply (only if a guest/customer WhatsApp-style message appears in context)
Write a polite draft in Indonesian-English mix as appropriate. If no guest message, write: (none — no guest thread in context)

## Safety
State explicitly: **No messages were sent.** WhatsApp/email sends require Bashara's separate confirmation or existing /wa flows.

Keep total under ~3500 characters. No markdown code blocks."""

    body = await wiki_raw_completion(prompt, model=model, max_tokens=1200, temperature=0.35)
    if not (body or "").strip():
        return (
            "Jarvis bundle was gathered but the synthesis model returned empty. "
            "Raw context length: "
            f"{len(context)} chars. Check GROQ_API_KEY / LEGION_JARVIS_MODEL."
        )
    return body.strip()
