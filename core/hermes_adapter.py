"""
Hermes Agent Integration for LegionBot

Provides a clean Python wrapper around Hermes Agent's AIAgent class,
enabling Hermes's tool registry, session management, delegate system,
and multi-platform capabilities within the swarm-bot framework.

Key features:
- Hermes AIAgent wrapped with async interface for aiogram handlers
- Hermes SessionDB (SQLite/FTS5) for cross-session memory
- Hermes tool registry bridged to swarm-bot tools
- Delegate tool for spawning subagents with isolated context
- Skills system for procedural memory

Architecture:
    handlers/hermes.py  →  core/hermes_adapter.py  →  hermes-agent/
                                              ↓
                                    hermes/run_agent.py (AIAgent)
                                              ↓
                                    hermes/model_tools.py (tools)
                                              ↓
                                    hermes/tools/registry.py (registry)
                                              ↓
                                    hermes/hermes_state.py (SessionDB)

Author: Bashara | Legion v10
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Path Setup — add hermes-agent to sys.path at runtime
# ─────────────────────────────────────────────────────────────────────────────

HERMES_REPO_PATH = os.environ.get(
    "HERMES_REPO_PATH",
    str(Path.home() / "hermes-agent"),
)

if HERMES_REPO_PATH not in sys.path:
    sys.path.insert(0, HERMES_REPO_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# Async Bridge — run Hermes's sync AIAgent in a thread pool
# ─────────────────────────────────────────────────────────────────────────────

class _HermesAsyncBridge:
    """Thread-safe async bridge for the synchronous AIAgent.

    Hermes's AIAgent is entirely synchronous (no async/await), but
    swarm-bot is fully async (aiogram). This bridge runs the agent
    in a ThreadPoolExecutor so it never blocks the event loop.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="hermes-")
        self._lock = threading.Lock()

    async def run_chat(
        self,
        agent,  # AIAgent instance
        message: str,
        session_id: str | None = None,
    ) -> str:
        """Run a single chat turn in the thread pool. Returns final response."""
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                self._executor,
                lambda: agent.chat(message),
            )
            return result
        except Exception as e:
            logger.error("Hermes chat error: %s", e)
            return f"[Hermes Error: {e}]"

    async def run_conversation(
        self,
        agent,  # AIAgent instance
        user_message: str,
        system_message: str | None = None,
        conversation_history: list[dict] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Run a full conversation turn. Returns dict with final_response + metadata."""
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                self._executor,
                lambda: agent.run_conversation(
                    user_message=user_message,
                    system_message=system_message,
                    conversation_history=conversation_history or [],
                    task_id=session_id,
                ),
            )
            return result
        except Exception as e:
            logger.error("Hermes conversation error: %s", e)
            return {"error": str(e), "final_response": f"[Hermes Error: {e}]"}

    def shutdown(self):
        """Shutdown the thread pool gracefully."""
        self._executor.shutdown(wait=True)


# Global bridge instance
_hermes_bridge: _HermesAsyncBridge | None = None


def get_hermes_bridge() -> _HermesAsyncBridge:
    """Get or create the global Hermes async bridge."""
    global _hermes_bridge
    if _hermes_bridge is None:
        _hermes_bridge = _HermesAsyncBridge()
    return _hermes_bridge


# ─────────────────────────────────────────────────────────────────────────────
# Hermes Session Manager — SQLite/FTS5 backed session store
# ─────────────────────────────────────────────────────────────────────────────

class HermesSessionManager:
    """Manages Hermes sessions using SessionDB (SQLite + FTS5).

    Provides:
    - create_session / get_session / end_session lifecycle
    - append_message for full conversation history
    - FTS5 search across all sessions (session_search tool)
    - Session lineage (parent_session_id chains)
    - Token tracking and cost estimation

    Thread-safe for concurrent reads/writes (WAL mode).
    """

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path
        self._db: Any = None
        self._lock = threading.Lock()

    def _get_db(self) -> Any:
        """Lazy-load SessionDB to avoid import-time circular deps."""
        if self._db is None:
            from hermes_state import (  # type: ignore[reportMissingImports]
                SessionDB,  # type: ignore[reportMissingImports]  # type: ignore[reportMissingImports]
            )

            self._db = SessionDB(db_path=self._db_path)
        return self._db

    async def create_session(
        self,
        session_id: str,
        source: str = "legion",
        model: str | None = None,
        system_prompt: str | None = None,
        user_id: str | None = None,
        parent_session_id: str | None = None,
    ) -> str:
        """Create a new session. Returns session_id."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        await loop.run_in_executor(
            None,
            lambda: db.create_session(
                session_id=session_id,
                source=source,
                model=model,
                system_prompt=system_prompt,
                user_id=user_id,
                parent_session_id=parent_session_id,
            ),
        )
        return session_id

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str | None = None,
        tool_name: str | None = None,
        tool_calls: Any = None,
        tool_call_id: str | None = None,
        token_count: int | None = None,
        finish_reason: str | None = None,
    ) -> int:
        """Append a message to a session. Returns message row ID."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        msg_id = await loop.run_in_executor(
            None,
            lambda: db.append_message(
                session_id=session_id,
                role=role,
                content=content,
                tool_name=tool_name,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
                token_count=token_count,
                finish_reason=finish_reason,
            ),
        )
        return msg_id

    async def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Load all messages for a session."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        messages = await loop.run_in_executor(
            None,
            lambda: db.get_messages(session_id),
        )
        return messages

    async def get_messages_as_conversation(
        self, session_id: str
    ) -> list[dict[str, Any]]:
        """Load messages in OpenAI conversation format."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        messages = await loop.run_in_executor(
            None,
            lambda: db.get_messages_as_conversation(session_id),
        )
        return messages

    async def search_messages(
        self,
        query: str,
        source_filter: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """FTS5 full-text search across session messages."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        results = await loop.run_in_executor(
            None,
            lambda: db.search_messages(
                query=query,
                source_filter=source_filter,
                limit=limit,
            ),
        )
        return results

    async def end_session(self, session_id: str, end_reason: str = "completed") -> None:
        """Mark a session as ended."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        await loop.run_in_executor(
            None,
            lambda: db.end_session(session_id, end_reason),
        )

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session metadata by ID."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        session = await loop.run_in_executor(
            None,
            lambda: db.get_session(session_id),
        )
        return session

    async def list_sessions(
        self,
        source: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List sessions with preview."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        sessions = await loop.run_in_executor(
            None,
            lambda: db.list_sessions_rich(source=source, limit=limit, offset=offset),
        )
        return sessions

    async def update_token_counts(
        self,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        reasoning_tokens: int = 0,
        estimated_cost_usd: float | None = None,
    ) -> None:
        """Update token counters for a session."""
        loop = asyncio.get_running_loop()
        db = self._get_db()
        await loop.run_in_executor(
            None,
            lambda: db.update_token_counts(
                session_id=session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_write_tokens=cache_write_tokens,
                reasoning_tokens=reasoning_tokens,
                estimated_cost_usd=estimated_cost_usd,
            ),
        )


