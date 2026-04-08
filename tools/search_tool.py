"""Web search via Tavily API (optional TAVILY_API_KEY)."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 6) -> str:
    key = (os.getenv("TAVILY_API_KEY") or "").strip()
    if not key:
        return ""
    payload = {
        "api_key": key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post("https://api.tavily.com/search", json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.warning("Tavily search failed: %s", exc)
        return ""

    results = data.get("results") or []
    if not isinstance(results, list) or not results:
        return ""
    lines: list[str] = []
    for item in results[:max_results]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or ""
        url = item.get("url") or ""
        content = (item.get("content") or "")[:280]
        lines.append(f"• {title}\n  {url}\n  {content}")
    return "## WEB SEARCH\n" + "\n\n".join(lines)
