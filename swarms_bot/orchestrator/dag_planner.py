"""DAG Planner — decomposes a complex goal into a dependency graph of subtasks.

When given a high-level goal like "build a full-stack app", the planner:
1. Calls an LLM to decompose it into N subtasks
2. Assigns the best agent + model to each node
3. Builds a directed acyclic graph (DAG) of dependencies
4. Returns a TaskDAG ready for parallel/sequential execution

This closes the gap vs Perplexity Computer which auto-fractures goals
into dependency graphs and assigns specialized models per node.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Prompt used to decompose a goal into subtasks
_DECOMPOSE_PROMPT = """
You are a senior engineering project planner.
Decompose the following goal into a list of concrete subtasks.

Rules:
- Each subtask must be atomic and executable by a single specialized AI agent
- Identify dependencies: which subtasks must complete BEFORE each one starts
- Assign the best agent type from: coding, debug, math, architect, analyst, researcher, general, devops, pm, computer
- Output ONLY valid JSON, no explanation

Goal: {goal}

Output format (JSON array):
[
  {{
    "id": "t1",
    "title": "Short title",
    "description": "Full task description for the agent",
    "agent": "architect",
    "depends_on": [],
    "priority": 1
  }},
  {{
    "id": "t2",
    "title": "Implement API",
    "description": "Implement the FastAPI endpoints defined in t1",
    "agent": "coding",
    "depends_on": ["t1"],
    "priority": 2
  }}
]

Respond with ONLY the JSON array.
"""


@dataclass
class DAGNode:
    """A single node in the task DAG."""
    id: str
    title: str
    description: str
    agent: str
    depends_on: List[str] = field(default_factory=list)
    priority: int = 1
    status: str = "pending"        # pending | running | done | failed | skipped
    result: Optional[str] = None
    error: Optional[str] = None
    cost_usd: float = 0.0
    execution_time_ms: int = 0


@dataclass
class TaskDAG:
    """A directed acyclic graph of subtasks."""
    goal: str
    nodes: Dict[str, DAGNode] = field(default_factory=dict)
    execution_order: List[List[str]] = field(default_factory=list)  # batches of parallel tasks

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.id] = node

    def get_ready_nodes(self) -> List[DAGNode]:
        """Return nodes whose dependencies are all done."""
        ready = []
        for node in self.nodes.values():
            if node.status != "pending":
                continue
            deps_done = all(
                self.nodes.get(dep, DAGNode("", "", "", "", status="done")).status == "done"
                for dep in node.depends_on
            )
            if deps_done:
                ready.append(node)
        return ready

    def is_complete(self) -> bool:
        return all(n.status in ("done", "failed", "skipped") for n in self.nodes.values())

    def summary(self) -> str:
        done = sum(1 for n in self.nodes.values() if n.status == "done")
        failed = sum(1 for n in self.nodes.values() if n.status == "failed")
        total = len(self.nodes)
        total_cost = sum(n.cost_usd for n in self.nodes.values())
        return f"{done}/{total} done, {failed} failed, ${total_cost:.4f} total"

    def to_text_plan(self) -> str:
        """Human-readable plan for Telegram display."""
        lines = [f"📋 <b>Plan for:</b> {self.goal}\n"]
        for node in sorted(self.nodes.values(), key=lambda n: n.priority):
            deps = ", ".join(node.depends_on) if node.depends_on else "none"
            icon = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌", "skipped": "⏭"}.get(node.status, "⏳")
            lines.append(f"{icon} <code>{node.id}</code> [{node.agent}] {node.title}")
            if node.depends_on:
                lines.append(f"   ↳ depends on: {deps}")
        return "\n".join(lines)


class DAGPlanner:
    """Uses an LLM to decompose a goal into a TaskDAG."""

    def __init__(self, model: str = "groq/llama-3.3-70b-versatile"):
        self.model = model

    async def decompose(self, goal: str, max_tasks: int = 12) -> TaskDAG:
        """Call LLM to decompose goal into TaskDAG."""
        try:
            import litellm
            prompt = _DECOMPOSE_PROMPT.format(goal=goal)
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048,
            )
            raw = response.choices[0].message.content or ""
            subtasks = self._parse_json(raw)
        except Exception as e:
            logger.warning("LLM decomposition failed (%s), using single-task fallback", e)
            subtasks = [{
                "id": "t1",
                "title": goal[:60],
                "description": goal,
                "agent": "general",
                "depends_on": [],
                "priority": 1,
            }]

        dag = TaskDAG(goal=goal)
        for raw_node in subtasks[:max_tasks]:
            node = DAGNode(
                id=raw_node.get("id", f"t{len(dag.nodes)+1}"),
                title=raw_node.get("title", "")[:80],
                description=raw_node.get("description", goal),
                agent=raw_node.get("agent", "general"),
                depends_on=raw_node.get("depends_on", []),
                priority=raw_node.get("priority", 1),
            )
            dag.add_node(node)

        logger.info("DAG created: %d nodes for goal: %s", len(dag.nodes), goal[:60])
        return dag

    def _parse_json(self, raw: str) -> list:
        """Extract JSON array from LLM output, handling markdown fences."""
        # Strip markdown code fences
        raw = re.sub(r"```(?:json)?\n?", "", raw).strip()
        # Find first [ ... ] block
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw)
