"""GitNexus MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the GitNexus MCP server."""
    return ["pnpm", "dlx", "--allow-build=kuzu", "gitnexus@1.4.0", "mcp"]


def is_available() -> bool:
    """Check if GitNexus MCP server is available."""
    return os.getenv("MCP_GITNEXUS_ENABLED", "0") == "1"
