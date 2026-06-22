"""MCP client for Model Context Protocol communication via stdio."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPClient:
    """Async MCP client that communicates with MCP servers over stdio."""

    def __init__(self, command: list[str]) -> None:
        self.command = command
        self._proc: asyncio.subprocess.Process | None = None
        self._request_id = 0

    async def start(self) -> None:
        """Start the MCP server subprocess."""
        self._proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info("MCP client started: %s", " ".join(self.command))
        # Perform the MCP initialize handshake so real servers accept subsequent
        # tools/list / tools/call requests. (Without this, strict MCP servers
        # like graphify.serve hang on the first tools/list because they wait
        # for the initialize → notifications/initialized sequence first.)
        await self._initialize_mcp_session()

    async def _initialize_mcp_session(self) -> None:
        """Send MCP initialize + notifications/initialized. Idempotent."""
        init_req = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "swarm-bot-mcp-client", "version": "0.1"},
            },
        }
        self._request_id += 1
        assert self._proc and self._proc.stdin
        self._proc.stdin.write(json.dumps(init_req).encode() + b"\n")
        await self._proc.stdin.drain()
        # Read the initialize response (some servers include extra info on this line)
        line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=10.0)  # type: ignore[reportOptionalMemberAccess]
        # Send the notifications/initialized notification (no id, no response expected)
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        self._proc.stdin.write(json.dumps(notif).encode() + b"\n")
        await self._proc.stdin.drain()
        logger.debug("MCP initialize handshake complete (got %d bytes)", len(line))

    async def call(self, tool_name: str, params: dict[str, Any] | None = None) -> Any:
        """Call an MCP tool by name with optional parameters."""
        if not self._proc:
            raise RuntimeError("MCP client not started")
        self._request_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": tool_name,
            "params": params or {},
        }
        self._proc.stdin.write(json.dumps(req).encode() + b"\n")  # type: ignore[reportOptionalMemberAccess]  # StreamWriter.write() is sync; drain() below is the async flush
        await self._proc.stdin.drain()  # type: ignore[reportOptionalMemberAccess]
        line = await self._proc.stdout.readline()  # type: ignore[reportOptionalMemberAccess]
        resp = json.loads(line.decode())
        if "error" in resp:
            raise RuntimeError(f"MCP error: {resp['error']}")
        return resp.get("result")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server.

        The MCP ``tools/list`` response wraps the tool schemas in
        ``{"tools": [...]}``. Older callers expected a bare list, so we
        normalize to a list here.
        """
        result = await self.call("tools/list")
        if isinstance(result, dict) and "tools" in result:
            return list(result.get("tools") or [])
        if isinstance(result, list):
            return result
        return []

    async def stop(self) -> None:
        """Stop the MCP server subprocess."""
        if self._proc:
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.terminate()
            await self._proc.wait()
