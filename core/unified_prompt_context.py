"""
Parallel prompt layers — single gather for wiki, Screenpipe, skills, graph, calendar, JST, RAG.

Used by llm_client.chat() so all optional context is fetched concurrently (<~800ms budget).
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
logger = logging.getLogger(__name__)

_VOICE_RULES = """
## VOICE MODE RULES
- Keep answers under ~3 sentences when the user is on a voice call.
- No markdown or code fences in spoken replies; say "I'll send the code on Telegram" when needed.
- Stay conversational and direct.
""".strip()


def _env_on(key: str, default: str = "0") -> bool:
    return os.getenv(key, default).strip().lower() in ("1", "true", "yes", "on")


def _jst_block() -> str:
    try:
        from zoneinfo import ZoneInfo

        jst = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%A, %B %d %Y — %H:%M JST")
        return f"## CURRENT DATETIME (Tokyo)\n{jst}"
    except Exception as exc:
        logger.debug("JST block skipped: %s", exc)
        return ""


async def _wiki_layer(query: str) -> str:
    if not _env_on("LEGION_WIKI_ENABLED", "1"):
        return ""
    try:
        from core.wiki_manager import get_wiki_manager

        return await get_wiki_manager().query(query, top_k=3) or ""
    except Exception as exc:
        logger.debug("unified wiki layer failed: %s", exc)
        return ""


async def _screenpipe_layer(query: str) -> str:
    if not _env_on("SCREENPIPE_ENABLED", "0"):
        return ""
    try:
        from tools.screenpipe_tool import get_screenpipe_tool

        sp = get_screenpipe_tool()
        return await sp.search(
            query,
            limit=int(os.getenv("SCREENPIPE_CONTEXT_LIMIT", "3")),
            hours_back=int(os.getenv("SCREENPIPE_CONTEXT_HOURS", "24")),
        )
    except Exception as exc:
        logger.debug("unified screenpipe layer failed: %s", exc)
        return ""


async def _rag_layer(query: str) -> str:
    if not (_env_on("LEGION_RAG_PROMPT_ENABLED", "0") or _env_on("LEGION_RAG_ENABLED", "0")):
        return ""
    try:
        from tools.rag_tool import rag_query

        return await rag_query(os.getenv("LEGION_RAG_COLLECTION", "legion_rag"), query, n_results=4)
    except Exception as exc:
        logger.debug("unified rag layer failed: %s", exc)
        return ""


async def _calendar_layer() -> str:
    if not _env_on("LEGION_MCP_CALENDAR_ENABLED", "0"):
        return ""
    try:
        from core.mcp_client import MCPClient

        client = MCPClient()
        raw = await asyncio.wait_for(
            client.get_calendar_events(days_ahead=int(os.getenv("LEGION_CALENDAR_DAYS", "3"))),
            timeout=float(os.getenv("LEGION_MCP_CALENDAR_TIMEOUT_SEC", "2.5")),
        )
        if not (raw or "").strip():
            return ""
        return f"## UPCOMING CALENDAR (MCP)\n{raw.strip()[:2000]}"
    except asyncio.TimeoutError:
        logger.debug("MCP calendar fetch timed out")
        return ""
    except Exception as exc:
        logger.debug("unified calendar layer failed: %s", exc)
        return ""


def _emotion_pad_layer() -> str:
    if os.getenv("LEGION_EMOTION_PROMPT_ENABLED", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from core.emotion_tracker import emotion_prompt_block

        return emotion_prompt_block() or ""
    except Exception as exc:
        logger.debug("unified emotion PAD failed: %s", exc)
        return ""


def _skills_layer(query: str) -> str:
    if os.getenv("LEGION_SKILLS_PROMPT_ENABLED", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from core.skill_registry import skills_prompt_block_for_query

        return skills_prompt_block_for_query(query) or ""
    except Exception as exc:
        logger.debug("unified skills layer failed: %s", exc)
        return ""


def _knowledge_graph_layer(query: str) -> str:
    if not _env_on("LEGION_KNOWLEDGE_GRAPH_ENABLED", "0"):
        return ""
    try:
        from core.knowledge_manager import get_knowledge_manager

        return get_knowledge_manager().prompt_snippet(query[:120]) or ""
    except Exception as exc:
        logger.debug("unified KG layer failed: %s", exc)
        return ""


async def gather_parallel_prompt_layers(
    user_message: str,
    user_id: str,
    *,
    mode: str = "text",
) -> list[str]:
    """
    Return ordered prompt fragments to append (non-empty only).
    Runs I/O-heavy fetches concurrently; sync snippets merged after gather.
    """
    if os.getenv("LEGION_UNIFIED_CONTEXT_ENABLED", "1").strip().lower() in ("0", "false", "no", "off"):
        return []

    q = (user_message or "").strip()
    if not q:
        q = "general context"

    jst = _jst_block()
    emo_fut = asyncio.to_thread(_emotion_pad_layer)
    wiki_fut = _wiki_layer(q)
    sp_fut = _screenpipe_layer(q)
    rag_fut = _rag_layer(q)
    cal_fut = _calendar_layer()

    wiki_r, sp_r, rag_r, cal_r, emo_r = await asyncio.gather(
        wiki_fut,
        sp_fut,
        rag_fut,
        cal_fut,
        emo_fut,
        return_exceptions=True,
    )

    blocks: list[str] = []
    if jst:
        blocks.append(jst)

    for label, res in (
        ("wiki", wiki_r),
        ("screenpipe", sp_r),
        ("rag", rag_r),
        ("calendar", cal_r),
        ("emotion_pad", emo_r),
    ):
        if isinstance(res, BaseException):
            logger.warning("parallel layer %s failed: %s", label, res)
            continue
        if isinstance(res, str) and res.strip():
            blocks.append(res.strip())

    sk = _skills_layer(q)
    if sk:
        blocks.append(sk)
    kg = _knowledge_graph_layer(q)
    if kg:
        blocks.append(kg)

    if (mode or "").strip().lower() == "voice":
        blocks.append(_VOICE_RULES)

    return blocks