# Global session manager
_hermes_session_manager: HermesSessionManager | None = None


def get_hermes_session_manager() -> HermesSessionManager:
    """Get or create the global Hermes session manager."""
    global _hermes_session_manager
    if _hermes_session_manager is None:
        db_path = Path(HERMES_REPO_PATH) / "state.db"
        _hermes_session_manager = HermesSessionManager(db_path=db_path)
    return _hermes_session_manager


# ─────────────────────────────────────────────────────────────────────────────
# Hermes AIAgent Factory — creates configured AIAgent instances
# ─────────────────────────────────────────────────────────────────────────────

# Default model for Hermes agent in LegionBot
DEFAULT_HERMES_MODEL = os.environ.get(
    "HERMES_DEFAULT_MODEL",
    "minimax-coding-plan/MiniMax-M2.7",
)


def create_hermes_agent(
    model: str | None = None,
    enabled_toolsets: list[str] | None = None,
    disabled_toolsets: list[str] | None = None,
    session_id: str | None = None,
    platform: str = "legion",
    user_id: str | None = None,
    max_iterations: int = 90,
    quiet_mode: bool = False,
    skip_context_files: bool = False,
    skip_memory: bool = False,
    save_trajectories: bool = False,
    verbose_logging: bool = False,
    base_url: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
) -> Any:
    """Factory to create a configured Hermes AIAgent instance.

    Args:
        model: Provider/model string (e.g. "minimax-coding-plan/MiniMax-M2.7")
        enabled_toolsets: Toolset names to enable (e.g. ["terminal", "file", "web"])
        disabled_toolsets: Toolset names to disable
        session_id: Pre-generated session ID for logging
        platform: Platform identifier ("legion", "telegram", etc.)
        user_id: Platform user identifier
        max_iterations: Max tool-calling iterations (default 90)
        quiet_mode: Suppress progress output
        skip_context_files: Skip SOUL.md, AGENTS.md injection
        skip_memory: Skip memory layer
        save_trajectories: Save trajectories to JSONL
        verbose_logging: Enable verbose debug logging
        base_url: Override API base URL
        api_key: Override API key
        provider: Provider name hint

    Returns:
        AIAgent instance (synchronous — use with HermesAsyncBridge for async)
    """
    from run_agent import AIAgent  # type: ignore[reportMissingImports]

    return AIAgent(
        model=model or DEFAULT_HERMES_MODEL,
        max_iterations=max_iterations,
        enabled_toolsets=enabled_toolsets or ["terminal", "file", "web", "browser"],
        disabled_toolsets=disabled_toolsets,
        session_id=session_id,
        platform=platform,
        user_id=user_id,
        quiet_mode=quiet_mode,
        skip_context_files=skip_context_files,
        skip_memory=skip_memory,
        save_trajectories=save_trajectories,
        verbose_logging=verbose_logging,
        base_url=base_url or os.environ.get("OPENROUTER_BASE_URL", "https://api.minimax.io/anthropic"),
        api_key=api_key or os.environ.get("MINIMAX_API_KEY"),
        provider=provider,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hermes Tool Registry Bridge — expose Hermes tools to swarm-bot handlers
# ─────────────────────────────────────────────────────────────────────────────

def get_hermes_tool_definitions(
    enabled_toolsets: list[str] | None = None,
    disabled_toolsets: list[str] | None = None,
    quiet_mode: bool = True,
) -> list[dict[str, Any]]:
    """Get Hermes tool schemas for OpenAI-format tool definitions.

    Use this to pass Hermes tools to any LLM client that accepts
    OpenAI-style function calling schemas.

    Args:
        enabled_toolsets: Only include tools from these toolsets
        disabled_toolsets: Exclude tools from these toolsets
        quiet_mode: Suppress status prints

    Returns:
        List of OpenAI-format tool definitions
    """
    try:
        from model_tools import (  # type: ignore[reportMissingImports]
            get_tool_definitions as hermes_get_tool_definitions,  # type: ignore[reportMissingImports]
        )

        return hermes_get_tool_definitions(
            enabled_toolsets=enabled_toolsets,
            disabled_toolsets=disabled_toolsets,
            quiet_mode=quiet_mode,
        )
    except Exception as e:
        logger.warning("Could not load Hermes tool definitions: %s", e)
        return []


def dispatch_hermes_tool_call(
    function_name: str,
    function_args: dict[str, Any],
    task_id: str | None = None,
    session_id: str | None = None,
    user_task: str | None = None,
) -> str:
    """Dispatch a tool call to Hermes's registry.

    Args:
        function_name: Name of the Hermes tool
        function_args: Tool arguments dict
        task_id: Terminal/browser session ID for isolation
        session_id: Current session ID
        user_task: User's original task (for browser context)

    Returns:
        Tool result as JSON string
    """
    try:
        from model_tools import (  # type: ignore[reportMissingImports]
            handle_function_call as hermes_dispatch,  # type: ignore[reportMissingImports]
        )

        return hermes_dispatch(
            function_name=function_name,
            function_args=function_args,
            task_id=task_id,
            session_id=session_id,
            user_task=user_task,
        )
    except Exception as e:
        logger.error("Hermes tool dispatch error (%s): %s", function_name, e)
        return json.dumps({"error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# Hermes Toolset Definitions for swarm-bot
# ─────────────────────────────────────────────────────────────────────────────

HERMES_LEGION_TOOLSETS = {
    # Core toolsets available to LegionBot via Hermes
    "hermes-terminal": {
        "description": "Terminal command execution and process management via Hermes",
        "tools": ["terminal", "process"],
        "includes": [],
    },
    "hermes-file": {
        "description": "File read/write/patch/search via Hermes",
        "tools": ["read_file", "write_file", "patch", "search_files"],
        "includes": [],
    },
    "hermes-web": {
        "description": "Web search and content extraction via Hermes",
        "tools": ["web_search", "web_extract"],
        "includes": [],
    },
    "hermes-browser": {
        "description": "Browser automation via Hermes (navigate, click, type, scroll)",
        "tools": [
            "browser_navigate", "browser_snapshot", "browser_click",
            "browser_type", "browser_scroll", "browser_back",
            "browser_press", "browser_get_images", "browser_vision", "browser_console",
        ],
        "includes": ["hermes-web"],
    },
    "hermes-vision": {
        "description": "Image analysis via Hermes vision tool",
        "tools": ["vision_analyze"],
        "includes": [],
    },
    "hermes-delegate": {
        "description": "Spawn isolated subagents for parallel work via Hermes delegate tool",
        "tools": ["delegate_task"],
        "includes": ["hermes-terminal", "hermes-file", "hermes-web"],
    },
    "hermes-session": {
        "description": "Search past conversations via Hermes session_search tool",
        "tools": ["session_search"],
        "includes": [],
    },
    "hermes-skills": {
        "description": "Access and manage Hermes skills — procedural memory that self-improves",
        "tools": ["skills_list", "skill_view", "skill_manage"],
        "includes": [],
    },
    "hermes-todo": {
        "description": "Task planning and tracking via Hermes todo tool",
        "tools": ["todo"],
        "includes": [],
    },
    "hermes-full": {
        "description": "Full Hermes tool suite — all tools for trusted local use",
        "tools": [
            "terminal", "process",
            "read_file", "write_file", "patch", "search_files",
            "web_search", "web_extract",
            "browser_navigate", "browser_snapshot", "browser_click",
            "browser_type", "browser_scroll", "browser_back",
            "browser_press", "browser_get_images", "browser_vision", "browser_console",
            "vision_analyze",
            "delegate_task",
            "session_search",
            "skills_list", "skill_view", "skill_manage",
            "todo",
            "execute_code",
        ],
        "includes": [],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Hermes Delegate — spawn subagents with isolated context
# ─────────────────────────────────────────────────────────────────────────────

async def hermes_delegate(
    goal: str,
    context: str | None = None,
    toolsets: list[str] | None = None,
    max_iterations: int = 50,
    session_id: str | None = None,
    workspace_path: str | None = None,
) -> str:
    """Spawn a Hermes subagent for a delegated task.

    Args:
        goal: The task to accomplish
        context: Additional context from the parent
        toolsets: Toolset names for the subagent (default: ["terminal", "file", "web"])
        max_iterations: Max iterations for the subagent (default 50)
        session_id: Parent session ID for logging
        workspace_path: Absolute path for the subagent's working directory

    Returns:
        Subagent's final summary response
    """
    from tools.delegate_tool import _build_child_system_prompt  # type: ignore[reportMissingImports]

    toolsets = toolsets or ["terminal", "file", "web"]

    # Build child system prompt
    system_prompt = _build_child_system_prompt(
        goal=goal,
        context=context,
        workspace_path=workspace_path,
    )

    # Create a focused child agent
    child_agent = create_hermes_agent(
        enabled_toolsets=toolsets,
        max_iterations=max_iterations,
        session_id=session_id,
        platform="legion-delegate",
        skip_context_files=True,  # Isolated — no parent context
    )

    bridge = get_hermes_bridge()

    try:
        result = await bridge.run_conversation(
            agent=child_agent,
            user_message=goal,
            system_message=system_prompt,
            session_id=session_id,
        )
        if isinstance(result, dict):
            return result.get("final_response", str(result))
        return str(result)
    except Exception as e:
        logger.error("Hermes delegate error: %s", e)
        return f"[Delegate Error: {e}]"


# ─────────────────────────────────────────────────────────────────────────────
# Hermes Session Search — FTS5 recall across conversations
# ─────────────────────────────────────────────────────────────────────────────

async def hermes_session_search(
    query: str,
    source_filter: list[str] | None = None,
    limit: int = 5,
    session_id: str | None = None,
) -> str:
    """Search past sessions using Hermes's FTS5 session_search.

    Args:
        query: Natural language search query
        source_filter: Filter by source platform (e.g. ["legion", "telegram"])
        limit: Max sessions to return (default 5)
        session_id: Current session for context

    Returns:
        Formatted search results with session summaries
    """
    mgr = get_hermes_session_manager()

    results = await mgr.search_messages(
        query=query,
        source_filter=source_filter,
        limit=limit,
    )

    if not results:
        return "No matching sessions found."

    output_parts = [f"**Found {len(results)} matching session(s):**\n"]

    for i, result in enumerate(results, 1):
        snippet = result.get("snippet", "")
        session_id_res = result.get("session_id", "unknown")
        source = result.get("source", "unknown")
        model = result.get("model", "unknown")
        session_started = result.get("session_started")

        if session_started:
            try:
                dt = datetime.fromtimestamp(session_started, tz=UTC)
                date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                date_str = "unknown"
        else:
            date_str = "unknown"

        output_parts.append(
            f"**{i}.** [{source}] {date_str} | Model: {model}\n"
            f"   Session: `{session_id_res}`\n"
            f"   {snippet}\n",
        )

    return "\n".join(output_parts)


# ─────────────────────────────────────────────────────────────────────────────
# Quick test / smoke test
# ─────────────────────────────────────────────────────────────────────────────

async def hermes_smoke_test() -> dict[str, Any]:
    """Smoke test — verify Hermes can be imported and tools are accessible."""
    results = {}

    # Test 1: AIAgent import
    try:
        results["AIAgent import"] = "✅ ok"
    except Exception as e:
        results["AIAgent import"] = f"❌ {e}"
        return results

    # Test 2: Tool registry
    try:
        tools = get_hermes_tool_definitions(quiet_mode=True)
        results["tool definitions"] = f"✅ {len(tools)} tools"
    except Exception as e:
        results["tool definitions"] = f"❌ {e}"

    # Test 3: SessionDB import
    try:
        from hermes_state import SessionDB  # type: ignore[reportMissingImports]

        db = SessionDB()
        results["SessionDB"] = "✅ ok"
        db.close()
    except Exception as e:
        results["SessionDB"] = f"❌ {e}"

    # Test 4: Toolset resolution
    try:
        from toolsets import resolve_toolset  # type: ignore[reportMissingImports]

        terminal_tools = resolve_toolset("terminal")
        results["toolset:terminal"] = f"✅ {len(terminal_tools)} tools"
    except Exception as e:
        results["toolset:terminal"] = f"❌ {e}"

    return results
