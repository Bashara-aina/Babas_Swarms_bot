"""Scrapling MCP server configuration."""

from __future__ import annotations


def command() -> list[str]:
    """Return the command to start the Scrapling MCP server."""
    return [
        "/home/newadmin/miniconda3/bin/python3",
        "/home/newadmin/swarm-bot/tools/mcpServers/scrapling_mcp/server.py",
    ]


def is_available() -> bool:
    """Check if Scrapling MCP server is available."""
    import importlib.util
    return importlib.util.find_spec("scrapling") is not None
