"""Browser (Playwright) MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Browser MCP server."""
    return ["npx", "-y", "@modelcontextprotocol/server-browser"]


def is_available() -> bool:
    """Check if Browser MCP server is available."""
    return os.getenv("MCP_BROWSER_ENABLED", "0") == "1"
