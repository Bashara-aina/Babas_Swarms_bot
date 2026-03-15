"""tools/orchestrate_engine.py — DAG-based task decomposition and execution.

Decomposes a complex task into sub-tasks using the planner agent,
then executes them respecting dependencies (topological order),
running independent sub-tasks in parallel via asyncio.gather().
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

_PLANNER_PROMPT = (
    "You are a task planner. Decompose the user's request into 2-6 concrete sub-tasks.\n"
    "Return ONLY valid JSON (no markdown, no explanation) with this schema:\n"
    "[\n"
    '  {"id": 1, "task": "description", "agent": "agent_key", "depends_on": []},\n'
    '  {"id": 2, "task": "description", "agent": "agent_key", "depends_on": [1]}\n'
    "]\n\n"
    "Available agent keys: coding, debug, architect, analyst, researcher, "
    "marketer, devops, pm, general.\n\n"
    "Rules:\n"
    "- Each sub-task should be self-contained enough for one agent to handle\n"
    "- Use depends_on to express ordering (empty = can run immediately)\n"
    "- Keep it practical — 2-6 sub-tasks, not more\n"
    "- Choose the best agent for each sub-task\n"
)


@dataclass
class SubTask:
    id: int
    task: str
    agent: str
    depends_on: list[int]
    result: str = ""
    status: str = "pending"  # pending, running, done, failed


async def _decompose(task: str) -> list[SubTask]:
    """Use LLM to decompose a complex task into sub-tasks."""
    from llm_client import chat

    full_prompt = f"{_PLANNER_PROMPT}\nTask to decompose:\n{task}"
    raw, _model = await chat(full_prompt, agent_key="architect", user_id="0")

    # Extract JSON from response (handle markdown wrapping)
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: treat entire task as single sub-task
        logger.warning("Planner returned invalid JSON, falling back to single task")
        return [SubTask(id=1, task=task, agent="general", depends_on=[])]

    subtasks = []
    for item in items:
        subtasks.append(SubTask(
            id=item.get("id", len(subtasks) + 1),
            task=item.get("task", ""),
            agent=item.get("agent", "general"),
            depends_on=item.get("depends_on", []),
        ))
    return subtasks


async def _execute_subtask(
    st: SubTask,
    completed: dict[int, str],
) -> None:
    """Execute a single sub-task, injecting context from dependencies."""
    from llm_client import chat

    # Build context from completed dependencies
    context_parts = []
    for dep_id in st.depends_on:
        if dep_id in completed:
            context_parts.append(f"[Result from step {dep_id}]:\n{completed[dep_id][:500]}")

    prompt = st.task
    if context_parts:
        prompt = "Context from previous steps:\n" + "\n\n".join(context_parts) + "\n\nTask:\n" + st.task

    st.status = "running"
    try:
        result, _model = await chat(prompt, agent_key=st.agent, user_id="0")
        st.result = result
        st.status = "done"
        completed[st.id] = result
    except Exception as e:
        st.result = f"Error: {e}"
        st.status = "failed"
        completed[st.id] = st.result


async def orchestrate_task(
    task: str,
    progress_cb: Optional[Callable[[str], Coroutine]] = None,
) -> str:
    """Decompose and execute a complex task.

    Args:
        task: The complex task description.
        progress_cb: Optional async callback for progress updates.

    Returns:
        HTML-formatted results from all sub-tasks.
    """
    # Step 1: Decompose
    if progress_cb:
        try:
            await progress_cb("decomposing task into sub-tasks…")
        except Exception:
            pass

    subtasks = await _decompose(task)
    if not subtasks:
        return "<b>Could not decompose task.</b>"

    # Step 2: Execute in topological order
    completed: dict[int, str] = {}
    task_map = {st.id: st for st in subtasks}
    remaining = set(st.id for st in subtasks)

    while remaining:
        # Find tasks whose dependencies are all satisfied
        ready = [
            tid for tid in remaining
            if all(d in completed for d in task_map[tid].depends_on)
        ]
        if not ready:
            # Deadlock — break cycle by running one anyway
            ready = [next(iter(remaining))]

        if progress_cb:
            names = [task_map[tid].task[:40] for tid in ready]
            try:
                await progress_cb(f"running {len(ready)} task(s): {', '.join(names)}")
            except Exception:
                pass

        # Execute ready tasks in parallel
        await asyncio.gather(
            *(_execute_subtask(task_map[tid], completed) for tid in ready)
        )
        remaining -= set(ready)

    # Step 3: Format results
    lines = [f"<b>Orchestration Complete</b> — {len(subtasks)} sub-tasks\n"]
    for st in subtasks:
        icon = "✅" if st.status == "done" else "❌"
        lines.append(
            f"\n{icon} <b>Step {st.id}</b>: {html.escape(st.task[:80])}\n"
            f"Agent: <code>{st.agent}</code> | Status: {st.status}\n"
            f"{st.result[:800]}"
        )

    return "\n".join(lines)
