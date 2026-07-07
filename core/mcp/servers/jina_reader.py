"""Jina Reader MCP server configuration."""

from __future__ import annotations


def command() -> list[str]:
    """Return the command to start the Jina Reader MCP server."""
    return [
        "/home/newadmin/miniconda3/bin/python3",
        "/home/newadmin/swarm-bot/tools/mcpServers/jina_reader_mcp/server.py",
    ]


def is_available() -> bool:
    """Check if Jina Reader MCP server is available."""
    import os
    return os.path.exists("/home/newadmin/swarm-bot/tools/mcpServers/jina_reader_mcp/server.py")
