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
        await self._proc.stdin.write(json.dumps(req).encode())
        await self._proc.stdin.drain()
        line = await self._proc.stdout.readline()
        resp = json.loads(line.decode())
        if "error" in resp:
            raise RuntimeError(f"MCP error: {resp['error']}")
        return resp.get("result")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server."""
        return await self.call("tools/list") or []

    async def stop(self) -> None:
        """Stop the MCP server subprocess."""
        if self._proc:
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.terminate()
            await self._proc.wait()
