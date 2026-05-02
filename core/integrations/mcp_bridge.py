"""core/integrations/mcp_bridge.py — Unified MCP tool integration layer.

Bridges the SwarmBot MCP infrastructure with external MCP servers via stdio.
Provides:
    - Server registry (filesystem, github, browser, memory, ruflo, etc.)
    - Tool call pool with persistent sessions
    - Server health monitoring
    - Fallback on connection failure

Usage:
    bridge = MCPBridge()
    result = await bridge.call_tool("filesystem", "read_file", {"path": "/tmp/test.txt"})
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

MCP_SERVER_REGISTRY: dict[str, dict[str, Any]] = {}


def register_mcp_server(name: str, command: list[str], description: str = "") -> None:
    """Register an MCP server in the global registry."""
    MCP_SERVER_REGISTRY[name] = {
        "command": command,
        "description": description,
        "enabled": True,
    }


def _load_opencode_servers() -> dict[str, Any]:
    """Load MCP servers from opencode.json config."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", ".opencode", "opencode.json")
    try:
        import json
        data = json.loads(open(path).read())
        mcp = data.get("mcp", {})
        servers = {}
        for name, cfg in mcp.items():
            if isinstance(cfg, dict) and cfg.get("type") == "local":
                cmd = cfg.get("command", [])
                if cmd:
                    servers[name] = {
                        "command": cmd,
                        "description": f"MCP server: {name}",
                        "enabled": True,
                    }
        return servers
    except Exception as exc:
        logger.warning("Failed to load opencode MCP servers: %s", exc)
        return {}


class MCPBridge:
    """Unified MCP tool access layer."""

    def __init__(self) -> None:
        self._cfg = _load_opencode_servers()
        self._sessions: dict[str, Any] = {}
        self._failed: dict[str, float] = {}
        self.FAILED_COOLDOWN = 30.0

    def _find_server(self, name: str) -> dict[str, Any] | None:
        if name in self._failed and (time.time() - self._failed[name]) < self.FAILED_COOLDOWN:
            return None
        return self._cfg.get(name) or MCP_SERVER_REGISTRY.get(name)

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on an MCP server."""
        srv = self._find_server(server_name)
        if not srv:
            return f"Error: MCP server '{server_name}' not found or in cooldown."

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return "Error: MCP Python SDK not installed (pip install mcp)"

        cmd = srv.get("command", [])
        if not cmd:
            return f"Error: MCP server '{server_name}' has no command."

        params = StdioServerParameters(
            command=str(cmd[0]),
            args=cmd[1:],
            env={**os.environ},
        )

        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return self._result_to_text(result)
        except Exception as exc:
            logger.error("MCP %s/%s failed: %s", server_name, tool_name, exc)
            self._failed[server_name] = time.time()
            return f"Error: MCP error ({server_name}/{tool_name}): {exc}"

    def _result_to_text(self, result: Any) -> str:
        if result is None:
            return ""
        content = getattr(result, "content", None)
        if content is None:
            return str(result)
        parts = []
        for block in content:
            text = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
            if text is not None:
                parts.append(str(text))
        return "\n".join(parts) if parts else str(result)

    async def list_tools(self, server_name: str) -> list[dict[str, str]]:
        """List available tools from an MCP server."""
        srv = self._find_server(server_name)
        if not srv:
            return []

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return []

        cmd = srv.get("command", [])
        if not cmd:
            return []

        params = StdioServerParameters(
            command=str(cmd[0]),
            args=cmd[1:],
            env={**os.environ},
        )
        out = []
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    for t in getattr(tools, "tools", None) or []:
                        name = getattr(t, "name", None) or ""
                        desc = getattr(t, "description", None) or ""
                        if name:
                            out.append({"name": str(name), "description": str(desc)[:500]})
        except Exception as exc:
            logger.debug("MCP list_tools %s failed: %s", server_name, exc)
        return out

    def server_status(self, server_name: str) -> dict[str, Any]:
        """Get health status of an MCP server."""
        in_cooldown = server_name in self._failed and (time.time() - self._failed[server_name]) < self.FAILED_COOLDOWN
        return {
            "name": server_name,
            "available": server_name in self._cfg or server_name in MCP_SERVER_REGISTRY,
            "in_cooldown": in_cooldown,
            "cooldown_remaining": max(0, self.FAILED_COOLDOWN - (time.time() - self._failed.get(server_name, 0))) if in_cooldown else 0,
        }


async def mcp_bridge_call(server: str, tool: str, args: dict[str, Any]) -> str:
    """Convenience function for MCP tool calls."""
    bridge = MCPBridge()
    return await bridge.call_tool(server, tool, args)
