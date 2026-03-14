"""ChiefOfStaff — Central orchestrator for multi-agent task routing.

Implements the supervisor pattern with deterministic routing:
1. Classify incoming task type
2. Select appropriate agent based on capability
3. Execute with retry and fallback
4. Track cost, latency, and routing decisions

Integrates with existing agents.py/llm_client.py infrastructure
while adding structured orchestration on top.

Enterprise integrations (optional, fail-open):
- BudgetManager: enforce cost limits before execution
- SecurityGuard: validate inputs before processing
- AuditLogger: log all routing decisions for compliance
- CostMetricsCollector: track real-time cost metrics
- CostAwareRouter: select cheapest capable model
- SessionManager: track tasks within user sessions
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    PLANNING = "planning"
    RESEARCH = "research"
    TESTING = "testing"
    DEBUG = "debug"
    MATH = "math"
    COMPUTER_CONTROL = "computer_control"
    GENERAL_QA = "general_qa"


@dataclass
class Task:
    """A unit of work to be routed and executed by an agent."""

    task_id: str
    user_id: int
    chat_id: int
    description: str
    task_type: Optional[TaskType] = None
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    max_retries: int = 3

    @classmethod
    def create(
        cls,
        user_id: int,
        chat_id: int,
        description: str,
        task_type: Optional[TaskType] = None,
        context: Optional[Dict] = None,
    ) -> "Task":
        return cls(
            task_id=str(uuid.uuid4())[:12],
            user_id=user_id,
            chat_id=chat_id,
            description=description,
            task_type=task_type,
            context=context or {},
        )


@dataclass
class AgentResponse:
    """Standardized response from any agent execution."""

    success: bool
    result: Any
    agent_name: str
    cost_usd: float = 0.0
    tokens_used: int = 0
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Task classification keywords ──────────────────────────────────────────────

_CLASSIFICATION_KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.CODE_GENERATION: [
        "code", "implement", "function", "class", "write", "create",
        "endpoint", "api", "script", "program", "build",
    ],
    TaskType.CODE_REVIEW: [
        "review", "audit", "check", "inspect", "security",
        "vulnerability", "quality",
    ],
    TaskType.PLANNING: [
        "plan", "design", "architect", "strategy", "roadmap",
        "decompose", "break down",
    ],
    TaskType.RESEARCH: [
        "research", "paper", "arxiv", "find", "search",
        "compare", "survey", "literature",
    ],
    TaskType.TESTING: [
        "test", "pytest", "unittest", "coverage", "spec",
    ],
    TaskType.DEBUG: [
        "debug", "traceback", "exception", "error", "crash", "fix",
        "bug", "nan", "oom", "cuda",
    ],
    TaskType.MATH: [
        "tensor", "matrix", "gradient", "derivative", "backprop",
        "calculate", "proof", "equation", "eigenvalue",
    ],
    TaskType.COMPUTER_CONTROL: [
        "screenshot", "click", "open", "desktop", "gui",
        "window", "mouse", "keyboard",
    ],
}

# Task type → preferred agent key (maps to existing agents.py keys)
_TASK_AGENT_MAP: Dict[TaskType, str] = {
    TaskType.CODE_GENERATION: "coding",
    TaskType.CODE_REVIEW: "coding",
    TaskType.PLANNING: "architect",
    TaskType.RESEARCH: "researcher",
    TaskType.TESTING: "coding",
    TaskType.DEBUG: "debug",
    TaskType.MATH: "math",
    TaskType.COMPUTER_CONTROL: "computer",
    TaskType.GENERAL_QA: "general",
}


class ChiefOfStaff:
    """Central orchestrator that routes tasks to specialized agents.

    Implements supervisor pattern with:
    - Keyword-based task classification (fast, no LLM call)
    - Agent selection from existing registry
    - Retry with exponential backoff
    - Cost and routing decision logging
    - Budget enforcement (optional)
    - Security validation (optional)
    - Audit logging (optional)
    - Cost metrics collection (optional)
    - Session tracking (optional)
    """

    def __init__(
        self,
        budget_manager: Optional[Any] = None,
        security_guard: Optional[Any] = None,
        audit_logger: Optional[Any] = None,
        cost_metrics: Optional[Any] = None,
        cost_router: Optional[Any] = None,
        session_manager: Optional[Any] = None,
    ) -> None:
        self.routing_history: List[Dict[str, Any]] = []
        self._total_cost_usd: float = 0.0
        self._total_tasks: int = 0
        self._successful_tasks: int = 0

        # Enterprise integrations (all optional, fail-open)
        self._budget = budget_manager
        self._security = security_guard
        self._audit = audit_logger
        self._cost_metrics = cost_metrics
        self._cost_router = cost_router
        self._sessions = session_manager

    def set_budget_manager(self, bm: Any) -> None:
        self._budget = bm

    def set_security_guard(self, sg: Any) -> None:
        self._security = sg

    def set_audit_logger(self, al: Any) -> None:
        self._audit = al

    def set_cost_metrics(self, cm: Any) -> None:
        self._cost_metrics = cm

    def set_cost_router(self, cr: Any) -> None:
        self._cost_router = cr

    def set_session_manager(self, sm: Any) -> None:
        self._sessions = sm

    def classify_task(self, task: Task) -> TaskType:
        """Classify task type using keyword matching.

        Fast path — no LLM call. Uses keyword scoring
        against CLASSIFICATION_KEYWORDS.
        """
        if task.task_type is not None:
            return task.task_type

        description_lower = task.description.lower()
        scores: Dict[TaskType, int] = {}

        for task_type, keywords in _CLASSIFICATION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in description_lower)
            if score > 0:
                scores[task_type] = score

        if scores:
            best_type = max(scores, key=lambda t: scores[t])
            logger.info(
                "Task classified: %s (score=%d)",
                best_type.value,
                scores[best_type],
            )
            return best_type

        return TaskType.GENERAL_QA

    def select_agent_key(self, task_type: TaskType, context: Dict) -> str:
        """Select the agent key for this task type.

        Returns a key compatible with existing agents.py AGENT_MODELS.
        """
        agent_override = context.get("agent_override")
        if agent_override:
            return agent_override
        return _TASK_AGENT_MAP.get(task_type, "general")

    async def route_task(self, task: Task) -> AgentResponse:
        """Main routing: validate → classify → budget check → select → execute → log.

        Uses existing llm_client.chat() for execution,
        maintaining full compatibility with the current system.

        Pipeline:
        1. Security validation (if SecurityGuard attached)
        2. Task classification (keyword-based, no LLM call)
        3. Budget check (if BudgetManager attached)
        4. Agent + model selection (optionally cost-aware)
        5. Execute with retry
        6. Track cost, log audit, update session
        """
        from llm_client import chat

        start_time = time.monotonic()
        self._total_tasks += 1

        # 1. Security validation
        if self._security:
            try:
                result = self._security.validate(task.description)
                if result.get("blocked"):
                    return AgentResponse(
                        success=False,
                        result=f"Blocked by security: {result.get('reason', 'policy violation')}",
                        agent_name="security_guard",
                        metadata={"blocked": True, "reason": result.get("reason")},
                    )
            except Exception as e:
                logger.warning("Security check failed (proceeding): %s", e)

        # 2. Classify
        task.task_type = self.classify_task(task)

        # 3. Budget check
        if self._budget:
            try:
                budget_status = self._budget.check_budget()
                if not budget_status.get("allowed", True):
                    return AgentResponse(
                        success=False,
                        result=(
                            f"Budget exhausted. "
                            f"Daily: ${budget_status.get('daily_spent', 0):.2f}"
                            f"/${budget_status.get('daily_limit', 0):.2f}"
                        ),
                        agent_name="budget_manager",
                        metadata={"budget_exceeded": True},
                    )
            except Exception as e:
                logger.warning("Budget check failed (proceeding): %s", e)

        # 4. Select agent
        agent_key = self.select_agent_key(task.task_type, task.context)

        # 5. Execute with retry
        response = await self._execute_with_retry(
            task, agent_key, chat, max_retries=task.max_retries,
        )

        # 6. Track
        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        response.execution_time_ms = execution_time_ms

        if response.success:
            self._successful_tasks += 1
        self._total_cost_usd += response.cost_usd

        # 7. Log routing decision
        self._log_routing(task, agent_key, response)

        # 8. Record cost in budget manager
        if self._budget and response.cost_usd > 0:
            try:
                self._budget.record_cost(
                    agent=agent_key,
                    model=response.metadata.get("model", ""),
                    cost_usd=response.cost_usd,
                    tokens_in=response.tokens_used,
                    tokens_out=0,
                    task_type=task.task_type.value if task.task_type else "",
                )
            except Exception:
                pass

        # 9. Record in cost metrics
        if self._cost_metrics:
            try:
                self._cost_metrics.record(
                    agent_name=agent_key,
                    model=response.metadata.get("model", ""),
                    cost_usd=response.cost_usd,
                    tokens_used=response.tokens_used,
                    latency_ms=execution_time_ms,
                )
            except Exception:
                pass

        # 10. Audit log
        if self._audit:
            try:
                await self._audit.log(
                    user_id=task.user_id,
                    agent_name=agent_key,
                    action_type="route_task",
                    success=response.success,
                    cost_usd=response.cost_usd,
                    tokens_used=response.tokens_used,
                    latency_ms=execution_time_ms,
                    metadata={
                        "task_type": task.task_type.value if task.task_type else "",
                        "model": response.metadata.get("model", ""),
                    },
                )
            except Exception:
                pass

        # 11. Track in session
        if self._sessions:
            try:
                self._sessions.track_task(
                    user_id=task.user_id,
                    agent_name=agent_key,
                    model=response.metadata.get("model", ""),
                    cost_usd=response.cost_usd,
                    tokens=response.tokens_used,
                    routing_decision={
                        "task_type": task.task_type.value if task.task_type else "",
                        "agent": agent_key,
                        "success": response.success,
                        "latency_ms": execution_time_ms,
                    },
                )
            except Exception:
                pass

        return response

    async def _execute_with_retry(
        self,
        task: Task,
        agent_key: str,
        chat_fn: Callable,
        max_retries: int = 3,
    ) -> AgentResponse:
        """Execute task with exponential backoff retry."""
        last_error = ""

        for attempt in range(max_retries):
            try:
                thread_id = task.context.get("thread_id")
                result_text, model_used = await chat_fn(
                    task.description,
                    agent_key=agent_key,
                    thread_id=thread_id,
                )

                return AgentResponse(
                    success=True,
                    result=result_text,
                    agent_name=agent_key,
                    metadata={"model": model_used, "attempt": attempt + 1},
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Agent %s attempt %d/%d failed: %s",
                    agent_key, attempt + 1, max_retries, e,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return AgentResponse(
            success=False,
            result=None,
            agent_name=agent_key,
            metadata={"error": last_error, "attempts": max_retries},
        )

    async def route_multi(
        self,
        task: Task,
        agent_keys: List[str],
    ) -> List[AgentResponse]:
        """Execute same task with multiple agents in parallel.

        Returns all responses for comparison/merging.
        """
        from llm_client import chat

        async def _run_one(agent_key: str) -> AgentResponse:
            start = time.monotonic()
            try:
                result, model = await chat(
                    task.description, agent_key=agent_key,
                )
                return AgentResponse(
                    success=True,
                    result=result,
                    agent_name=agent_key,
                    execution_time_ms=int((time.monotonic() - start) * 1000),
                    metadata={"model": model},
                )
            except Exception as e:
                return AgentResponse(
                    success=False,
                    result=str(e),
                    agent_name=agent_key,
                    execution_time_ms=int((time.monotonic() - start) * 1000),
                    metadata={"error": str(e)},
                )

        responses = await asyncio.gather(*[_run_one(ak) for ak in agent_keys])
        return list(responses)

    async def orchestrate_complex(
        self,
        task: Task,
        progress_cb: Optional[Callable[[str], Coroutine]] = None,
    ) -> AgentResponse:
        """Decompose and execute a complex task using orchestrate_engine.

        Delegates to existing tools/orchestrate_engine.py for DAG execution.
        """
        from tools.orchestrate_engine import orchestrate_task

        start = time.monotonic()

        try:
            result = await orchestrate_task(
                task.description,
                progress_cb=progress_cb,
            )
            return AgentResponse(
                success=True,
                result=result,
                agent_name="orchestrator",
                execution_time_ms=int((time.monotonic() - start) * 1000),
                metadata={"type": "orchestrated"},
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                result=str(e),
                agent_name="orchestrator",
                execution_time_ms=int((time.monotonic() - start) * 1000),
                metadata={"error": str(e)},
            )

    def _log_routing(
        self,
        task: Task,
        agent_key: str,
        response: AgentResponse,
    ) -> None:
        """Log routing decision for analytics."""
        entry = {
            "task_id": task.task_id,
            "task_type": task.task_type.value if task.task_type else "unknown",
            "agent": agent_key,
            "success": response.success,
            "cost_usd": response.cost_usd,
            "tokens": response.tokens_used,
            "latency_ms": response.execution_time_ms,
            "model": response.metadata.get("model", ""),
            "timestamp": time.time(),
        }
        self.routing_history.append(entry)

        # Keep last 500 decisions in memory
        if len(self.routing_history) > 500:
            self.routing_history = self.routing_history[-500:]

        logger.info(
            "Routed task=%s type=%s agent=%s success=%s latency=%dms",
            task.task_id,
            entry["task_type"],
            agent_key,
            response.success,
            response.execution_time_ms,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return orchestrator performance statistics."""
        success_rate = (
            self._successful_tasks / self._total_tasks
            if self._total_tasks > 0
            else 0.0
        )

        # Aggregate by agent
        agent_stats: Dict[str, Dict] = {}
        for entry in self.routing_history:
            agent = entry["agent"]
            if agent not in agent_stats:
                agent_stats[agent] = {"count": 0, "success": 0, "total_ms": 0}
            agent_stats[agent]["count"] += 1
            if entry["success"]:
                agent_stats[agent]["success"] += 1
            agent_stats[agent]["total_ms"] += entry["latency_ms"]

        return {
            "total_tasks": self._total_tasks,
            "successful_tasks": self._successful_tasks,
            "success_rate": round(success_rate, 3),
            "total_cost_usd": round(self._total_cost_usd, 4),
            "routing_history_size": len(self.routing_history),
            "agent_stats": agent_stats,
        }

    def format_stats_html(self) -> str:
        """Format stats as HTML for Telegram display."""
        stats = self.get_stats()

        lines = [
            "<b>ChiefOfStaff Orchestrator Stats</b>\n",
            f"Tasks: {stats['total_tasks']} total, "
            f"{stats['successful_tasks']} ok "
            f"({stats['success_rate']*100:.1f}%)",
            f"Cost: ${stats['total_cost_usd']:.4f}",
            "",
        ]

        if stats["agent_stats"]:
            lines.append("<b>Per-Agent:</b>")
            for agent, data in stats["agent_stats"].items():
                avg_ms = data["total_ms"] / data["count"] if data["count"] else 0
                lines.append(
                    f"  <code>{agent}</code>: "
                    f"{data['count']} tasks, "
                    f"{data['success']}/{data['count']} ok, "
                    f"avg {avg_ms:.0f}ms"
                )

        return "\n".join(lines)
