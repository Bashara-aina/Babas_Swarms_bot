"""Exa MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Exa MCP server."""
    return [
        "/home/newadmin/swarm-bot/tools/mcpServers/bootstrap/mcp_bootstrap.sh",
        "/home/newadmin/.local/node18/bin/exa-mcp-server"
    ]


def is_available() -> bool:
    """Check if Exa MCP server is available."""
    return os.path.exists("/home/newadmin/.local/node18/bin/exa-mcp-server")
