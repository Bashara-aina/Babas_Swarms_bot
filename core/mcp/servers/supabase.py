"""Supabase MCP server configuration."""

from __future__ import annotations

import os


def command() -> list[str]:
    """Return the command to start the Supabase MCP server."""
    return ["npx", "-y", "@modelcontextprotocol/server-supabase"]


def is_available() -> bool:
    """Check if Supabase MCP server is available."""
    return os.getenv("SUPABASE_URL", "").strip() != "" and os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() != ""
