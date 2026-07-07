#!/usr/bin/env python3
"""
SearXNG + Crawl4AI MCP Server
Provides SearXNG metasearch (via locahost:8888) with optional
deep crawling of result pages via Crawl4AI.
"""

from __future__ import annotations

import json
import os
from typing import Any, Sequence

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

APP_NAME = "searxng-mcp"
VERSION = "1.0.0"

# Default to local SearXNG instance
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888")
CRAWL4AI_AVAILABLE = False

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    pass

server = Server(APP_NAME)


def _format_results(results: list[dict]) -> str:
    """Format search results into readable text."""
    lines = []
    for i, r in enumerate(results):
        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "")
        engine = r.get("engine", "")
        snippet = content[:300] if content else ""
        lines.append(f"[{i+1}] {title}")
        lines.append(f"    URL: {url}")
        if snippet:
            lines.append(f"    {snippet}")
        if engine:
            lines.append(f"    (source: {engine})")
        lines.append("")
    return "\n".join(lines)


@server.list_tools()
async def list_tools() -> list[Tool]:
    tools = [
        Tool(
            name="web_search",
            description=(
                "Search the web via SearXNG metasearch engine. "
                "Returns results from multiple search engines aggregated together. "
                "Privacy-respecting, no tracking."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "engines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search engines to use (e.g. duckduckgo, google, bing, brave)",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g. en, de, fr)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10)",
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range filter: day, week, month, year",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search categories: general, news, images, files, map, music, it, science, social_media",
                    },
                },
                "required": ["query"],
            },
        ),
    ]

    if CRAWL4AI_AVAILABLE:
        tools.append(
            Tool(
                name="search_and_crawl",
                description=(
                    "Search the web then deep-crawl the top result pages. "
                    "Combines SearXNG search with Crawl4AI for full page content extraction. "
                    "Use when you need more than snippets."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Number of search results to fetch (default 5)",
                        },
                        "max_crawl": {
                            "type": "integer",
                            "description": "Number of top results to deep-crawl (default 3)",
                        },
                        "engines": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Search engines to use",
                        },
                    },
                    "required": ["query"],
                },
            )
        )

    return tools


async def _search_searxng(
    query: str,
    categories: list[str] | None = None,
    engines: list[str] | None = None,
    language: str = "auto",
    max_results: int = 10,
    time_range: str | None = None,
) -> list[dict]:
    """Execute a search against local SearXNG instance."""
    params: dict[str, Any] = {
        "q": query,
        "format": "json",
        "language": language,
        "pageno": 1,
    }
    if categories:
        params["categories"] = ",".join(categories)
    if engines:
        params["engines"] = ",".join(engines)
    if time_range:
        params["time_range"] = time_range

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.get(f"{SEARXNG_URL}/search", params=params)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            return [{"title": "Search Error", "url": "", "content": f"SearXNG error: {exc}"}]

    results = data.get("results", [])
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "engine": r.get("engine", ""),
        }
        for r in results[:max_results]
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    if name == "web_search":
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)
        results = await _search_searxng(
            query=query,
            categories=arguments.get("categories"),
            engines=arguments.get("engines"),
            language=arguments.get("language", "auto"),
            max_results=max_results,
            time_range=arguments.get("time_range"),
        )
        formatted = _format_results(results)
        summary = f"SearXNG search results for '{query}'"
        return [TextContent(type="text", text=f"# {summary}\n\n{formatted}")]

    if name == "search_and_crawl" and CRAWL4AI_AVAILABLE:
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)
        max_crawl = arguments.get("max_crawl", 3)

        results = await _search_searxng(
            query=query,
            engines=arguments.get("engines"),
            max_results=max_results,
        )
        formatted = _format_results(results)
        parts = [f"# Search results for '{query}'\n\n{formatted}"]

        # crawl top N results
        urls_to_crawl = [r["url"] for r in results[:max_crawl] if r.get("url")]
        if urls_to_crawl:
            parts.append(f"\n## Deep-crawling {len(urls_to_crawl)} pages\n")
            async with AsyncWebCrawler() as crawler:
                for url in urls_to_crawl:
                    try:
                        result = await crawler.arun(url=url)
                        content = (result.markdown or "")[:3000]
                        title = getattr(result, "metadata", {}).get("title", "")
                        parts.append(f"### {title}\n{url}\n\n{content}\n")
                    except Exception as exc:
                        parts.append(f"### Failed to crawl\n{url}\n\nError: {exc}\n")

        return [TextContent(type="text", text="\n".join(parts))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
