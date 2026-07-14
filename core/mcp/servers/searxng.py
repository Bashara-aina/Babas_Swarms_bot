"""SearXNG MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the SearXNG MCP server."""
    return [
        "/home/newadmin/miniconda3/bin/python3",
        "/home/newadmin/swarm-bot/tools/mcpServers/searxng_mcp/server.py",
    ]


def is_available() -> bool:
    """Check if SearXNG MCP server is available."""
    return os.path.exists("/home/newadmin/swarm-bot/tools/mcpServers/searxng_mcp/server.py")
