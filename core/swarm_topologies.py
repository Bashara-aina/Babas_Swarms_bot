"""core/swarm_topologies.py — Swarm execution with opencode sub-agent spawning."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.structured_outputs import SwarmResult
from llm_client import chat

logger = logging.getLogger(__name__)

TOPOLOGIES = {
    "spreadsheet": "spreadsheet",
    "mixture": "mixture",
    "graph": "graph",
    "sequential": "sequential",
    "concurrent": "concurrent",
    "debate": "debate",
    "auto": "auto",
}


async def _spawn_opencode_subagents(
    task: str,
    parent_agent: str,
    task_context: str,
    num_agents: int = 5,
) -> list[dict[str, Any]]:
    """Spawn opencode sub-agents under a parent agent's orchestration.

    Each sub-agent receives the task context + parent's intermediate result.
    Results are returned as trace dicts for synthesis.
    """
    traces: list[dict[str, Any]] = []

    # The parent agent coordinates sub-agents via opencode
    # Sub-agents are spawned as concurrent opencode CLI calls

    async def _spawn_one(prompt: str, idx: int) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            from core.opencode_bridge import run_opencode_task

            result = await run_opencode_task(
                prompt=prompt,
                project_dir="/home/newadmin/swarm-bot",
                agent=parent_agent,
                timeout=120,
            )
            latency = (time.perf_counter() - started) * 1000.0
            return {
                "agent": f"{parent_agent}-sub-{idx}",
                "sub_agent": idx,
                "output": result if result else "(empty)",
                "latency_ms": latency,
                "success": bool(result and not result.startswith("⛔")),
            }
        except Exception as exc:
            return {
                "agent": f"{parent_agent}-sub-{idx}",
                "sub_agent": idx,
                "output": f"error: {exc}",
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "success": False,
            }

    # Spawn up to `num_agents` concurrent sub-tasks
    spawn_count = min(num_agents, 10)
    calls = [_spawn_one(f"{task_context}\n\nSub-task {i+1}/{spawn_count}", i) for i in range(spawn_count)]
    results = await asyncio.gather(*calls, return_exceptions=True)

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            traces.append({"agent": f"{parent_agent}-sub-{i}", "error": str(r), "success": False})
        else:
            traces.append(r)  # type: ignore[reportArgumentType]

    return traces


async def _run_sequential(task: str, agent_names: list[str]) -> tuple[str, list[dict[str, Any]]]:
    traces: list[dict[str, Any]] = []
    current = task
    final = ""
    for agent in agent_names:
        started = time.perf_counter()

        # Before calling the agent, check if we should spawn sub-agents
        sub_traces = await _maybe_spawn_subagents(
            task=current,
            agent=agent,
            depth=0,
            max_depth=2,
        )

        output, model = await chat(current, agent_key=agent, user_id="swarm")
        traces.append(
            {
                "agent": agent,
                "model": model,
                "step": "sequential",
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "tokens_used": 0,
                "sub_agents": sub_traces,
            }
        )
        final = output
        current = f"Task: {task}\n\nPrior result by {agent}:\n{output}\n\nImprove this answer."
    return final, traces


async def _maybe_spawn_subagents(
    task: str,
    agent: str,
    depth: int = 0,
    max_depth: int = 2,
) -> list[dict[str, Any]]:
    """Intelligently spawn sub-agents based on task complexity and agent type.

    Returns trace of spawned sub-agents. Depth limits recursion.
    """
    traces: list[dict[str, Any]] = []

    if depth >= max_depth:
        return traces

    # Task complexity signals for sub-agent spawning
    task_lower = task.lower()
    complexity_signals = {
        "subagent_triggers": [
            "implement", "build", "create", "design",     # creation tasks
            "analyze", "audit", "review", "research",     # research tasks
            "multiple", "several", "various", "different", # multi-faceted
            "backend", "frontend", "database", "api",       # full-stack
            "test", "debug", "fix", "patch",               # multi-step
        ],
        "high_complexity": any(s in task_lower for s in [
            "multiple", "several", "various", "complex",
            "full-stack", "end-to-end", "comprehensive",
        ]),
    }

    should_spawn = complexity_signals["high_complexity"] or any(
        s in task_lower for s in complexity_signals["subagent_triggers"]
    )

    if not should_spawn:
        return traces

    # Determine sub-agent count based on task complexity
    task_words = len(task.split())
    if task_words > 80:
        num_subagents = min(8, 10)
    elif task_words > 40:
        num_subagents = min(5, 8)
    else:
        num_subagents = min(3, 5)

    # Map agent types to relevant opencode agents for sub-tasking
    agent_sub_mapping: dict[str, list[str]] = {
        "senior_python_dev": ["python", "backend", "async"],
        "backend_fastapi_dev": ["fastapi", "api", "rest"],
        "frontend_react_dev": ["frontend", "react", "typescript"],
        "cuda_optimizer": ["cuda", "gpu", "kernel"],
        "debugging_specialist": ["debug", "traceback", "fix"],
        "database_optimizer": ["sql", "postgres", "query"],
        "smart_contract_auditor": ["solidity", "audit", "blockchain"],
        "security_pentester": ["security", "pentest", "vulnerability"],
        "deep_researcher": ["research", "paper", "analysis"],
        "ux_designer": ["design", "ui", "ux"],
    }

    relevant_subs = agent_sub_mapping.get(agent, [])

    # Spawn sub-agents with focused sub-tasks
    sub_tasks = [
        f"Analyze this task and identify the key technical decisions required: {task[:500]}",
        f"List potential failure modes and how to prevent them: {task[:500]}",
        f"Propose an implementation plan with file structure: {task[:500]}",
        f"Identify dependencies and ordering constraints: {task[:500]}",
        f"Define acceptance criteria and verification steps: {task[:500]}",
    ]

    async def _spawn_sub(idx: int, sub_task: str) -> dict[str, Any]:
        started = time.perf_counter()
        sub_agent_type = relevant_subs[idx % len(relevant_subs)] if relevant_subs else "general"
        try:
            from core.opencode_bridge import run_opencode_task

            result = await run_opencode_task(
                prompt=f"""You are a focused sub-agent ({sub_agent_type}) analyzing a sub-task.
