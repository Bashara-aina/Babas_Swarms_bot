"""MCP manager for starting and managing multiple MCP server clients."""

from __future__ import annotations

import logging
import os

from core.mcp.client import MCPClient

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages multiple MCP server clients."""

    def __init__(self) -> None:
        self._clients: dict[str, MCPClient] = {}

    def _is_enabled(self, name: str) -> bool:
        """Check if an MCP server is enabled via environment variable."""
        return os.getenv(f"MCP_{name.upper()}_ENABLED", "0") == "1"

    async def start_all(self) -> None:
        """Start all enabled MCP servers."""
        from core.mcp.servers import (
            brave,
            browser,
            filesystem,
            github,
            obsidian,
            supabase,
        )

        for name, server_config in [
            ("brave", brave),
            ("github", github),
            ("filesystem", filesystem),
            ("obsidian", obsidian),
            ("supabase", supabase),
            ("browser", browser),
        ]:
            if self._is_enabled(name) and server_config.is_available():
                try:
                    client = MCPClient(server_config.command())
                    await client.start()
                    tools = await client.list_tools()
                    self._clients[name] = client
                    logger.info("MCP %s: %d tools registered", name, len(tools))
                except Exception as e:
                    logger.warning("MCP %s failed to start: %s", name, e)

    async def stop_all(self) -> None:
        """Stop all MCP server clients."""
        for client in self._clients.values():
            await client.stop()
        self._clients.clear()


MCP_MANAGER = MCPManager()
