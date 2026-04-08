"""MCP — config loading, status, stdio tool calls, and convenience wrappers."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "mcp_config.json"


def load_mcp_config() -> dict[str, Any]:
    if not _CONFIG_PATH.exists():
        return {"servers": [], "mcpServers": {}}
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("mcp_config.json read failed: %s", exc)
        return {"servers": [], "mcpServers": {}}

    servers = list(data.get("servers") or [])
    meta = data.get("mcpServers") or {}
    known = {s.get("name") for s in servers if isinstance(s, dict)}
    for name, m in meta.items():
        if name in known:
            continue
        servers.append(
            {
                "name": name,
                "command": "",
                "args": [],
                "enabled": False,
                "description": (m or {}).get("description", "") if isinstance(m, dict) else "",
            }
        )
    data["servers"] = servers
    return data


def format_mcp_status() -> str:
    cfg = load_mcp_config()
    servers = cfg.get("servers") or []
    if not servers:
        return "No MCP servers in config/mcp_config.json."
    lines = ["<b>MCP servers</b>"]
    for s in servers:
        if not isinstance(s, dict):
            continue
        en = "on" if s.get("enabled") else "off"
        name = s.get("name", "?")
        cmd = s.get("command", "")
        args = " ".join(s.get("args") or [])
        lines.append(f"• {name} [{en}]: <code>{cmd} {args}</code>".strip())
    return "\n".join(lines)


def _tool_result_to_text(result: Any) -> str:
    if result is None:
        return ""
    content = getattr(result, "content", None)
    if content is None:
        return str(result)
    parts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(str(text))
        elif isinstance(block, dict):
            parts.append(str(block.get("text") or block))
    return "\n".join(parts) if parts else str(result)


class MCPClient:
    """Stdio MCP client — one connection per tool call (avoids zombie processes)."""

    def __init__(self) -> None:
        self._cfg = load_mcp_config()

    def _find_server(self, server_name: str) -> dict[str, Any] | None:
        for s in self._cfg.get("servers") or []:
            if isinstance(s, dict) and s.get("name") == server_name:
                return s
        return None

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        srv = self._find_server(server_name)
        if not srv:
            return f"MCP server '{server_name}' not in config."
        if not srv.get("enabled"):
            return f"MCP server '{server_name}' is disabled in config."

        try:
            from mcp import ClientSession, StdioServerParameters  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except Exception as exc:
            logger.warning("mcp SDK not installed: %s", exc)
            return "MCP Python SDK not installed (pip install mcp)."

        cmd = srv.get("command")
        if not cmd:
            return f"MCP server '{server_name}' has no command configured."
        args = list(srv.get("args") or [])
        env = {**os.environ, **(srv.get("env") or {})}
        params = StdioServerParameters(command=str(cmd), args=args, env=env)

        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return _tool_result_to_text(result)[:12000] or "(empty tool result)"
        except Exception as exc:
            logger.error("MCP call_tool %s/%s failed: %s", server_name, tool_name, exc)
            return f"MCP error ({server_name}/{tool_name}): {exc}"

    async def list_tools(self, server_name: str) -> list[dict[str, str]]:
        srv = self._find_server(server_name)
        if not srv or not srv.get("enabled"):
            return []
        try:
            from mcp import ClientSession, StdioServerParameters  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except Exception:
            return []

        cmd = srv.get("command")
        if not cmd:
            return []
        params = StdioServerParameters(
            command=str(cmd),
            args=list(srv.get("args") or []),
            env={**os.environ, **(srv.get("env") or {})},
        )
        out: list[dict[str, str]] = []
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    for t in getattr(listed, "tools", None) or []:
                        name = getattr(t, "name", None) or ""
                        desc = getattr(t, "description", None) or ""
                        if name:
                            out.append({"name": str(name), "description": str(desc)[:500]})
        except Exception as exc:
            logger.debug("MCP list_tools failed: %s", exc)
        return out

    async def get_calendar_events(self, days_ahead: int = 7) -> str:
        server = os.getenv("LEGION_MCP_CALENDAR_SERVER", "gmail")
        for tool in (
            "list_calendar_events",
            "calendar_list_events",
            "get_calendar_events",
            "list_events",
        ):
            text = await self.call_tool(server, tool, {"days_ahead": days_ahead})
            if text and "disabled" not in text.lower() and "not in config" not in text.lower():
                return text
        return ""

    async def read_gmail(self, query: str = "is:unread", max_results: int = 5) -> str:
        server = os.getenv("LEGION_MCP_GMAIL_SERVER", "gmail")
        for tool in ("search_emails", "gmail_search", "list_messages"):
            t = await self.call_tool(server, tool, {"query": query, "max_results": max_results})
            if t and "disabled" not in t.lower():
                return t
        return ""

    async def send_email(self, to: str, subject: str, body: str) -> str:
        server = os.getenv("LEGION_MCP_GMAIL_SERVER", "gmail")
        return await self.call_tool(
            server,
            "send_email",
            {"to": to, "subject": subject, "body": body},
        )

    async def create_github_issue(self, repo: str, title: str, body: str) -> str:
        server = os.getenv("LEGION_MCP_GITHUB_SERVER", "github")
        owner = os.getenv("GITHUB_DEFAULT_OWNER", "Bashara-aina")
        return await self.call_tool(
            server,
            "create_issue",
            {"owner": owner, "repo": repo, "title": title, "body": body},
        )

    async def setup_legion_inbox(self) -> str:
        server = os.getenv("LEGION_MCP_AGENTMAIL_SERVER", "agentmail")
        return await self.call_tool(
            server,
            "create_inbox",
            {
                "username": os.getenv("AGENTMAIL_USERNAME", "legion"),
                "display_name": os.getenv("AGENTMAIL_DISPLAY_NAME", "Legion — Bashara's AI Assistant"),
            },
        )

    async def read_agentmail(self) -> str:
        server = os.getenv("LEGION_MCP_AGENTMAIL_SERVER", "agentmail")
        return await self.call_tool(
            server,
            "list_messages",
            {"inbox_id": os.getenv("AGENTMAIL_INBOX_ID", "")},
        )

    async def read_whatsapp_messages(self, limit: int = 10) -> str:
        """Best-effort MCP WhatsApp read — tool names vary by server implementation."""
        server = os.getenv("LEGION_MCP_WHATSAPP_SERVER", "whatsapp")
        for tool in (
            "get_messages",
            "list_messages",
            "whatsapp_get_messages",
            "read_messages",
        ):
            text = await self.call_tool(server, tool, {"limit": limit})
            if text and "disabled" not in text.lower() and "not in config" not in text.lower():
                if "MCP error" not in text and "no command" not in text.lower():
                    return text
        return ""


async def try_list_tools_stdio(server: dict[str, Any]) -> list[str]:
    """Best-effort: connect using inline server dict (for /mcp_status diagnostics)."""
    try:
        from mcp import ClientSession, StdioServerParameters  # type: ignore
        from mcp.client.stdio import stdio_client  # type: ignore
    except Exception:
        return []

    cmd = server.get("command")
    if not cmd:
        return []
    args = list(server.get("args") or [])
    env = {**os.environ, **(server.get("env") or {})}
    params = StdioServerParameters(command=str(cmd), args=args, env=env)
    names: list[str] = []
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                for t in getattr(listed, "tools", None) or []:
                    n = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
                    if n:
                        names.append(str(n))
    except Exception as exc:
        logger.debug("MCP list_tools failed for %s: %s", server.get("name"), exc)
    return names
