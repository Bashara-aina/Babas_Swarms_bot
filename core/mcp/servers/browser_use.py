"""Browser-Use MCP server configuration."""

from __future__ import annotations


def command() -> list[str]:
    """Return the command to start the Browser-Use MCP server."""
    return [
        "/home/newadmin/miniconda3/bin/python3",
        "-m",
        "tools.mcpServers.browser_use_mcp.server"
    ]


def is_available() -> bool:
    """Check if Browser-Use MCP server is available."""
    import importlib.util
    return importlib.util.find_spec("browser_use") is not None
