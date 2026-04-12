"""GitHub MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the GitHub MCP server."""
    return ["npx", "-y", "@modelcontextprotocol/server-github"]


def is_available() -> bool:
    """Check if GitHub MCP server is available."""
    return os.getenv("GITHUB_TOKEN", "").strip() != ""
