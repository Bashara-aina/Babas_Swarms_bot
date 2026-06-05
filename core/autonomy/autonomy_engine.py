"""Autonomy Engine — main orchestration for the Ruflo Autonomy Layer.

Ties together:
  - boot_sequence    (Part II)
  - task_classifier (Part III)
  - mode_executors  (Part IV + V)
  - context_enricher (Part VII)
  - security_layer  (Part VIII)
  - memory_router   (Part VI)
  - session_teardown (Part X)

Plus: Part IX observability, Part XI communication rules, Part XII self-healing.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from core.autonomy.boot_sequence import BootResult, run_boot_sequence
from core.autonomy.context_enricher import enrich_context
from core.autonomy.memory_router import (
    route_direct_task,
    route_lite_task,
    route_swarm_task,
)
from core.autonomy.mode_executors import (
    execute_direct,
    execute_lite,
    execute_swarm,
)
from core.autonomy.security_layer import (
    detect_secrets_in_pasted_code,
    pre_api_endpoint_scan,
    pre_git_commit_scan,
    pre_pii_data_scan,
)
from core.autonomy.session_teardown import (
    check_git_status,
    detect_goodbye,
    run_teardown_sequence,
)
from core.autonomy.task_classifier import Classification, ExecutionMode, classify_task

logger = logging.getLogger(__name__)

_autonomy_engine: AutonomyEngine | None = None


def get_autonomy_engine() -> AutonomyEngine:
    global _autonomy_engine
    if _autonomy_engine is None:
        _autonomy_engine = AutonomyEngine()
    return _autonomy_engine


# ---------------------------------------------------------------------------
# Part XI — Communication Rules
# ---------------------------------------------------------------------------

def format_user_output(result: Any, mode: ExecutionMode) -> str:
    """Format output for user per Part XI communication rules.

    NEVER show: agent names, swarm IDs, ruflo tool calls, memory confirmations.
    ALWAYS show: actual work output, blocking errors, progress on long tasks.
    """
    if hasattr(result, "error") and result.error:
        return f"Error: {result.error}"
    if hasattr(result, "output") and result.output:
        return result.output[:2000]
    if hasattr(result, "success") and result.success:
        return "Done."
    return "Completed."


# ---------------------------------------------------------------------------
# Part XII — Self-Healing
# ---------------------------------------------------------------------------

class AutonomyError(Exception):
    pass


async def self_heal(failure_type: str, context: dict) -> dict:
    """Attempt self-healing based on failure type."""
    recovery_map = {
        "ruflo_unhealthy": lambda ctx: _restart_ruflo(),
        "agent_spawn_failed": lambda ctx: _respawn_agent(ctx),
        "session_restore_empty": lambda ctx: {"action": "proceed_fresh"},
        "memory_search_empty": lambda ctx: {"action": "proceed_without_memory"},
        "swarm_stall": lambda ctx: _unstall_swarm(ctx),
        "ruflo_crash": lambda ctx: _restart_ruflo(),
    }

    handler = recovery_map.get(failure_type)
    if handler:
        return await handler(context)
    return {"action": "degrade_to_direct"}


async def _restart_ruflo() -> dict:
    """Restart ruflo MCP server."""
    try:
        import subprocess
        import sys
        proc = subprocess.Popen(
            [sys.executable, "-m", "mcp_servers.ruflo_mcp_server", "--transport", "stdio"],
            cwd="/home/newadmin/swarm-bot",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await asyncio.sleep(3)
        return {"action": "ruflo_restarted", "pid": proc.pid}
    except Exception as e:
        return {"action": "ruflo_restart_failed", "error": str(e)}


async def _respawn_agent(context: dict) -> dict:
    """Re-spawn a failed agent with more conservative instructions."""
    from core.mcp_client import MCPClient
    try:
        client = MCPClient()
        result = await client.call_tool("ruflo", "agent_spawn", {
            "agentType": context.get("agentType", "coder"),
            "task": context.get("task", "") + " (be more conservative, previous attempt failed)",
            "model": "minimax-coding-plan/MiniMax-M3",
        })
        return {"action": "agent_respawned", "result": result}
    except Exception as e:
        return {"action": "agent_respawn_failed", "error": str(e)}


async def _unstall_swarm(context: dict) -> dict:
    """Kill stuck agents and re-spawn the stalled role."""
    from core.mcp_client import MCPClient
    try:
        client = MCPClient()
        agents_raw = await client.call_tool("ruflo", "agent_list", {})
        # call_tool returns str, parse JSON (may be truncated — handle gracefully)
        agents = []
        if isinstance(agents_raw, str) and agents_raw.startswith("{"):
            import json
            try:
                agents_data = json.loads(agents_raw)
                agents = agents_data.get("agents", []) if isinstance(agents_data, dict) else []
            except json.JSONDecodeError:
                # Truncated JSON — extract agentIds via regex
                import re
                agent_ids = re.findall(r'"agentId":\s*"([^"]+)"', agents_raw)
                agents = [{"agentId": aid, "status": "active"} for aid in agent_ids]
        stuck = [a["agentId"] for a in agents if isinstance(a, dict) and a.get("status") == "active"]
        for name in stuck:
            await client.call_tool("ruflo", "agent_stop", {"agentId": name})
        return {"action": "swarm_reset", "stopped_agents": len(stuck)}
    except Exception as e:
        return {"action": "swarm_reset_failed", "error": str(e)}


# ---------------------------------------------------------------------------
# Main Engine
# ---------------------------------------------------------------------------

class AutonomyEngine:
    """Main orchestration engine for the Autonomy Layer.

    Call `process_message()` on every user message.
    Call `shutdown()` on session end.
    """

    def __init__(self):
        self._booted: bool = False
        self._boot_result: BootResult | None = None
        self._last_classification: Classification | None = None
        self._task_count: int = 0
        self._session_start: float = time.time()
        self._degraded: bool = False
        self._pending_long_task: str | None = None

    # -------------------------------------------------------------------------
    # Boot (Part II)
    # -------------------------------------------------------------------------

    async def boot(self) -> BootResult:
        """Run boot sequence. Idempotent — safe to call multiple times."""
        if self._booted:
            return self._boot_result or BootResult(healthy=True)

        logger.info("Running Ruflo Autonomy Layer boot sequence...")
        self._boot_result = await run_boot_sequence()
        self._booted = True

        if not self._boot_result.healthy:
            logger.warning("Ruflo boot failed — running in degraded mode")
            self._degraded = True
        else:
            logger.info(
                "Ruflo Autonomy Layer booted: workers=%d, hooks=%d",
                self._boot_result.workers_dispatched,
                self._boot_result.hooks_registered,
            )

        return self._boot_result

    # -------------------------------------------------------------------------
    # Message processing entry point
    # -------------------------------------------------------------------------

    async def process_message(
        self,
        user_message: str,
        work_fn: Callable[..., Awaitable[Any]] | None = None,
        mcp_calls: list[tuple[str, dict]] | None = None,
        git_staged_files: list[str] | None = None,
        api_endpoint_schema: str | None = None,
        code_with_pii: str | None = None,
        pasted_code: str | None = None,
    ) -> str:
        """Process a user message through the full Autonomy Layer pipeline.

        This is the main entry point. Call it for every user message.

        Args:
            user_message: The raw user input
            work_fn: Async function that does the actual work (called in appropriate mode)
            mcp_calls: Alternative to work_fn — list of (tool, args) to execute
            git_staged_files: If provided, run pre-git-commit security scan
            api_endpoint_schema: If provided, run pre-API security scan
            code_with_pii: If provided, run PII scan
            pasted_code: If provided, check for hardcoded secrets

        Returns:
            User-facing output string (per Part XI communication rules)
        """
        # Check for goodbye / session end signals
        if detect_goodbye(user_message):
            return await self._handle_session_end()

        # Run security pre-checks (Part VIII) — invisible, always on
        security_error = await self._run_security_checks(
            git_staged_files=git_staged_files,
            api_schema=api_endpoint_schema,
            code_pii=code_with_pii,
            pasted_code=pasted_code,
        )
        if security_error:
            return f"Security: {security_error}"

        # Classify the task (Part III) — < 100ms
        classification = await classify_task(user_message)
        self._last_classification = classification

        # Context enrichment (Part VII) — runs in parallel, < 5s
        enrich_task = asyncio.create_task(enrich_context(user_message))

        # Execute based on mode (Part IV)
        result = await self._execute_by_mode(classification, user_message, work_fn, mcp_calls)

        # Memory routing (Part VI) — after execution
        await self._route_memory(classification, user_message, result, mcp_calls)

        # Observability (Part IX) — benchmark on swarm tasks
        if classification.mode == ExecutionMode.SWARM:
            await self._record_swarm_metrics(result)

        self._task_count += 1

        # Wait for enrichment to finish (don't block response)
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(enrich_task, timeout=1.0)

        return format_user_output(result, classification.mode)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _run_security_checks(
        self,
        git_staged_files: list[str] | None = None,
        api_schema: str | None = None,
        code_pii: str | None = None,
        pasted_code: str | None = None,
    ) -> str | None:
        """Run security pre-checks. Returns error message if blocked."""
        if git_staged_files:
            clean, err = await pre_git_commit_scan(git_staged_files)
            if not clean:
                return err

        if api_schema:
            clean, err = await pre_api_endpoint_scan(api_schema)
            if not clean:
                return err

        if code_pii:
            clean, err = await pre_pii_data_scan(code_pii)
            if not clean:
                return err

        if pasted_code:
            has_secrets, err = await detect_secrets_in_pasted_code(pasted_code)
            if has_secrets:
                return err

        return None

    async def _execute_by_mode(
        self,
        classification: Classification,
        user_message: str,
        work_fn: Callable[..., Awaitable[Any]] | None,
        mcp_calls: list[tuple[str, dict]] | None,
    ):
        """Route to appropriate executor based on classification."""
        mode = classification.mode

        if mode == ExecutionMode.DIRECT:
            if work_fn:
                await work_fn()
                from core.autonomy.mode_executors import ExecutionResult
                return ExecutionResult(success=True, mode="direct", output="Done.")
            if mcp_calls:
                tool, args = mcp_calls[0]
                return await execute_direct(user_message, tool, args)
            return await execute_direct(user_message, "filesystem", {"operation": "noop"})

        if mode == ExecutionMode.LITE:
            if work_fn:
                await work_fn()
                from core.autonomy.mode_executors import ExecutionResult
                return ExecutionResult(success=True, mode="lite", output="Done.")
            calls = mcp_calls or [("filesystem", {"operation": "noop"})]
            return await execute_lite(user_message, classification.reason, calls)

        # SWARM
        if work_fn:
            # SWARM mode: run work_fn, then execute swarm orchestration
            await work_fn()
        calls = mcp_calls or []
        return await execute_swarm(user_message, classification.reason, calls)

    async def _route_memory(
        self,
        classification: Classification,
        task: str,
        result: Any,
        mcp_calls: list[tuple[str, dict]] | None,
    ):
        """Route memory based on execution mode (Part VI)."""
        mode = classification.mode
        files = [str(a[1].get("path", "")) for a in (mcp_calls or []) if isinstance(a[1], dict)]

        if mode == ExecutionMode.DIRECT:
            tool = mcp_calls[0][0] if mcp_calls else "unknown"
            success = getattr(result, "success", False)
            await route_direct_task(task, tool, "success" if success else "failed")
        elif mode == ExecutionMode.LITE:
            await route_lite_task(task, classification.reason, files)
        else:
            decisions = [f"mode={mode.value}", f"neural_conf={classification.neural_confidence:.2f}"]
            await route_swarm_task(task, classification.reason, decisions, len(files), ["general"])

    async def _record_swarm_metrics(self, result: Any):
        """Record swarm performance metrics (Part IX)."""
        try:
            from core.mcp_client import MCPClient
            client = MCPClient()
            swarm_id = getattr(result, "swarm_id", "unknown")
            await client.call_tool("ruflo", "performance_profile", {"target": swarm_id})
            await client.call_tool("ruflo", "benchmark_run", {
                "scope": "session",
                "metrics": ["token_usage", "latency", "task_count"],
            })
        except Exception as e:
            logger.debug("observability record failed: %s", e)

    async def _handle_session_end(self) -> str:
        """Run teardown sequence and return one-line announcement."""
        # Check for uncommitted changes
        has_changes, uncommitted = await check_git_status()

        announcement = await run_teardown_sequence(
            session_summary=f"Completed {self._task_count} tasks",
            task_count=self._task_count,
            detected_projects=["swarm-bot"],
            has_code_changes=has_changes,
            uncommitted_files=uncommitted if has_changes else None,
        )
        return announcement

    # -------------------------------------------------------------------------
    # Session end (Part X)
    # -------------------------------------------------------------------------

    async def shutdown(self) -> str:
        """Full session shutdown. Call on OpenCode close or goodbye signal."""
        return await self._handle_session_end()

    # -------------------------------------------------------------------------
    # Properties for observability
    # -------------------------------------------------------------------------

    @property
    def is_healthy(self) -> bool:
        return self._boot_result.healthy if self._boot_result else False

    @property
    def is_degraded(self) -> bool:
        return self._degraded

    @property
    def task_count(self) -> int:
        return self._task_count

    @property
    def last_classification(self) -> Classification | None:
        return self._last_classification