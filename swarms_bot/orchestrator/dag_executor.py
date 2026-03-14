"""DAG Executor — runs a TaskDAG with parallel execution, retry, and progress callbacks.

Executes nodes in dependency order:
- Nodes with no pending dependencies run in parallel via asyncio.gather
- Results from upstream nodes are injected into downstream node descriptions
- Failed nodes mark dependent nodes as skipped
- Calls progress_cb after each batch completes
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Coroutine, Dict, List, Optional, Any

from swarms_bot.orchestrator.dag_planner import DAGNode, TaskDAG

logger = logging.getLogger(__name__)


class DAGExecutor:
    """Executes a TaskDAG respecting dependency order, with parallel batches."""

    def __init__(
        self,
        agent_registry: Dict[str, Any],  # agent_key -> Agent
        max_parallel: int = 4,
    ):
        self.registry = agent_registry
        self.max_parallel = max_parallel

    async def execute(
        self,
        dag: TaskDAG,
        progress_cb: Optional[Callable[[str], Coroutine]] = None,
        approval_cb: Optional[Callable[[str], Coroutine[Any, Any, bool]]] = None,
    ) -> TaskDAG:
        """
        Execute the DAG.
        - progress_cb(message): called after each batch completes
        - approval_cb(plan_text) -> bool: called before execution starts if set
          (human-in-the-loop: user must approve the plan)
        Returns the DAG with all node results populated.
        """
        # Human-in-the-loop: show plan and ask for approval
        if approval_cb:
            approved = await approval_cb(dag.to_text_plan())
            if not approved:
                for node in dag.nodes.values():
                    node.status = "skipped"
                    node.error = "Cancelled by user"
                return dag

        batch_num = 0
        while not dag.is_complete():
            ready = dag.get_ready_nodes()
            if not ready:
                # Check for stuck nodes (circular deps or all failed)
                pending = [n for n in dag.nodes.values() if n.status == "pending"]
                if pending:
                    logger.warning("DAG stuck — marking remaining nodes as skipped")
                    for node in pending:
                        node.status = "skipped"
                        node.error = "Upstream dependency failed"
                break

            batch_num += 1
            # Mark as running
            for node in ready:
                node.status = "running"

            if progress_cb:
                names = ", ".join(f"{n.id}:{n.title[:20]}" for n in ready)
                await progress_cb(f"🔄 Batch {batch_num}: running [{names}] in parallel")

            # Execute batch in parallel (respect max_parallel cap)
            semaphore = asyncio.Semaphore(self.max_parallel)
            tasks = [self._run_node(node, dag, semaphore) for node in ready]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Report batch results
            if progress_cb:
                for node in ready:
                    icon = "✅" if node.status == "done" else "❌"
                    await progress_cb(
                        f"{icon} {node.id} [{node.agent}]: "
                        f"{(node.result or node.error or '')[:120]}"
                    )

        return dag

    async def _run_node(
        self,
        node: DAGNode,
        dag: TaskDAG,
        semaphore: asyncio.Semaphore,
    ) -> None:
        """Execute a single DAG node, injecting upstream results into context."""
        async with semaphore:
            # Inject upstream results into description
            description = node.description
            for dep_id in node.depends_on:
                dep_node = dag.nodes.get(dep_id)
                if dep_node and dep_node.result:
                    description += (
                        f"\n\n--- Context from {dep_id} ({dep_node.title}) ---\n"
                        f"{dep_node.result[:1000]}"
                    )

            agent = self.registry.get(node.agent) or self.registry.get("general")
            if not agent:
                node.status = "failed"
                node.error = f"Agent '{node.agent}' not found in registry"
                return

            start = time.monotonic()
            for attempt in range(3):
                try:
                    from swarms_bot.orchestrator.agent_base import Task
                    task = Task.create(
                        user_id=0,
                        chat_id=0,
                        description=description,
                        context={"dag_node_id": node.id, "attempt": attempt},
                    )
                    response = await agent.execute(task)
                    node.execution_time_ms = int((time.monotonic() - start) * 1000)
                    node.cost_usd = response.cost_usd

                    if response.success:
                        node.status = "done"
                        node.result = str(response.result)
                        return
                    else:
                        node.error = str(response.result)
                except Exception as e:
                    node.error = str(e)
                    logger.warning("Node %s attempt %d failed: %s", node.id, attempt + 1, e)
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)

            node.status = "failed"
            # Mark dependent nodes as skipped
            for other in dag.nodes.values():
                if node.id in other.depends_on and other.status == "pending":
                    other.status = "skipped"
                    other.error = f"Upstream node {node.id} failed"
