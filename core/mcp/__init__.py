"""MCP (Model Context Protocol) package."""

from core.mcp.client import MCPClient
from core.mcp.manager import MCP_MANAGER, MCPManager

__all__ = ["MCPClient", "MCP_MANAGER", "MCPManager"]
