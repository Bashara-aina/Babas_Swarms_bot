"""Crawl4AI MCP server configuration."""

from __future__ import annotations


def command() -> list[str]:
    """Return the command to start the Crawl4AI MCP server."""
    return [
        "/home/newadmin/miniconda3/bin/python3",
        "/home/newadmin/swarm-bot/tools/mcpServers/crawl4ai_mcp/server.py"
    ]


def is_available() -> bool:
    """Check if Crawl4AI MCP server is available."""
    try:
        from crawl4ai import AsyncWebCrawler
        return True
    except ImportError:
        return False