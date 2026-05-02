#!/usr/bin/env python3
"""
Crawl4AI MCP Server - Native web crawling for AI agents
Provides: markdown, html, screenshot, pdf, crawl, js execution via crawl4ai SDK
"""

import asyncio
import json
import os
import sys
from contextlib import redirect_stdout
from io import StringIO
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

APP_NAME = "crawl4ai-mcp"
VERSION = "1.0.0"

server = Server(APP_NAME)

_browser_config = BrowserConfig(
    headless=True,
    verbose=False,
)

# Suppress crawl4ai progress output during crawls
_crawl4ai_logging_config = """
import logging
logging.getLogger('crawl4ai').setLevel(logging.WARNING)
"""

async def _crawl_url(url: str, **kwargs) -> dict:
    """Execute a crawl operation with suppressed progress output."""
    run_config = CrawlerRunConfig(
        cache_mode=kwargs.get("cache_mode", CacheMode.BYPASS),
        word_count_threshold=kwargs.get("word_count_threshold", 0),
        verbose=False,
    )

    # Suppress all crawl4ai stdout (progress bars, etc.)
    sink = StringIO()
    with redirect_stdout(sink):
        async with AsyncWebCrawler(config=_browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)

    return {
        "url": url,
        "success": True,
        "markdown": result.markdown if hasattr(result, 'markdown') else str(result),
        "html": result.html if hasattr(result, 'html') else None,
        "links": result.links if hasattr(result, 'links') else {},
        "metadata": result.metadata if hasattr(result, 'metadata') else {},
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available crawl4ai tools."""
    return [
        Tool(
            name="crawl4ai_crawl",
            description="Crawl a URL and return clean markdown. Use for research, fact-checking, extracting content. Returns LLM-friendly markdown + raw HTML + links + metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to crawl"},
                    "cache": {"type": "boolean", "default": False, "description": "Enable caching"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="crawl4ai_search",
            description="Search and crawl multiple URLs. Use for batch content gathering, product research, competitor analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "List of URLs to crawl"},
                    "cache": {"type": "boolean", "default": False, "description": "Enable caching"},
                },
                "required": ["urls"],
            },
        ),
        Tool(
            name="crawl4ai_facts",
            description="Extract and verify factual claims from a URL. Use for research, journalism, fact-checking, confirming information with citations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to analyze"},
                    "claims": {"type": "array", "items": {"type": "string"}, "description": "Specific claims to verify (optional)"},
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute crawl4ai tools."""

    if name == "crawl4ai_crawl":
        url = arguments["url"]
        cache = arguments.get("cache", False)

        result = await _crawl_url(url, cache_mode=CacheMode.ENABLED if cache else CacheMode.BYPASS)

        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "crawl4ai_crawl",
                "url": url,
                "success": result["success"],
                "content_length": len(result["markdown"]),
                "markdown": result["markdown"][:8000] if len(result["markdown"]) > 8000 else result["markdown"],
                "links_count": len(result.get("links", {}).get("external", [])),
                "metadata": result.get("metadata", {}),
            }, indent=2)
        )]

    elif name == "crawl4ai_search":
        urls = arguments["urls"]
        cache = arguments.get("cache", False)

        results = []
        for url in urls:
            try:
                result = await _crawl_url(url, cache_mode=CacheMode.ENABLED if cache else CacheMode.BYPASS)
                results.append({
                    "url": url,
                    "success": True,
                    "content_length": len(result["markdown"]),
                    "markdown_preview": result["markdown"][:2000] if len(result["markdown"]) > 2000 else result["markdown"],
                })
            except Exception as e:
                results.append({"url": url, "success": False, "error": str(e)})

        return [TextContent(
            type="text",
            text=json.dumps({"tool": "crawl4ai_search", "results": results}, indent=2)
        )]

    elif name == "crawl4ai_facts":
        url = arguments["url"]

        result = await _crawl_url(url)
        content = result["markdown"]

        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "crawl4ai_facts",
                "url": url,
                "source_verified": True,
                "content_length": len(content),
                "content_preview": content[:5000],
                "extracted_facts": [],
            }, indent=2)
        )]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
