"""Local Deep Research MCP server configuration."""

from __future__ import annotations


def command() -> list[str]:
    """Return the command to start the Local Deep Research MCP server.

    Note: Uses direct command (no bootstrap wrapper) because bootstrap
    FIFO filter causes issues with this server.
    """
    return [
        "/home/newadmin/miniconda3/bin/python3",
        "-m",
        "local_deep_research.mcp"
    ]


def is_available() -> bool:
    """Check if Local Deep Research MCP server is available."""
    import importlib.util
    return importlib.util.find_spec("local_deep_research") is not None
