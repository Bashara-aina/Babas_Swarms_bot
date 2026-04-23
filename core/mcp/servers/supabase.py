"""Supabase MCP server configuration."""

from __future__ import annotations

import os


def _env(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def command() -> list[str]:
    """Return the command to start the Supabase MCP server."""
    return ["npx", "-y", "@modelcontextprotocol/server-supabase"]


def is_available() -> bool:
    """Check if Supabase MCP server is available."""
    return _env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL") != "" and _env(
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY"
    ) != ""
