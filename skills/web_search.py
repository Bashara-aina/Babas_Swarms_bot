"""Web search skill — DuckDuckGo with SerpAPI fallback.

Provides real-time web search for Legion using async DuckDuckGo API.
Falls back to SerpAPI if SERPAPI_KEY is set.

Usage:
    ws = WebSearch()
    results = await ws.search("latest AI agents 2026", num_results=5)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── DuckDuckGo async search ────────────────────────────────────────────────────


async def _duckduckgo_search(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search DuckDuckGo using the v2 DDG API (no API key required)."""
    import aiohttp

    try:
        encoded_q = query.replace("+", "%2B").replace(" ", "+")
        url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json&no_html=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        results: list[dict[str, Any]] = []
        # Related topics / instant answer topics (often give real URLs)
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if not topic.get("Text"):
                continue
            if topic.get("FirstURL"):
                results.append(
                    {
                        "title": topic.get("Text", "")[:120],
                        "url": topic["FirstURL"],
                        "snippet": topic.get("Text", "")[:200],
                    }
                )
            elif topic.get("Name"):
                # Disambiguation or category
                results.append(
                    {
                        "title": topic["Name"],
                        "url": "",
                        "snippet": topic.get("Text", ""),
                    }
                )

        return results
    except Exception as e:
        logger.warning("[WebSearch] DuckDuckGo search failed: %s", e)
        return []


async def _serpapi_search(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search using SerpAPI (Google results) if SERPAPI_KEY is set."""
    import aiohttp

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "num": num_results},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        results: list[dict[str, Any]] = []
        for item in data.get("organic_results", [])[:num_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
        return results
    except Exception as e:
        logger.warning("[WebSearch] SerpAPI search failed: %s", e)
        return []


class WebSearch:
    """Async web search using DuckDuckGo (primary) or SerpAPI (fallback)."""

    async def search(self, query: str, num_results: int = 5) -> list[dict[str, Any]]:
        """
        Search the web for `query`.

        Returns a list of dicts: [{"title": ..., "url": ..., "snippet": ...}]
        Tries DuckDuckGo first; falls back to SerpAPI if SERPAPI_KEY is set.
        """
        results = await _duckduckgo_search(query, num_results)
        if results:
            return results

        serp_results = await _serpapi_search(query, num_results)
        if serp_results:
            return serp_results

        return []

    def format_for_telegram(self, results: list[dict[str, Any]], query: str) -> str:
        """Format search results as Telegram HTML."""
        if not results:
            return f"🔍 No results found for <b>{query}</b>"

        lines = [f"🔍 <b>Web Search</b>: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "Unknown")[:80]
            url = r.get("url", "")
            snippet = r.get("snippet", "")[:120]
            if url:
                lines.append(f"{i}. <a href='{url}'>{title}</a>")
            else:
                lines.append(f"{i}. {title}")
            if snippet:
                lines.append(f"   {snippet}")
            lines.append("")
        return "\n".join(lines)
