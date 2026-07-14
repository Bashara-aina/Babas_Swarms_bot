"""
core/mcp/router.py — Unified MCP tool registry and dispatcher

Responsibilities:
1. Aggregate tool definitions from all running MCP servers
2. Build a unified TOOL_DEFINITIONS list for the agent's LLM
3. Route incoming tool calls to the correct MCP server
4. Provide async tool execution with proper error handling

All 17 MCP servers are supported:
  ruflo (200+ tools), hermes, crawl4ai, browser-use,
  sequential-thinking, exa, local-deep-research,
  gitnexus, obsidian, filesystem, brave, github, supabase,
  browser, graphify

Usage:
  from core.mcp.router import get_mcp_router, MCP_ROUTER

  # Get tool definitions for LLM
  tools = await MCP_ROUTER.get_tool_definitions()

  # Execute a tool call
  result = await MCP_ROUTER.execute_tool("ruflo_memory_search", {"query": "..."})

  # Route a task to optimal MCP tool
  result = await MCP_ROUTER.route_task("search memory for project context", task_type="memory")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Tool name prefixes for each MCP server ───────────────────────────────────
TOOL_PREFIXES: dict[str, str] = {
    "ruflo": "ruflo_",
    "hermes": "hermes_",
    "crawl4ai": "crawl4ai_",
    "browser_use": "browser_use_",
    "sequential_thinking": "sequential_thinking_",
    "exa": "exa_",
    "local_deep_research": "local_deep_research_",
    "gitnexus": "gitnexus_",
    "obsidian": "obsidian_",
    "filesystem": "filesystem_",
    "brave": "brave_",
    "github": "github_",
    "supabase": "supabase_",
    "browser": "browser_",
    "graphify": "graphify_",
    "scrapling": "scrapling_",
    "jina_reader": "jina_",
    "firecrawl": "firecrawl_",
}

# Reverse map: prefix → server name
PREFIX_TO_SERVER: dict[str, str] = {v.rstrip("_"): k for k, v in TOOL_PREFIXES.items()}


# ── Lazy-load: config + env-based enable gate ────────────────────────────────
# Mitigation 2 (token reduction): only start MCP servers that are explicitly
# enabled. Priority: env var (MCP_<NAME>_ENABLED) > config/mcp_config.json > True
# (default for backward compat). Loading the config file once at import time
# avoids per-call I/O.

def _load_mcp_config_enabled() -> dict[str, bool]:
    """Read config/mcp_config.json and return {server_name: enabled_bool}.

    Failures are non-fatal — returns empty dict and we fall back to defaults.
    """
    try:
        config_path = (
            Path(__file__).resolve().parent.parent.parent / "config" / "mcp_config.json"
        )
        if not config_path.exists():
            return {}
        data = json.loads(config_path.read_text(encoding="utf-8"))
        result: dict[str, bool] = {}
        for server in data.get("servers", []):
            name = server.get("name")
            if name:
                # Normalize: "browser-use" (config, hyphen) -> "browser_use" to match
                # TOOL_PREFIXES in core/mcp/servers/* and env-var naming convention.
                # The python router only iterates over TOOL_PREFIXES, so config keys
                # not in TOOL_PREFIXES (e.g. "symphony", "git") are loaded but unused.
                normalized = name.lower().replace("-", "_")
                result[normalized] = bool(server.get("enabled", True))
        return result
    except Exception as exc:
        logger.warning("mcp_config.json read failed: %s — falling back to defaults", exc)
        return {}


_MCP_CONFIG_ENABLED: dict[str, bool] = _load_mcp_config_enabled()


def _is_mcp_enabled(name: str) -> bool:
    """Check whether an MCP server is enabled.

    Precedence:
      1. Env var ``MCP_<NAME>_ENABLED`` (if set: ``"1"``/``"0"``).
      2. ``config/mcp_config.json`` ``enabled`` flag (loaded at import).
      3. Default: ``True`` (backward compatibility).
    """
    # Normalize to canonical form (lowercase + underscores) so env-var name
    # and dict lookup match what _load_mcp_config_enabled stored.
    canonical = name.lower().replace("-", "_")
    env_val = os.getenv(f"MCP_{canonical.upper()}_ENABLED")
    if env_val is not None:
        return env_val == "1"
    if canonical in _MCP_CONFIG_ENABLED:
        return _MCP_CONFIG_ENABLED[canonical]
    return True


class MCPRouter:
    """Unified dispatcher for all MCP servers and tools."""

    def __init__(self) -> None:
        self._clients: dict[str, Any] = {}  # server_name → MCPClient
        self._tool_definitions: list[dict] = []  # aggregated tool schemas
        self._tool_to_server: dict[str, str] = {}  # tool_name → server_name
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all MCP server connections and aggregate tool definitions."""
        if self._initialized:
            return

        logger.info("MCP Router: initializing all server connections...")

        # Import server configs
        from core.mcp.servers import (
            brave,
            browser,
            browser_use,
            crawl4ai,
            exa,
            filesystem,
            firecrawl,
            github,
            gitnexus,
            graphify,
            hermes,
            jina_reader,
            local_deep_research,
            obsidian,
            ruflo,
            scrapling,
            searxng,
            sequential_thinking,
            supabase,
        )

        server_configs = {
            "ruflo": ruflo,
            "hermes": hermes,
            "crawl4ai": crawl4ai,
            "browser_use": browser_use,
            "sequential_thinking": sequential_thinking,
            "exa": exa,
            "local_deep_research": local_deep_research,
            "firecrawl": firecrawl,
            "gitnexus": gitnexus,
            "obsidian": obsidian,
            "filesystem": filesystem,
            "brave": brave,
            "github": github,
            "supabase": supabase,
            "browser": browser,
            "graphify": graphify,
            "scrapling": scrapling,
            "jina_reader": jina_reader,
            "searxng": searxng,
        }

        for name, config in server_configs.items():
            try:
                if not _is_mcp_enabled(name):
                    logger.info("MCP %s: skipped (disabled via env or config)", name)
                    continue

                if not config.is_available():
                    logger.debug("MCP %s: not available (is_available=False)", name)
                    continue

                from core.mcp.client import MCPClient

                async def init_server() -> tuple[MCPClient, list[dict]]:
                    """Initialize one server with its tools."""
                    client = MCPClient(config.command())
                    await client.start()
                    tools = await client.list_tools()
                    return client, tools

                # Per-server timeout: 20s max (local_deep_research can hang)
                client, tools = await asyncio.wait_for(init_server(), timeout=20.0)
                self._clients[name] = client

                # Build tool definition mapping
                prefix = TOOL_PREFIXES.get(name, f"{name}_")
                for tool in tools:
                    if isinstance(tool, dict):
                        tool_name = tool.get("name", "")
                        if tool_name:
                            # Prefix the tool name to avoid collisions
                            prefixed_name = f"{prefix}{tool_name}"
                            self._tool_to_server[prefixed_name] = name
                            # Store original tool schema with prefixed name
                            prefixed_tool = dict(tool)
                            prefixed_tool["name"] = prefixed_name
                            self._tool_definitions.append(prefixed_tool)
                    else:
                        # Tool object with name attribute
                        tool_name = getattr(tool, "name", "")
                        if tool_name:
                            prefixed_name = f"{prefix}{tool_name}"
                            self._tool_to_server[prefixed_name] = name

                logger.info("MCP %s: %d tools registered (prefix=%s)", name, len(tools), prefix)
            except Exception as e:
                logger.warning("MCP %s failed to initialize: %s", name, e)
                continue

        self._initialized = True
        logger.info(
            "MCP Router: %d servers connected, %d tools total",
            len(self._clients),
            len(self._tool_definitions)
        )

    async def get_tool_definitions(self) -> list[dict]:
        """Return all aggregated MCP tool definitions for the LLM's tool registry."""
        if not self._initialized:
            await self.initialize()
        return self._tool_definitions

    def get_tool_count(self) -> int:
        """Return total number of registered MCP tools."""
        return len(self._tool_definitions)

    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        """Execute a tool call by routing to the appropriate MCP server.

        Args:
            tool_name: Prefixed tool name (e.g., "ruflo_memory_search")
            args: Tool arguments

        Returns:
            Tool result as JSON string, or error message
        """
        if not self._initialized:
            await self.initialize()

        # Find which server owns this tool
        server_name = self._tool_to_server.get(tool_name)
        if not server_name:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        client = self._clients.get(server_name)
        if not client:
            return json.dumps({"error": f"MCP server {server_name} not connected"})

        try:
            # Strip prefix to get original tool name
            prefix = TOOL_PREFIXES.get(server_name, "")
            if prefix and tool_name.startswith(prefix):
                original_name = tool_name[len(prefix):]
            else:
                original_name = tool_name

            result = await client.call(original_name, args)
            return json.dumps(result) if result is not None else '{"success": true}'
        except Exception as e:
            logger.error("MCP tool %s failed: %s", tool_name, e)
            return json.dumps({"error": str(e)})

    async def list_servers(self) -> list[dict[str, Any]]:
        """Return status of all MCP servers."""
        return [
            {"name": name, "connected": client is not None, "tool_count": sum(1 for t, s in self._tool_to_server.items() if s == name)}
            for name, client in self._clients.items()
        ]

    async def route_task(self, task: str, task_type: str | None = None) -> str:
        """Route a task to the optimal MCP tool(s) based on task type.

        This is a convenience method that maps task descriptions to
        the best available MCP tool. For precise tool use, call
        execute_tool directly with the appropriate tool name.

        Args:
            task: Task description
            task_type: Optional hint (memory, browser, research, code, files)

        Returns:
            Task result from the routed MCP tool
        """
        if not self._initialized:
            await self.initialize()

        task_lower = task.lower()

        # ── Memory / knowledge tasks → ruflo ─────────────────────────────────
        if task_type == "memory" or any(k in task_lower for k in ["remember", "search memory", "past session", "what did we", "memory search"]):
            return await self.execute_tool("ruflo_memory_search", {"query": task})

        # ── Browser automation → browser_use ───────────────────────────────
        if task_type == "browser" or any(k in task_lower for k in ["browse", "open url", "click", "fill form", "screenshot", "scrape"]):
            return await self.execute_tool("browser_use_browser_run_task", {"task": task, "max_steps": 20})

        # ── Web research / crawling → crawl4ai ────────────────────────────
        if task_type == "research" or any(k in task_lower for k in ["crawl", "scrape", "extract from url", "web research"]):
            return await self.execute_tool("crawl4ai_crawl4ai_crawl", {"url": task})

        # ── Sequential reasoning → sequential_thinking ─────────────────────
        if task_type == "reasoning" or any(k in task_lower for k in ["think step", "reasoning", "analyze this", "break down"]):
            return await self.execute_tool("sequential_thinking_think", {"thought": task})

        # ── Code intelligence → gitnexus ───────────────────────────────────
        if task_type == "code" or any(k in task_lower for k in ["code context", "what calls", "impact analysis", "execution flow"]):
            return await self.execute_tool("gitnexus_query", {"query": task})

        # ── File operations → filesystem ───────────────────────────────────
        if task_type == "files" or any(k in task_lower for k in ["read file", "write file", "list directory", "search files"]):
            return await self.execute_tool("filesystem_read_file", {"path": task})

        # Default: return routing info
        return json.dumps({
            "routed": False,
            "task": task,
            "available_servers": list(self._clients.keys()),
            "hint": "Use execute_tool directly with a specific tool name. Available: " + ", ".join(self._tool_to_server.keys())
        })


# ── Global singleton ───────────────────────────────────────────────────────────
_MCP_ROUTER: MCPRouter | None = None


def get_mcp_router() -> MCPRouter:
    """Get the global MCP router singleton."""
    global _MCP_ROUTER
    if _MCP_ROUTER is None:
        _MCP_ROUTER = MCPRouter()
    return _MCP_ROUTER


# Convenient alias
MCP_ROUTER = get_mcp_router()


# ── Tool definition aggregation for llm_client/__init__.py ────────────────────
async def get_all_mcp_tools() -> list[dict]:
    """Return all MCP tool definitions aggregated from all servers."""
    router = get_mcp_router()
    return await router.get_tool_definitions()


def get_mcp_tool_count() -> int:
    """Return count of all registered MCP tools."""
    router = get_mcp_router()
    return router.get_tool_count()
