# /home/newadmin/swarm-bot/orchestration/supervisor.py
"""Hierarchical Supervisor Agent — decomposes complex tasks and orchestrates sub-agents.

Patterns:
- Sequential: A → B → C  (when B depends on A)
- Parallel: [A, B, C] → merge  (when independent)
- Hierarchical: Supervisor → [Worker1, Worker2] → Synthesis

For simple tasks (keyword count ≤ 1 agent), falls back to direct routing.
For complex tasks, the supervisor uses the architect model to create a plan.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

MAX_PARALLEL = 3        # Max agents to run concurrently
MAX_PLAN_STEPS = 6      # Max steps in a decomposed plan
COMPLEXITY_THRESHOLD = 120   # Token count above which supervisor activates


@dataclass
class SubTask:
    """An atomic step in an orchestrated plan.

    Attributes:
        description: What this step does.
        agent_key: Which agent handles it.
        depends_on: Indices of prerequisite steps (empty = can run immediately).
        result: Filled in after execution.
    """

    description: str
    agent_key: str
    depends_on: list[int] = field(default_factory=list)
    result: str = ""


def _is_complex(task: str) -> bool:
    """Heuristic: decide if a task warrants supervisor orchestration.

    Args:
        task: Raw task string.

    Returns:
        True if the task is complex enough to decompose.
    """
    t = task.lower()

    # Multi-step indicators
    multi_step_kws = [
        "then", "after that", "first", "finally", "step by step",
        "and then", "also", "additionally", "finally", "commit",
        "and restart", "and run", "and fix", "and deploy",
    ]
    multi_step = sum(1 for kw in multi_step_kws if kw in t)

    # Cross-domain indicators
    domains = ["debug", "code", "design", "explain", "test", "deploy", "commit", "scrape", "screenshot"]
    domain_count = sum(1 for d in domains if d in t)

    return (
        len(task) > COMPLEXITY_THRESHOLD
        or multi_step >= 2
        or domain_count >= 3
    )


def _quick_decompose(task: str) -> list[SubTask]:
    """Rule-based decomposition for common multi-step patterns.

    Used as fast-path before invoking the architect model.

    Args:
        task: Task string to decompose.

    Returns:
        List of SubTasks, or empty list if no pattern matched.
    """
    t = task.lower()

    # Pattern: "debug X, fix it, commit"
    if ("debug" in t or "error" in t) and ("fix" in t or "correct" in t) and "commit" in t:
        return [
            SubTask("Analyze and debug the error", "debug"),
            SubTask("Apply the fix to the code", "coding", depends_on=[0]),
            SubTask("Run tests to verify the fix", "coding", depends_on=[1]),
            SubTask("Commit the changes", "coding", depends_on=[2]),
        ]

    # Pattern: "explain X then implement it"
    if ("explain" in t or "what is" in t) and ("implement" in t or "write" in t or "code" in t):
        return [
            SubTask("Explain the concept clearly", "mentor"),
            SubTask("Implement the solution", "coding", depends_on=[0]),
        ]

    # Pattern: "analyze data and plot"
    if ("analyze" in t or "analyse" in t) and ("plot" in t or "chart" in t or "visualize" in t):
        return [
            SubTask("Analyze the data and extract insights", "analyst"),
            SubTask("Generate visualization code", "coding", depends_on=[0]),
        ]

    # Pattern: "design and implement"
    if ("design" in t or "architect" in t or "plan" in t) and ("implement" in t or "build" in t or "code" in t):
        return [
            SubTask("Design the architecture and create a plan", "architect"),
            SubTask("Implement based on the design", "coding", depends_on=[0]),
        ]

    return []


async def _llm_decompose(task: str, run_fn) -> list[SubTask]:
    """Use architect model to decompose a complex task into SubTasks.

    Args:
        task: Complex task to decompose.
        run_fn: Async function(model, task, agent_key) → str.

    Returns:
        List of SubTasks from LLM decomposition.
    """
    import agents as ag

    prompt = f"""Break this task into 2-5 atomic steps for AI agents.

Task: {task}

Available agents: {', '.join(ag.AGENT_MODELS.keys())}

Respond ONLY with a numbered list, one step per line:
1. [agent_name] description of step
2. [agent_name] description of step

