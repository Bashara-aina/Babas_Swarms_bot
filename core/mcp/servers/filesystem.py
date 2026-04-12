"""Filesystem MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Filesystem MCP server."""
    return ["npx", "-y", "@modelcontextprotocol/server-filesystem", os.getenv("MCP_FILESYSTEM_PATH", ".")]


def is_available() -> bool:
    """Check if Filesystem MCP server is available."""
    return os.getenv("MCP_FILESYSTEM_ENABLED", "0") == "1"
