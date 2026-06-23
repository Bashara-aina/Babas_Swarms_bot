"""Sequential Thinking MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Sequential Thinking MCP server."""
    return [
        "/home/newadmin/swarm-bot/tools/mcpServers/bootstrap/mcp_bootstrap.sh",
        "@modelcontextprotocol/server-sequential-thinking"
    ]


def is_available() -> bool:
    """Check if Sequential Thinking MCP server is available."""
    return os.path.exists("/home/newadmin/.local/node18/bin/npx")
