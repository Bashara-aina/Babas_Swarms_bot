"""Brave Search MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Brave Search MCP server."""
    return ["npx", "-y", "@modelcontextprotocol/server-brave-search"]


def is_available() -> bool:
    """Check if Brave Search MCP server is available."""
    return os.getenv("BRAVE_API_KEY", "").strip() != ""
