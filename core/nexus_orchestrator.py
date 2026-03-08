"""
Nexus Orchestrator — 3-layer intelligent routing + task execution.

Extends the existing confirmation-queue / monitor logic from task_orchestrator_old.py.
Adds three routing layers:
  Layer 1: Keyword matching (routing_keywords.yaml, fast, O(1))
  Layer 2: Semantic embeddings (sentence-transformers, local)
  Layer 3: LLM fallback (local Gemma3:12b, last resort)

Public API
----------
nexus.route(task)                 → RoutingDecision
nexus.route_to_dept(dept, task)   → RoutingDecision  (used by /dept)
nexus.execute_task(decision, ...) → str
nexus.run_swarm(task, ...)        → str              (used by /swarm)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from core.agent_registry import (
    AGENT_REGISTRY,
    AgentDef,
    agents_by_department,
    get_agent,
    get_department_default,
    list_all_departments,
    search_by_capability,
    semantic_search,
)

if TYPE_CHECKING:
    from aiogram.types import Message

# ---------------------------------------------------------------------------
# Re-export legacy task_orchestrator API so existing call-sites continue to work
# ---------------------------------------------------------------------------
try:
    from core.task_orchestrator_old import (  # type: ignore
        TaskStep,
        PendingConfirmation,
        MonitorTask,
        execute_chain,
        queue_confirmation,
        confirm_action,
        deny_action,
        list_pending,
        start_monitor,
        cancel_monitor,
        list_monitors,
        make_loss_spike_detector,
        _pending,
    )
except Exception:
    pass  # old module may not be present in all deployments

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class RoutingDecision:
    """Result of a routing determination."""

    agent: AgentDef
    confidence: float  # 0.0–1.0
    method: str        # "keyword" | "semantic" | "llm_fallback" | "department_override" | "manual_override"
    reasoning: str     # human-readable explanation


# ---------------------------------------------------------------------------
# Nexus Orchestrator
# ---------------------------------------------------------------------------

class NexusOrchestrator:
    """Central routing coordinator for Babas Agency Swarm."""

    KEYWORD_THRESHOLD = 2      # min keyword score for Layer 1 acceptance
    SEMANTIC_THRESHOLD = 0.55  # min cosine similarity for Layer 2 acceptance

    def __init__(self) -> None:
        kw_path = Path("config/routing_keywords.yaml")
        if kw_path.exists():
            with kw_path.open() as f:
                self._keyword_map: dict[str, list[str]] = yaml.safe_load(f) or {}
        else:
            logger.warning("routing_keywords.yaml not found — Layer 1 disabled")
            self._keyword_map = {}

    # ─── Public routing API ─────────────────────────────────────────────────

    async def route(self, task: str) -> RoutingDecision:
        """Cascade through 3 routing layers and return the best agent."""

        decision = await self._layer1_keyword(task)
        if decision:
            logger.debug(
                "Layer 1 (keyword): %s (confidence=%.2f)", decision.agent.name, decision.confidence
            )
            return decision

        decision = await self._layer2_semantic(task)
        if decision:
            logger.debug(
                "Layer 2 (semantic): %s (confidence=%.2f)", decision.agent.name, decision.confidence
            )
            return decision

        decision = await self._layer3_llm(task)
        logger.debug(
            "Layer 3 (LLM fallback): %s (confidence=%.2f)", decision.agent.name, decision.confidence
        )
        return decision

    async def route_to_dept(self, dept: str, task: str) -> RoutingDecision:
        """Skip all routing layers; use the department's default agent."""
        agent = get_department_default(dept)
        if not agent:
            agents = agents_by_department(dept)
            agent = agents[0] if agents else self._fallback_agent()

        return RoutingDecision(
            agent=agent,
            confidence=1.0,
            method="department_override",
            reasoning=f"Manual department selection: {dept}",
        )

    # ─── Task execution ──────────────────────────────────────────────────────

    async def execute_task(
        self,
        decision: RoutingDecision,
        task: str,
        message: Optional["Message"] = None,
        stream: bool = True,
    ) -> str:
        """Execute task with the selected agent, using full fallback chain."""
        logger.info(
            "Executing with %s (%s, conf=%.2f)",
            decision.agent.name,
            decision.method,
            decision.confidence,
        )

        # Build system prompt
        system_prompt = self._build_system_prompt(decision.agent, task)

        # Try primary model first, then fallbacks
        model_ids = [decision.agent.primary_model_id] + decision.agent.fallback_model_ids

        last_error: Optional[Exception] = None
        for model_id in model_ids:
            if not model_id:
                continue
            try:
                result = await self._call_model(model_id, system_prompt, task)
                return result
            except Exception as exc:
                logger.warning("Model %s failed: %s — trying next fallback", model_id, exc)
                last_error = exc

        error_msg = str(last_error) if last_error else "All models failed"
        return f"❌ Error executing task: {error_msg}"

    # ─── Swarm mode ──────────────────────────────────────────────────────────

    async def run_swarm(
        self,
        task: str,
        message: Optional["Message"] = None,
        pattern: str = "auto",
    ) -> str:
        """Delegate to supervisor.orchestrate() for multi-agent collaboration."""
        try:
            from core.orchestration.supervisor import orchestrate  # type: ignore

            result = await orchestrate(task=task, message=message)
            return result
        except ImportError:
            # Supervisor not yet fully wired — run 3-agent parallel fallback
            return await self._simple_swarm(task)
        except Exception as exc:
            logger.error("Swarm execution failed: %s", exc)
            return f"❌ Swarm error: {exc}"

    # ─── Layer implementations ───────────────────────────────────────────────

    async def _layer1_keyword(self, task: str) -> Optional[RoutingDecision]:
        """Keyword matching using routing_keywords.yaml."""
        if not self._keyword_map:
            return None

        task_lower = task.lower()
        found_keywords = [kw for kw in self._keyword_map if kw in task_lower]

        if not found_keywords:
            return None

        results = search_by_capability(found_keywords)
        if not results:
            return None

        agent_name, score = results[0]
        if score < self.KEYWORD_THRESHOLD:
            return None

        agent = get_agent(agent_name)
        if not agent:
            return None

        confidence = min(score / 8.0, 1.0)
        return RoutingDecision(
            agent=agent,
            confidence=confidence,
            method="keyword",
            reasoning=f"Matched keywords: {', '.join(found_keywords[:5])}",
        )

    async def _layer2_semantic(self, task: str) -> Optional[RoutingDecision]:
        """Sentence-transformer semantic similarity search."""
        results = semantic_search(task, top_k=3)
        if not results:
            return None

        agent_name, similarity = results[0]
        if similarity < self.SEMANTIC_THRESHOLD:
            return None

        agent = get_agent(agent_name)
        if not agent:
            return None

        return RoutingDecision(
            agent=agent,
            confidence=similarity,
            method="semantic",
            reasoning=f"Semantic similarity: {similarity:.3f}",
        )

    async def _layer3_llm(self, task: str) -> RoutingDecision:
        """Ask local Gemma3:12b which department should handle the task."""
        dept_list = "\n".join(f"- {d}" for d in list_all_departments())
        prompt = (
            "You are a task router. Given a user task, choose ONE department.\n\n"
            f"Departments:\n{dept_list}\n\n"
            f"Task: \"{task}\"\n\n"
            "Respond with ONLY the department name (snake_case, no other text)."
        )

        dept_name = "engineering"  # ultimate fallback
        try:
            raw = await self._call_model(
                "ollama_chat/qwen3.5:35b", "", prompt, max_tokens=15
            )
            candidate = raw.strip().lower().replace(" ", "_").replace("-", "_")
            if candidate in AGENT_REGISTRY or candidate in list_all_departments():
                dept_name = candidate
        except Exception as exc:
            logger.warning("Layer 3 LLM routing failed: %s", exc)

        agent = get_department_default(dept_name) or self._fallback_agent()
        return RoutingDecision(
            agent=agent,
            confidence=0.65,
            method="llm_fallback",
            reasoning=f"LLM routed to department: {dept_name}",
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _build_system_prompt(self, agent: AgentDef, task: str) -> str:
        """Load Jinja2 template or return a default system prompt."""
        tmpl_path = Path(agent.prompt_template)
        try:
            if tmpl_path.exists():
                from jinja2 import Environment, FileSystemLoader  # type: ignore

                env = Environment(
                    loader=FileSystemLoader(str(tmpl_path.parent)),
                    autoescape=False,
                )
                tmpl = env.get_template(tmpl_path.name)
                return tmpl.render(
                    role=agent.name.replace("_", " ").title(),
                    department=agent.department.replace("_", " ").title(),
                    role_description=agent.description,
                    capabilities=agent.capabilities,
                    tools=agent.tools,
                    task=task,
                    context="",
                )
        except Exception as exc:
            logger.debug("Template load failed (%s): %s", tmpl_path, exc)

        # Default prompt when template missing
        return (
            f"You are {agent.name.replace('_', ' ')} in the "
            f"{agent.department.replace('_', ' ')} department. "
            f"{agent.description} "
            "Think step-by-step. Be precise and practical."
        )

    async def _call_model(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
    ) -> str:
        """Call any LiteLLM-compatible model asynchronously."""
        try:
            import litellm  # type: ignore

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: litellm.completion(
                    model=model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                ),
            )
            content: str = response.choices[0].message.content or ""
            return content.strip()

        except Exception as exc:
            raise RuntimeError(f"LiteLLM call failed for {model_id}: {exc}") from exc

    async def _simple_swarm(self, task: str) -> str:
        """Minimal parallel swarm: 3 best keyword-matched agents collaborate."""
        results_raw = search_by_capability(task.lower().split()[:5])
        top_agents = [
            get_agent(name)
            for name, _ in results_raw[:3]
            if get_agent(name) is not None
        ]
        if not top_agents:
            top_agents = [self._fallback_agent()]

        async def _run(agent: AgentDef) -> str:
            system_prompt = self._build_system_prompt(agent, task)
            try:
                return await self._call_model(
                    agent.primary_model_id, system_prompt, task
                )
            except Exception as exc:
                return f"[{agent.name} error: {exc}]"

        responses = await asyncio.gather(*[_run(a) for a in top_agents])
        parts = [
            f"**{a.name}** ({a.department}):\n{r}"
            for a, r in zip(top_agents, responses)
        ]
        return "\n\n---\n\n".join(parts)

    def _fallback_agent(self) -> AgentDef:
        """Absolute last-resort agent (first engineering agent)."""
        eng = agents_by_department("engineering")
        if eng:
            return eng[0]
        # Return any agent
        return next(iter(AGENT_REGISTRY.values()))


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

nexus = NexusOrchestrator()
