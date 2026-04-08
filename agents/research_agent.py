"""
Research pipeline — DeerFlow-style multi-step research using existing Legion routers.

Phase 1: web search (Tavily) when key present; phase 2: deep synthesis via researcher agent.
"""

from __future__ import annotations

import logging
import os

from llm_client import chat

logger = logging.getLogger(__name__)


async def run_research_pipeline(topic: str, *, user_id: str | None = None) -> str:
    topic = (topic or "").strip()
    if not topic:
        return "Empty research topic."
    uid = user_id or "research_pipeline"
    chunks: list[str] = []

    if (os.getenv("TAVILY_API_KEY") or "").strip():
        try:
            from tools.search_tool import web_search

            raw = await web_search(topic, max_results=5)
            if raw:
                chunks.append(raw)
        except Exception as exc:
            logger.debug("research tavily skipped: %s", exc)

    try:
        from tools.browser_tool import fetch_page_text

        if topic.startswith("http://") or topic.startswith("https://"):
            page = await fetch_page_text(topic, max_chars=8000)
            if page:
                chunks.append("## PAGE TEXT\n" + page[:6000])
    except Exception as exc:
        logger.debug("research browser skipped: %s", exc)

    context = "\n\n".join(chunks)[:12000]
    prompt = (
        "You are Legion's research agent. Synthesize the following sources into a structured answer "
        "with sections: Summary, Key facts, Risks/unknowns, Suggested next steps.\n\n"
        f"Topic: {topic}\n\nSources:\n{context or '(no external fetch — use general knowledge carefully)'}"
    )
    answer, _ = await chat(prompt, agent_key="researcher", user_id=str(uid))
    return answer
