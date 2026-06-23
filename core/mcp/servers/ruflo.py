"""Ruflo MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Ruflo MCP server.

    Note: Uses direct command (no bootstrap wrapper) because ruflo outputs
    text that confuses the bootstrap FIFO filter.
    """
    ruflo_bin = "/home/newadmin/.local/node18/bin/ruflo"
    if not os.path.exists(ruflo_bin):
        ruflo_bin = "/home/newadmin/.local/bin/ruflo"
    return [ruflo_bin, "mcp", "start"]


def is_available() -> bool:
    """Check if Ruflo MCP server is available."""
    return os.path.exists("/home/newadmin/.local/node18/bin/ruflo") or os.path.exists("/home/newadmin/.local/bin/ruflo")
