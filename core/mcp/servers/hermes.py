"""Hermes MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Hermes MCP server."""
    return [
        "/home/newadmin/swarm-bot/tools/mcpServers/bootstrap/mcp_bootstrap.sh",
        "hermes", "mcp", "serve"
    ]


def is_available() -> bool:
    """Check if Hermes MCP server is available."""
    return os.path.exists("/home/newadmin/swarm-bot/ext/hermes-agent") or os.path.exists("/home/newadmin/.local/bin/hermes")
