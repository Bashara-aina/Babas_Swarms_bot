"""orchestrator.py — Parallel multi-agent execution for Legion.

Supports:
  - LLM-powered task decomposition into sub-tasks
  - Parallel execution with concurrency limits
  - Dependency DAG between sub-tasks
  - Result synthesis
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

MAX_PARALLEL = 3
_parallel_sem = asyncio.Semaphore(MAX_PARALLEL)

ProgressCb = Optional[Callable[[str], Coroutine[Any, Any, None]]]


@dataclass
class SubTask:
    description: str
    agent_key: str = "general"
    depends_on: list[int] = field(default_factory=list)
    result: str = ""
    status: str = "pending"  # pending, running, completed, failed


async def parallel_agents(
    task: str,
    sub_tasks: list[SubTask],
    progress_cb: ProgressCb = None,
) -> str:
    """Execute sub-tasks respecting dependency DAG, up to MAX_PARALLEL concurrent.

    Returns synthesized result from all sub-tasks.
    """
    from llm_client import chat

    completed: dict[int, str] = {}
    total = len(sub_tasks)

    while len(completed) < total:
        # Find tasks whose dependencies are all completed
        ready = [
            i for i, s in enumerate(sub_tasks)
            if i not in completed
            and s.status == "pending"
            and all(d in completed for d in s.depends_on)
        ]

        if not ready:
            # Check if stuck (all remaining have unmet dependencies)
            pending = [i for i in range(total) if i not in completed]
            if all(
                any(d not in completed for d in sub_tasks[i].depends_on)
                for i in pending
            ):
                break  # Dependency deadlock
            await asyncio.sleep(0.1)
            continue

        async def _run(idx: int) -> tuple[int, str]:
            async with _parallel_sem:
                step = sub_tasks[idx]
                step.status = "running"

                if progress_cb:
                    await progress_cb(
                        f"[{len(completed)+1}/{total}] {step.agent_key}: {step.description[:50]}…"
                    )

                # Build context from dependencies
                context_parts = []
                for dep_idx in step.depends_on:
                    if dep_idx in completed:
                        dep = sub_tasks[dep_idx]
                        context_parts.append(
                            f"Result from '{dep.description[:40]}': {completed[dep_idx][:300]}"
                        )

                full_task = step.description
                if context_parts:
                    full_task += "\n\nContext from previous steps:\n" + "\n".join(context_parts)

                try:
                    result, _ = await chat(full_task, agent_key=step.agent_key)
                    step.status = "completed"
                    return idx, result
                except Exception as e:
                    step.status = "failed"
                    return idx, f"Failed: {e}"

        # Run ready tasks in parallel (up to MAX_PARALLEL)
        batch = ready[:MAX_PARALLEL]
        results = await asyncio.gather(*[_run(i) for i in batch])

        for idx, result in results:
            completed[idx] = result
            sub_tasks[idx].result = result

    # Synthesize results
    return _synthesize(task, sub_tasks, completed)


def _synthesize(task: str, sub_tasks: list[SubTask], completed: dict[int, str]) -> str:
    """Combine sub-task results into a coherent response."""
    lines = [f"Task: {task}", f"Completed {len(completed)}/{len(sub_tasks)} sub-tasks:", ""]

    for i, st in enumerate(sub_tasks):
        status = "✅" if st.status == "completed" else "❌"
        lines.append(f"{status} [{st.agent_key}] {st.description}")
        if i in completed:
            # Truncate long results
            result = completed[i]
            if len(result) > 500:
                result = result[:500] + "…"
            lines.append(f"   {result}")
        lines.append("")

    return "\n".join(lines)


async def auto_decompose(task: str) -> list[SubTask] | None:
    """Use LLM to decompose a complex task into sub-tasks.

    Returns list of SubTask or None if task is simple enough for single agent.
    """
    from llm_client import chat

    prompt = (
        "You are a task decomposition system. Analyze this task and decide:\n"
        "1. If it's simple enough for a single agent, respond with: SIMPLE\n"
        "2. If it needs multiple steps, respond with a JSON array of sub-tasks.\n\n"
        "Available agent types: coding, debug, math, architect, analyst, general\n\n"
        "JSON format for each sub-task:\n"
        '{"description": "what to do", "agent": "agent_type", "depends_on": [list of 0-indexed step numbers]}\n\n'
        f"Task: {task}\n\n"
        "Respond with ONLY 'SIMPLE' or the JSON array, nothing else."
    )

    try:
        result, _ = await chat(prompt, agent_key="architect")
        result = result.strip()

        if "SIMPLE" in result.upper():
            return None

        # Try to parse JSON
        # Find JSON array in the response
        json_match = result
        if "[" in result:
            start = result.index("[")
            end = result.rindex("]") + 1
            json_match = result[start:end]

        steps = json.loads(json_match)
        sub_tasks = []
        for step in steps:
            sub_tasks.append(SubTask(
                description=step.get("description", ""),
                agent_key=step.get("agent", "general"),
                depends_on=step.get("depends_on", []),
            ))

        if len(sub_tasks) < 2:
            return None

        return sub_tasks

    except Exception as e:
        logger.warning("Task decomposition failed: %s", e)
        return None


async def smart_route(
    task: str,
    progress_cb: ProgressCb = None,
) -> tuple[str, str] | tuple[None, str]:
    """Top-level router: decides single agent vs multi-agent.

    Returns (result, "orchestrator") if multi-agent was used,
    or (None, "") if task should be handled by regular agent_loop/chat.
    """
    sub_tasks = await auto_decompose(task)

    if sub_tasks and len(sub_tasks) >= 2:
        if progress_cb:
            await progress_cb(f"🧠 decomposed into {len(sub_tasks)} sub-tasks")
        result = await parallel_agents(task, sub_tasks, progress_cb)
        return result, "orchestrator"

    return None, ""