No preamble, no explanation. Just the numbered list."""

    model = ag.get_model("architect")
    try:
        response = await run_fn(model, prompt, "architect")
    except Exception as exc:
        logger.warning("LLM decompose failed: %s", exc)
        return []

    steps = []
    for line in response.strip().splitlines():
        m = re.match(r"\d+\.\s*\[(\w+)\]\s*(.+)", line.strip())
        if m:
            agent_key = m.group(1).lower()
            desc = m.group(2).strip()
            import agents as ag2
            if agent_key in ag2.AGENT_MODELS:
                # Each step depends on the previous one (sequential by default)
                deps = [len(steps) - 1] if steps else []
                steps.append(SubTask(desc, agent_key, depends_on=deps))

    if len(steps) > MAX_PLAN_STEPS:
        steps = steps[:MAX_PLAN_STEPS]

    logger.info("LLM decomposed task into %d steps", len(steps))
    return steps


async def orchestrate(
    task: str,
    run_fn,
    progress_fn=None,
) -> str:
    """Orchestrate a task — decompose if complex, run agents, synthesize.

    Args:
        task: User's task string.
        run_fn: Async function(model, task, agent_key) → str.
        progress_fn: Optional async callback(str) for progress updates.

    Returns:
        Final synthesised result string.
    """
    if not _is_complex(task):
        return None   # Signal to caller: use direct routing

    if progress_fn:
        await progress_fn("Decomposing complex task…")

    # Try fast rule-based decomposition first
    steps = _quick_decompose(task)
    if not steps:
        steps = await _llm_decompose(task, run_fn)

    if not steps or len(steps) < 2:
        return None   # Not decomposable — fall back to direct routing

    if progress_fn:
        plan = "\n".join(f"{i+1}. [{s.agent_key}] {s.description}" for i, s in enumerate(steps))
        await progress_fn(f"Plan ({len(steps)} steps):\n{plan}")

    # Execute steps respecting dependencies
    completed: dict[int, str] = {}

    while len(completed) < len(steps):
        # Find steps ready to run (all deps satisfied)
        ready = [
            i for i, s in enumerate(steps)
            if i not in completed
            and all(d in completed for d in s.depends_on)
        ]

        if not ready:
            logger.error("Dependency deadlock — running remaining steps sequentially")
            ready = [i for i in range(len(steps)) if i not in completed][:1]

        # Run ready steps in parallel (up to MAX_PARALLEL)
        batch = ready[:MAX_PARALLEL]
        if progress_fn and batch:
            descs = ", ".join(steps[i].description[:40] for i in batch)
            await progress_fn(f"Running ({len(batch)} parallel): {descs}…")

        async def _run_step(idx: int) -> tuple[int, str]:
            step = steps[idx]
            import agents as ag
            model = ag.get_model(step.agent_key) or ag.get_model("coding")

            # Inject prior results as context
            prior_context = ""
            if step.depends_on and step.depends_on[0] in completed:
                dep_result = completed[step.depends_on[0]]
                prior_context = f"\n\nContext from previous step:\n{dep_result[:800]}"

            full_task = f"{step.description}{prior_context}"
            try:
                result = await run_fn(model, full_task, step.agent_key)
            except Exception as exc:
                logger.exception("Step %d failed: %s", idx, exc)
                result = f"[Step failed: {exc}]"
            return idx, result

        results = await asyncio.gather(*[_run_step(i) for i in batch])
        for idx, result in results:
            completed[idx] = result
            steps[idx].result = result

    # Synthesize all results
    all_results = "\n\n".join(
        f"**Step {i+1} [{s.agent_key}]:** {s.description}\n{s.result}"
        for i, s in enumerate(steps)
    )

    if len(steps) == 1:
        return steps[0].result

    # Use mentor to synthesize
    import agents as ag
    mentor_model = ag.get_model("mentor") or ag.get_model("coding")
    synth_prompt = (
        f"Synthesize these agent results into a single coherent answer for:\n\n"
        f"Original task: {task}\n\n{all_results}\n\n"
        f"Provide a clean, integrated response. Be concise."
    )

    if progress_fn:
        await progress_fn("Synthesizing results…")

    try:
        synthesis = await run_fn(mentor_model, synth_prompt, "mentor")
    except Exception:
        synthesis = all_results  # Return raw results on synthesis failure

    return synthesis
