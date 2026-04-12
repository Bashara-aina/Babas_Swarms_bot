"""Obsidian MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Obsidian MCP server."""
    vault_path = os.getenv("MCP_OBSIDIAN_VAULT_PATH", "")
    if vault_path:
        return ["npx", "-y", "@modelcontextprotocol/server-obsidian", vault_path]
    return ["npx", "-y", "@modelcontextprotocol/server-obsidian"]


def is_available() -> bool:
    """Check if Obsidian MCP server is available."""
    return os.getenv("MCP_OBSIDIAN_ENABLED", "0") == "1"
