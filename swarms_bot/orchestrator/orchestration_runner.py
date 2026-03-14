"""OrchestrationRunner — the single entry point for full orchestration.

Ties together every component:
  1. DAGPlanner      — LLM decomposes goal into DAG
  2. HumanApprovalGate — user approves/rejects plan
  3. SharedWorkspace — filesystem coordination space
  4. AgentMessageBus — structured inter-agent messaging
  5. ModelRouter     — per-node best model selection
  6. SpawnableAgents — nested sub-agent spawning
  7. DAGExecutor     — parallel batch execution with retry
  8. Synthesis       — merge all results into final answer

Usage in handlers/ai.py:
    from swarms_bot.orchestrator.orchestration_runner import OrchestrationRunner
    runner = OrchestrationRunner(agent_registry, send_fn=msg.answer)
    result = await runner.run(goal="Build a FastAPI CRUD app", user_id=msg.from_user.id)
    await msg.answer(result)
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, Optional

from swarms_bot.orchestrator.dag_planner import DAGPlanner
from swarms_bot.orchestrator.dag_executor import DAGExecutor
from swarms_bot.orchestrator.agent_messaging import AgentMessageBus, MessageType
from swarms_bot.orchestrator.shared_workspace import SharedWorkspace
from swarms_bot.orchestrator.nested_agents import SpawnableAgent, SpawnContext
from swarms_bot.orchestrator.human_in_loop import HumanApprovalGate
from swarms_bot.orchestrator.model_router import ModelRouter

logger = logging.getLogger(__name__)


class OrchestrationRunner:
    """Full end-to-end orchestration runner."""

    def __init__(
        self,
        agent_registry: Dict[str, Any],
        send_fn: Optional[Callable] = None,   # async fn(text, markup=None)
        require_approval: bool = True,
        approval_timeout: int = 120,
        max_parallel: int = 4,
        persist_workspace: bool = True,
    ):
        self.registry = agent_registry
        self.send_fn = send_fn
        self.require_approval = require_approval
        self.approval_timeout = approval_timeout
        self.max_parallel = max_parallel
        self.persist_workspace = persist_workspace
        self.model_router = ModelRouter()

    async def run(
        self,
        goal: str,
        user_id: int = 0,
        progress_cb: Optional[Callable[[str], Coroutine]] = None,
    ) -> str:
        """
        Full orchestration pipeline. Returns final synthesized result string.
        """
        run_id = uuid.uuid4().hex[:8]
        start = time.monotonic()
        logger.info("OrchestrationRunner run=%s goal=%s", run_id, goal[:80])

        # 1. Message bus
        bus = AgentMessageBus(
            run_id=run_id,
            persist_path=f"data/messages/{run_id}.db" if self.persist_workspace else None,
        )

        # 2. Shared workspace
        workspace = SharedWorkspace(run_id=run_id)
        await workspace.set_goal(goal)
        await workspace.append_log(f"Run {run_id} started for user {user_id}")

        async def _notify(text: str, markup=None) -> None:
            await workspace.append_log(text)
            if progress_cb:
                await progress_cb(text)
            elif self.send_fn:
                try:
                    await self.send_fn(text, markup)
                except Exception:
                    pass

        # 3. Decompose goal into DAG
        await _notify("🧠 Decomposing goal into task plan…")
        planner = DAGPlanner()
        dag = await planner.decompose(goal)
        await workspace.set_plan(dag.to_text_plan())
        await bus.publish(
            sender="planner",
            msg_type=MessageType.PLAN,
            content=dag.to_text_plan(),
            payload={"node_count": len(dag.nodes)},
        )

        # 4. Human-in-the-loop approval
        if self.require_approval and self.send_fn:
            gate = HumanApprovalGate(
                send_fn=self.send_fn,
                timeout_seconds=self.approval_timeout,
            )

            async def _approval_cb(plan_text: str) -> bool:
                return await gate.request_plan_approval(plan_text, run_id=run_id)

            approved = await _approval_cb(dag.to_text_plan())
            if not approved:
                await _notify("❌ Plan rejected by user. Orchestration cancelled.")
                return "Orchestration cancelled."
        else:
            await _notify(dag.to_text_plan())

        # 5. Wire model router into each node
        for node in dag.nodes.values():
            complexity = self.model_router.estimate_complexity(node.description)
            best_model, _ = self.model_router.select(node.agent, complexity)
            node.description = (
                f"[Using model: {best_model}]\n\n"
                + node.description
            )
            await workspace.update_status(node.id, "pending", node.title)

        # 6. Build spawnable agent registry
        spawnable_registry: Dict[str, Any] = {}
        for key, agent in self.registry.items():
            spawn_ctx = SpawnContext(run_id=run_id, budget_remaining=5.0)
            spawnable_registry[key] = SpawnableAgentWrapper(
                agent=agent,
                spawn_ctx=spawn_ctx,
                registry=self.registry,
                bus=bus,
                workspace=workspace,
            )

        # 7. Execute DAG
        executor = DAGExecutor(
            agent_registry=spawnable_registry,
            max_parallel=self.max_parallel,
        )

        async def _progress_cb(text: str) -> None:
            await _notify(text)

        dag = await executor.execute(dag, progress_cb=_progress_cb)

        # 8. Write artifacts to workspace
        for node in dag.nodes.values():
            if node.result:
                await workspace.write_artifact(node.id, "result.md", node.result)
                await workspace.update_status(node.id, node.status, node.result[:80])
                await bus.publish(
                    sender=node.agent,
                    msg_type=MessageType.TASK_RESULT if node.status == "done" else MessageType.ERROR,
                    content=node.result[:500],
                    payload={"node_id": node.id, "cost": node.cost_usd},
                    recipient="broadcast",
                )

        # 9. Synthesize final result
        await _notify(f"🔗 Synthesizing results… ({dag.summary()})")
        all_results = await workspace.get_all_results()
        final_result = await self._synthesize(goal, all_results)

        elapsed = time.monotonic() - start
        await workspace.append_log(f"Run {run_id} complete in {elapsed:.1f}s — {dag.summary()}")
        await bus.publish(
            sender="orchestrator",
            msg_type=MessageType.FINAL_RESULT,
            content=final_result[:500],
            payload={"run_id": run_id, "elapsed_s": elapsed, "summary": dag.summary()},
        )

        footer = (
            f"\n\n---\n✅ <b>Orchestration complete</b> | "
            f"{dag.summary()} | {elapsed:.1f}s | run={run_id}"
        )
        return final_result + footer

    async def _synthesize(self, goal: str, all_results: str) -> str:
        """Call LLM to synthesize all agent outputs into a coherent final answer."""
        if not all_results.strip():
            return "No results produced."

        try:
            import litellm
            prompt = (
                f"You are a senior technical lead synthesizing outputs from multiple AI agents.\n"
                f"Original goal: {goal}\n\n"
                f"Agent outputs:\n{all_results[:8000]}\n\n"
                f"Produce a clear, complete, well-structured final answer that achieves the original goal."
            )
            response = await litellm.acompletion(
                model="groq/llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content or all_results
        except Exception as e:
            logger.warning("Synthesis LLM call failed: %s", e)
            return all_results


class SpawnableAgentWrapper:
    """Wraps a registry Agent with message bus + workspace integration."""

    def __init__(
        self,
        agent: Any,
        spawn_ctx: SpawnContext,
        registry: Dict[str, Any],
        bus: AgentMessageBus,
        workspace: SharedWorkspace,
    ):
        self.agent = agent
        self.spawn_ctx = spawn_ctx
        self.registry = registry
        self.bus = bus
        self.workspace = workspace

    async def execute(self, task: Any) -> Any:
        # Inject bus context into task description
        bus_context = self.bus.get_context_for_agent(
            self.agent.agent_key if hasattr(self.agent, "agent_key") else "general"
        )
        if bus_context:
            task.description = (
                f"{task.description}\n\n--- Shared Context from Other Agents ---\n{bus_context}"
            )
        return await self.agent.execute(task)
