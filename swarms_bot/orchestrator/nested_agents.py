"""Nested agent spawning — agents can spawn sub-agents to unlimited depth.

Implements the recursive supervisor pattern:
  ChiefOfStaff
    └── Coordinator Agent
          ├── CodeAgent
          │     └── TestAgent (spawned by CodeAgent)
          └── ReviewAgent
                └── SecurityAgent (spawned by ReviewAgent)

Each SpawnableAgent can:
1. Detect it needs a sub-agent (via task complexity or explicit tool call)
2. Spawn a child SpawnableAgent with a sub-task
3. Receive the child result and incorporate it into its own response

Depth is capped at MAX_DEPTH to prevent infinite recursion.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_DEPTH = 4  # max nesting depth


@dataclass
class SpawnContext:
    """Context passed down through nested agent calls."""
    run_id: str
    depth: int = 0
    parent_agent: str = ""
    budget_remaining: float = 5.0
    spawn_log: List[Dict] = field(default_factory=list)


class SpawnableAgent:
    """An agent that can spawn child agents for sub-tasks.

    Wraps any Agent from the registry and adds spawning capability.
    When the agent's response contains a spawn directive
    (e.g. '<spawn agent="coding" task="..." />'), the framework
    executes the sub-task and injects the result back.
    """

    def __init__(
        self,
        agent_key: str,
        agent_registry: Dict[str, Any],
        spawn_ctx: Optional[SpawnContext] = None,
    ):
        self.agent_key = agent_key
        self.registry = agent_registry
        self.ctx = spawn_ctx or SpawnContext(run_id="default")

    async def execute(
        self,
        task_description: str,
        thread_id: Optional[str] = None,
    ) -> tuple[str, float]:  # (result, cost_usd)
        """Execute task, auto-handling any sub-agent spawns."""
        import re
        from llm_client import chat

        if self.ctx.depth >= MAX_DEPTH:
            logger.warning(
                "Max spawn depth %d reached for agent %s", MAX_DEPTH, self.agent_key
            )
            result, _ = await chat(task_description, agent_key=self.agent_key, thread_id=thread_id)
            return result, 0.0

        # First pass: run the agent
        result, model = await chat(
            task_description,
            agent_key=self.agent_key,
            thread_id=thread_id,
        )

        # Check for spawn directives in result
        spawn_pattern = re.compile(
            r'<spawn\s+agent="([^"]+)"\s+task="([^"]+)"\s*/?>',
            re.IGNORECASE | re.DOTALL,
        )
        spawn_matches = spawn_pattern.findall(result)

        if not spawn_matches:
            return result, 0.0

        # Execute all spawn directives (parallel)
        logger.info(
            "Agent %s (depth=%d) spawning %d sub-agents: %s",
            self.agent_key, self.ctx.depth,
            len(spawn_matches),
            [m[0] for m in spawn_matches],
        )

        async def _spawn_one(child_key: str, child_task: str) -> tuple[str, str, float]:
            child_ctx = SpawnContext(
                run_id=self.ctx.run_id,
                depth=self.ctx.depth + 1,
                parent_agent=self.agent_key,
                budget_remaining=self.ctx.budget_remaining,
                spawn_log=self.ctx.spawn_log,
            )
            child = SpawnableAgent(child_key, self.registry, child_ctx)
            child_result, child_cost = await child.execute(child_task, thread_id=thread_id)
            self.ctx.spawn_log.append({
                "parent": self.agent_key,
                "child": child_key,
                "depth": self.ctx.depth + 1,
                "task": child_task[:80],
                "cost": child_cost,
            })
            return child_key, child_result, child_cost

        spawn_results = await asyncio.gather(
            *[_spawn_one(key, task) for key, task in spawn_matches],
            return_exceptions=True,
        )

        total_cost = 0.0
        # Replace spawn directives with actual results
        final_result = result
        for i, (key, task) in enumerate(spawn_matches):
            sr = spawn_results[i]
            if isinstance(sr, Exception):
                child_output = f"[spawn failed: {sr}]"
            else:
                _, child_output, child_cost = sr
                total_cost += child_cost
            # Replace directive with result
            directive = f'<spawn agent="{key}" task="{task}" />'
            final_result = final_result.replace(directive, f"\n\n**[Sub-agent {key} result]:**\n{child_output}\n")

        return final_result, total_cost

    def spawn_tree_summary(self) -> str:
        """Return a readable summary of all spawns that occurred."""
        if not self.ctx.spawn_log:
            return "No sub-agents spawned."
        lines = ["🌳 Agent Spawn Tree:"]
        for entry in self.ctx.spawn_log:
            indent = "  " * entry["depth"]
            lines.append(f"{indent}└── {entry['child']} (spawned by {entry['parent']}): {entry['task']}")
        return "\n".join(lines)
