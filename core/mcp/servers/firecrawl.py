"""Firecrawl MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Firecrawl MCP server."""
    return [
        "/home/newadmin/.local/node18/bin/firecrawl-mcp"
    ]


def is_available() -> bool:
    """Check if Firecrawl MCP server is available."""
    return os.path.exists("/home/newadmin/.local/node18/bin/firecrawl-mcp")
