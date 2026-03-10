"""orchestrator.py — Multi-agent team execution for Legion v4.

Full team model with named specialist agents, task decomposition,
parallel execution with dependency DAG, and result synthesis.
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

# ── Agent Team Registry ─────────────────────────────────────────────────────

AGENT_TEAM = {
    "strategist": {
        "model": "cerebras/qwen-3-235b-a22b",
        "role": "High-level planning, architecture decisions, business strategy",
        "system": (
            "You are a senior technical strategist. Break complex goals into clear sub-tasks. "
            "Assign each sub-task to the right specialist. Consider dependencies between tasks. "
            "Think about sequencing: what must happen first? What can run in parallel?"
        ),
    },
    "developer": {
        "model": "groq/llama-3.3-70b-versatile",
        "role": "Code generation, debugging, refactoring",
        "system": (
            "You are a senior software engineer. Write clean, tested, production-ready code. "
            "Give exact file paths and complete implementations. Handle edge cases."
        ),
    },
    "researcher": {
        "model": "groq/moonshotai/kimi-k2-instruct",
        "role": "Academic research, paper analysis, competitive intelligence",
        "system": (
            "You are an academic researcher. Analyze papers rigorously, find evidence, "
            "cite sources. Be precise with numbers, equations, and methodologies."
        ),
    },
    "marketer": {
        "model": "groq/llama-3.3-70b-versatile",
        "role": "Content, social media, copywriting, brand strategy",
        "system": (
            "You are a senior marketing strategist. Create compelling content that resonates. "
            "Know platform conventions. Write authentic, value-driven copy."
        ),
    },
    "analyst": {
        "model": "groq/moonshotai/kimi-k2-instruct",
        "role": "Data analysis, metrics, benchmarks, performance review",
        "system": (
            "You are a quantitative analyst. Analyze data with statistical rigor. "
            "Identify trends, anomalies, correlations. Present findings clearly with evidence."
        ),
    },
    "devops": {
        "model": "groq/llama-3.3-70b-versatile",
        "role": "Infrastructure, deployment, CI/CD, security, monitoring",
        "system": (
            "You are a senior DevOps engineer. Think about reliability, security, scalability. "
            "Give exact commands and configuration. Consider failure modes."
        ),
    },
    "pm": {
        "model": "cerebras/qwen-3-235b-a22b",
        "role": "Project management, task decomposition, deadline tracking",
        "system": (
            "You are a senior PM. Break work into clear tasks with owners and deadlines. "
            "Track dependencies. Identify blockers. Keep things on schedule."
        ),
    },
}


@dataclass
class SubTask:
    description: str
    agent_key: str = "general"
    depends_on: list[int] = field(default_factory=list)
    result: str = ""
    status: str = "pending"  # pending, running, completed, failed


# ── Task Decomposition ──────────────────────────────────────────────────────

async def decompose_task(task: str) -> list[dict[str, Any]]:
    """Send task to strategist for decomposition into subtasks."""
    from llm_client import chat

    available = ", ".join(AGENT_TEAM.keys())
    all_agents = f"{available}, coding, debug, math, architect, analyst, general"

    prompt = (
        "You are a task decomposition system. Break this task into sub-tasks.\n\n"
        f"Available agents: {all_agents}\n\n"
        "Respond with ONLY a JSON array (no other text):\n"
        '[{"id": "1", "agent": "agent_type", "task": "what to do", "depends_on": []}]\n\n'
        "Rules:\n"
        "- Assign the right specialist agent to each sub-task\n"
        "- Use depends_on to specify which tasks must complete first (by id)\n"
        "- Tasks without dependencies can run in parallel\n"
        "- Keep sub-tasks focused and actionable\n\n"
        f"Task: {task}"
    )

    result, _ = await chat(prompt, agent_key="architect")

    try:
        text = result.strip()
        if "[" in text:
            start = text.index("[")
            end = text.rindex("]") + 1
            subtasks = json.loads(text[start:end])
            return subtasks
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Decomposition parse failed: %s", e)

    return [{"id": "1", "agent": "general", "task": task, "depends_on": []}]


# ── Parallel Execution ──────────────────────────────────────────────────────

async def execute_parallel(
    subtasks: list[dict[str, Any]],
    progress_cb: ProgressCb = None,
) -> dict[str, str]:
    """Execute subtasks respecting dependencies. Returns {id: result}."""
    from llm_client import chat

    completed: dict[str, str] = {}
    total = len(subtasks)
    task_map = {str(s["id"]): s for s in subtasks}

    max_iterations = total * 2
    iteration = 0

    while len(completed) < total and iteration < max_iterations:
        iteration += 1

        ready = []
        for s in subtasks:
            sid = str(s["id"])
            if sid in completed:
                continue
            deps = [str(d) for d in s.get("depends_on", [])]
            if all(d in completed for d in deps):
                ready.append(s)

        if not ready:
            remaining = [s for s in subtasks if str(s["id"]) not in completed]
            if remaining:
                ready = [remaining[0]]
            else:
                break

        async def _run_subtask(s: dict) -> tuple[str, str]:
            async with _parallel_sem:
                sid = str(s["id"])
                agent = s.get("agent", "general")
                task_desc = s.get("task", "")

                if progress_cb:
                    await progress_cb(
                        f"[{len(completed)+1}/{total}] {agent}: {task_desc[:50]}..."
                    )

                context_parts = []
                for dep_id in s.get("depends_on", []):
                    dep_id_str = str(dep_id)
                    if dep_id_str in completed:
                        dep_task = task_map.get(dep_id_str, {})
                        context_parts.append(
                            f"Result from '{dep_task.get('task', '')[:40]}': "
                            f"{completed[dep_id_str][:300]}"
                        )

                full_task = task_desc
                if context_parts:
                    full_task += "\n\nContext from previous steps:\n" + "\n".join(context_parts)

                # Map team agents to standard agent keys for chat()
                agent_map = {
                    "strategist": "architect",
                    "developer": "coding",
                    "researcher": "debug",
                    "marketer": "general",
                    "analyst": "analyst",
                    "devops": "general",
                    "pm": "architect",
                }
                chat_agent = agent_map.get(agent, agent)

                try:
                    result, _ = await chat(full_task, agent_key=chat_agent)
                    return sid, result
                except Exception as e:
                    return sid, f"Failed: {e}"

        batch = ready[:MAX_PARALLEL]
        results = await asyncio.gather(*[_run_subtask(s) for s in batch])

        for sid, result in results:
            completed[sid] = result

    return completed


# ── Result Synthesis ────────────────────────────────────────────────────────

async def synthesize_results(
    task: str,
    subtask_results: dict[str, str],
    subtasks: list[dict[str, Any]],
) -> str:
    """Send all results to strategist for final synthesis."""
    from llm_client import chat

    parts = []
    for s in subtasks:
        sid = str(s["id"])
        agent = s.get("agent", "?")
        desc = s.get("task", "?")
        result = subtask_results.get(sid, "(no result)")
        parts.append(f"[{agent}] {desc}\nResult: {result[:500]}")

    context = "\n\n".join(parts)

    prompt = (
        f"You are synthesizing results from multiple specialist agents.\n\n"
        f"Original task: {task}\n\n"
        f"Agent results:\n{context}\n\n"
        "Synthesize these into a single coherent response. "
        "Highlight key findings, recommendations, and action items. "
        "Be concise but comprehensive."
    )

    result, _ = await chat(prompt, agent_key="architect")
    return result


# ── Legacy-compatible functions ─────────────────────────────────────────────

async def parallel_agents(
    task: str,
    sub_tasks: list[SubTask],
    progress_cb: ProgressCb = None,
) -> str:
    """Execute sub-tasks respecting dependency DAG. Legacy interface."""
    from llm_client import chat

    completed: dict[int, str] = {}
    total = len(sub_tasks)

    while len(completed) < total:
        ready = [
            i for i, s in enumerate(sub_tasks)
            if i not in completed
            and s.status == "pending"
            and all(d in completed for d in s.depends_on)
        ]

        if not ready:
            pending = [i for i in range(total) if i not in completed]
            if all(
                any(d not in completed for d in sub_tasks[i].depends_on)
                for i in pending
            ):
                break
            await asyncio.sleep(0.1)
            continue

        async def _run(idx: int) -> tuple[int, str]:
            async with _parallel_sem:
                step = sub_tasks[idx]
                step.status = "running"

                if progress_cb:
                    await progress_cb(
                        f"[{len(completed)+1}/{total}] {step.agent_key}: {step.description[:50]}..."
                    )

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

        batch = ready[:MAX_PARALLEL]
        results = await asyncio.gather(*[_run(i) for i in batch])

        for idx, result in results:
            completed[idx] = result
            sub_tasks[idx].result = result

    return _synthesize_legacy(task, sub_tasks, completed)


def _synthesize_legacy(task: str, sub_tasks: list[SubTask], completed: dict[int, str]) -> str:
    """Combine sub-task results into a coherent response."""
    lines = [f"Task: {task}", f"Completed {len(completed)}/{len(sub_tasks)} sub-tasks:", ""]

    for i, st in enumerate(sub_tasks):
        status = "done" if st.status == "completed" else "failed"
        lines.append(f"[{status}] [{st.agent_key}] {st.description}")
        if i in completed:
            result = completed[i]
            if len(result) > 500:
                result = result[:500] + "..."
            lines.append(f"   {result}")
        lines.append("")

    return "\n".join(lines)


async def auto_decompose(task: str) -> list[SubTask] | None:
    """Use LLM to decompose a complex task into sub-tasks."""
    from llm_client import chat

    prompt = (
        "You are a task decomposition system. Analyze this task and decide:\n"
        "1. If it's simple enough for a single agent, respond with: SIMPLE\n"
        "2. If it needs multiple steps, respond with a JSON array of sub-tasks.\n\n"
        "Available agent types: coding, debug, math, architect, analyst, general, "
        "strategist, developer, researcher, marketer, devops, pm\n\n"
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
    """Top-level router: decides single agent vs multi-agent."""
    sub_tasks = await auto_decompose(task)

    if sub_tasks and len(sub_tasks) >= 2:
        if progress_cb:
            await progress_cb(f"decomposed into {len(sub_tasks)} sub-tasks")
        result = await parallel_agents(task, sub_tasks, progress_cb)
        return result, "orchestrator"

    return None, ""