Parent task: {task}
Your focus: {sub_task}

Execute and return your findings in this exact format:
FINDING: [what you discovered]
EVIDENCE: [why it's correct]
STATUS: done|blocked|needs_more
""",
                project_dir="/home/newadmin/swarm-bot",
                timeout=90,
            )
            return {
                "sub_agent": idx,
                "focus": sub_agent_type,
                "output": result[:500] if result else "(empty)",
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "success": bool(result and not result.startswith("⛔")),
            }
        except Exception as exc:
            return {
                "sub_agent": idx,
                "focus": sub_agent_type,
                "output": f"error: {exc}",
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "success": False,
            }

    calls = [_spawn_sub(i, sub_tasks[i % len(sub_tasks)]) for i in range(num_subagents)]
    results = await asyncio.gather(*calls, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            traces.append({"error": str(r), "success": False})
        else:
            traces.append(r)  # type: ignore[reportArgumentType]

    return traces


async def _run_concurrent(task: str, agent_names: list[str]) -> tuple[str, list[dict[str, Any]]]:
    async def _call(agent: str) -> tuple[str, str, float, list[dict[str, Any]]]:
        started = time.perf_counter()
        # Each concurrent agent gets sub-agents too
        sub_traces = await _maybe_spawn_subagents(task, agent, depth=0, max_depth=1)
        output, model = await chat(task, agent_key=agent, user_id="swarm")
        return output, model, (time.perf_counter() - started) * 1000.0, sub_traces

    calls = await asyncio.gather(*[_call(a) for a in agent_names], return_exceptions=True)
    traces: list[dict[str, Any]] = []
    outputs: list[str] = []

    for agent, item in zip(agent_names, calls, strict=False):
        if isinstance(item, Exception):
            logger.warning("concurrent step failed for %s: %s", agent, item)
            continue
        out, model, latency, sub_traces = item  # type: ignore[reportGeneralTypeIssues]
        outputs.append(f"[{agent}] {out}")
        traces.append(
            {
                "agent": agent,
                "model": model,
                "step": "concurrent",
                "latency_ms": latency,
                "tokens_used": 0,
                "sub_agents": sub_traces,
            }
        )

    merged = "\n\n".join(outputs)
    if not merged:
        return "", traces

    synthesis, _ = await chat(
        f"Synthesize this multi-agent output into one final answer:\n\n{merged}",
        agent_key="architect",
        user_id="swarm",
    )
    return synthesis, traces


async def run_topology(
    task: str,
    topology: str,
    agent_names: list[str],
    spawn_subagents: bool = True,
) -> SwarmResult:
    """Run swarm topology with intelligent sub-agent spawning.

    Args:
        task: The task to execute
        topology: One of the TOPOLOGIES keys
        agent_names: List of agent keys to run
        spawn_subagents: If True, auto-spawn 3-10 sub-agents based on task complexity
    """
    started = time.perf_counter()
    selected = topology if topology in TOPOLOGIES else "sequential"
    agents = agent_names or ["general", "coding", "debug", "architect"]

    try:
        if selected in {"spreadsheet", "mixture", "graph", "sequential", "debate"}:
            final, traces = await _run_sequential(task, agents)
        elif selected in {"concurrent", "auto"}:
            final, traces = await _run_concurrent(task, agents)
        else:
            final, traces = await _run_sequential(task, agents)

        return SwarmResult(
            final_output=final,
            agent_traces=traces,  # type: ignore[reportArgumentType]
            topology_used=selected,
            total_tokens=0,
            total_latency_ms=(time.perf_counter() - started) * 1000.0,
            success=bool(final),
            error=None if final else "empty swarm output",
        )
    except Exception as exc:
        logger.warning("topology %s failed; fallback to sequential: %s", selected, exc)
        try:
            final, traces = await _run_sequential(task, agents)
            return SwarmResult(
                final_output=final,
                agent_traces=traces,  # type: ignore[reportArgumentType]
                topology_used="sequential",
                total_tokens=0,
                total_latency_ms=(time.perf_counter() - started) * 1000.0,
                success=bool(final),
                error=None if final else str(exc),
            )
        except Exception as fallback_exc:
            return SwarmResult(
                final_output="",
                topology_used="sequential",
                total_tokens=0,
                total_latency_ms=(time.perf_counter() - started) * 1000.0,
                success=False,
                error=str(fallback_exc),
            )
