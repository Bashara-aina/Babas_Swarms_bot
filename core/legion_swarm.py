"""Legion Swarm Orchestrator — multi-agent parallel execution with debate.

Agents: build, deployment-engineer, diff-analyzer, focused-implementer,
paper-wiki-writer, plan, planner, research-agent, reviewer, wikibot, worker

Each agent has a distinct persona and contributes to a 3-phase workflow:
  Phase 1 — Parallel Proposal: all agents propose simultaneously
  Phase 2 — Debate: agents critique and refine each other's work
  Phase 3 — Synthesis: architect agent merges into final recommendation
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class LegionAgentDef:
    key: str
    name: str
    persona: str
    role_description: str


LEGION_TEAM: list[LegionAgentDef] = [
    LegionAgentDef(
        key="build",
        name="Build Engineer",
        persona="You are a world-class build systems engineer. You think in terms of compilation pipelines, dependency graphs, and reproducible builds.",
        role_description="Designs and implements build systems, CI/CD pipelines, and automation scripts.",
    ),
    LegionAgentDef(
        key="deployment-engineer",
        name="Deployment Engineer",
        persona="You are a senior platform engineer specializing in zero-downtime deployments, container orchestration, and infrastructure-as-code.",
        role_description="Plans and executes deployment strategies, containerization, and infrastructure provisioning.",
    ),
    LegionAgentDef(
        key="diff-analyzer",
        name="Diff Analyzer",
        persona="You are an expert code reviewer with an eye for subtle bugs, performance regressions, and security vulnerabilities. You read diffs like poetry.",
        role_description="Analyzes code changes, identifies potential issues, and provides detailed feedback on modifications.",
    ),
    LegionAgentDef(
        key="focused-implementer",
        name="Focused Implementer",
        persona="You are a pragmatic coder who ships. You take ambiguous requirements and turn them into working code. You prefer simple solutions over clever ones.",
        role_description="Implements features and fixes with precision, focusing on correctness and maintainability.",
    ),
    LegionAgentDef(
        key="paper-wiki-writer",
        name="Paper & Wiki Writer",
        persona="You are a technical writer who produces academic-quality documentation. You explain complex systems with clarity and precision.",
        role_description="Writes documentation, technical specifications, and wiki articles.",
    ),
    LegionAgentDef(
        key="plan",
        name="Planner",
        persona="You are a strategic planner who thinks in milestones, dependencies, and risk vectors. You decompose ambiguous goals into actionable roadmaps.",
        role_description="Creates project plans, roadmaps, and task breakdowns with clear dependencies.",
    ),
    LegionAgentDef(
        key="planner",
        name="Senior Planner",
        persona="You are an experienced technical program manager. You see around corners, anticipate blockers, and design realistic timelines.",
        role_description="Develops comprehensive plans with risk assessment and resource allocation.",
    ),
    LegionAgentDef(
        key="research-agent",
        name="Research Agent",
        persona="You are a research scientist who demands evidence. Every claim needs a citation, experiment, or data point. You separate hype from reality.",
        role_description="Researches topics thoroughly, gathers evidence, and provides factual analysis.",
    ),
    LegionAgentDef(
        key="reviewer",
        name="Code Reviewer",
        persona="You are a meticulous code reviewer who cares about correctness, performance, security, and readability. Nothing slips past you.",
        role_description="Reviews code changes, identifies bugs, and ensures quality standards are met.",
    ),
    LegionAgentDef(
        key="wikibot",
        name="Wiki Bot",
        persona="You are the institutional memory keeper. You document decisions, capture lessons learned, and maintain a searchable knowledge base.",
        role_description="Maintains project wiki, documents decisions, and preserves institutional knowledge.",
    ),
    LegionAgentDef(
        key="worker",
        name="Worker Agent",
        persona="You are a reliable executor who gets things done. You execute tasks precisely, report progress clearly, and know when to ask for help.",
        role_description="Executes assigned tasks, reports results, and handles operational work.",
    ),
]


@dataclass
class AgentResult:
    key: str
    name: str
    output: str
    latency_ms: float
    success: bool
    error: str = ""


@dataclass
class SwarmReport:
    phase1_outputs: dict[str, str]
    phase2_outputs: dict[str, str]
    final_synthesis: str
    agent_results: list[AgentResult]
    total_latency_ms: float
    topology_used: str = "legion-swarm"


class LegionSwarmOrchestrator:
    """Parallel multi-agent swarm with 3-phase workflow.

    Phase 1: All agents propose in parallel (asyncio.gather)
    Phase 2: Cross-examination debate rounds
    Phase 3: Synthesis by architect agent
    """

    def __init__(
        self,
        llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
        progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
        debate_rounds: int = 2,
        max_parallel: int = 11,
    ):
        self.llm_call = llm_call
        self.progress_fn = progress_fn
        self.debate_rounds = debate_rounds
        self.max_parallel = max_parallel

    async def _progress(self, msg: str) -> None:
        if self.progress_fn:
            await self.progress_fn(msg)
        logger.info("[LegionSwarm] %s", msg)

    def _get_model_for_agent(self, agent_key: str) -> str:
        from agents import AGENT_MODELS

        return AGENT_MODELS.get(agent_key, AGENT_MODELS.get("general", "minimax/MiniMax-M2.7"))

    def _build_system_prompt(self, agent_def: LegionAgentDef) -> str:
        from agents import PERSONALITY_WRAPPER

        return f"{PERSONALITY_WRAPPER.strip()}\n\n{agent_def.persona}"

    async def _call_agent(
        self,
        agent_def: LegionAgentDef,
        task: str,
        context: str = "",
    ) -> AgentResult:
        started = time.perf_counter()
        system = self._build_system_prompt(agent_def)
        user_msg = f"Task: {task}"
        if context:
            user_msg += f"\n\nAdditional context:\n{context}"
        model = self._get_model_for_agent(agent_def.key)
        try:
            output = await self.llm_call(model, system, user_msg)
            return AgentResult(
                key=agent_def.key,
                name=agent_def.name,
                output=output,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                success=True,
            )
        except Exception as exc:
            logger.warning("Agent %s failed: %s", agent_def.key, exc)
            return AgentResult(
                key=agent_def.key,
                name=agent_def.name,
                output="",
                latency_ms=(time.perf_counter() - started) * 1000.0,
                success=False,
                error=str(exc),
            )

    async def run(self, task: str) -> SwarmReport:
        started = time.perf_counter()
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def _run_with_sem(agent_def: LegionAgentDef, ctx: str = "") -> AgentResult:
            async with semaphore:
                return await self._call_agent(agent_def, task, ctx)

        phase1_outputs: dict[str, str] = {}

        # ── PHASE 1: Parallel Proposal ──────────────────────────────────────────
        await self._progress(f"🧠 Phase 1/3 — {len(LEGION_TEAM)} agents proposing in parallel...")

        phase1_tasks = [_run_with_sem(agent_def) for agent_def in LEGION_TEAM]
        phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)

        for agent_def, result in zip(LEGION_TEAM, phase1_results):
            if isinstance(result, Exception):
                phase1_outputs[agent_def.key] = f"[Error: {result}]"
            else:
                phase1_outputs[agent_def.key] = result.output if isinstance(result, AgentResult) else str(result)

        # ── PHASE 2: Debate Rounds ───────────────────────────────────────────────
        await self._progress(f"🔥 Phase 2/3 — {self.debate_rounds} debate round(s)...")

        phase2_outputs: dict[str, str] = {}
        current_proposals = dict(phase1_outputs)

        for round_num in range(self.debate_rounds):
            await self._progress(f"  Debate round {round_num + 1}/{self.debate_rounds}...")

            debate_contexts = []
            for agent_def in LEGION_TEAM:
                others_text = "\n\n".join(
                    f"[{key}]: {prop}" for key, prop in current_proposals.items() if key != agent_def.key
                )
                debate_contexts.append(
                    f"You are {agent_def.name}.\n"
                    f"Task: {task}\n\n"
                    f"Your initial proposal:\n{current_proposals[agent_def.key]}\n\n"
                    f"Other agents' proposals:\n{others_text}\n\n"
                    f"Critique the strongest weaknesses in other proposals and refine your own. "
                    f"Keep what's strong, fix what's weak. Respond with your refined position."
                )

            round_tasks = [_run_with_sem(agent_def, ctx) for agent_def, ctx in zip(LEGION_TEAM, debate_contexts)]
            round_results = await asyncio.gather(*round_tasks, return_exceptions=True)

            for agent_def, result in zip(LEGION_TEAM, round_results):
                if isinstance(result, Exception):
                    current_proposals[agent_def.key] = current_proposals.get(agent_def.key, "")
                else:
                    current_proposals[agent_def.key] = result.output if isinstance(result, AgentResult) else str(result)

        phase2_outputs = dict(current_proposals)

        # ── PHASE 3: Synthesis ─────────────────────────────────────────────────
        await self._progress("🏆 Phase 3/3 — Synthesizing final recommendation...")

        all_proposals_text = "\n\n".join(
            f"=== {LEGION_TEAM[i].name} ({LEGION_TEAM[i].key}) ===\n{output}"
            for i, output in enumerate(phase1_outputs.values())
        )
        refined_text = "\n\n".join(
            f"=== {LEGION_TEAM[i].name} ({LEGION_TEAM[i].key}) ===\n{output}"
            for i, output in enumerate(phase2_outputs.values())
        )

        synth_system = (
            "You are the Chief Architect. You have witnessed a multi-agent debate where "
            "11 specialized agents proposed and refined their solutions.\n\n"
            "Your job: Synthesize all proposals into ONE coherent, actionable recommendation.\n"
            "Format your response as:\n"
            "## Summary\n[2-3 sentence overview]\n\n"
            "## Key Decisions\n[bullet points of major decisions with reasoning]\n\n"
            "## Implementation Plan\n[numbered steps]\n\n"
            "## Risks & Mitigations\n[potential issues and how to address them]"
        )

        synth_msg = (
            f"Original task: {task}\n\n"
            f"=== INITIAL PROPOSALS ===\n{all_proposals_text}\n\n"
            f"=== POST-DEBATE REFINEMENTS ===\n{refined_text}\n\n"
            f"Synthesize the strongest elements from all proposals into one optimal solution."
        )

        try:
            final_synthesis = await self.llm_call(
                "minimax/MiniMax-M2.7",
                synth_system,
                synth_msg,
            )
        except Exception as exc:
            logger.warning("Synthesis failed: %s", exc)
            final_synthesis = (
                f"[Synthesis failed: {exc}]\n\nBest initial proposal:\n{max(phase2_outputs.values(), key=len)}"
            )

        # Build agent results
        agent_results: list[AgentResult] = []
        for agent_def in LEGION_TEAM:
            result = AgentResult(
                key=agent_def.key,
                name=agent_def.name,
                output=phase2_outputs.get(agent_def.key, ""),
                latency_ms=0.0,
                success=True,
            )
            agent_results.append(result)

        return SwarmReport(
            phase1_outputs=phase1_outputs,
            phase2_outputs=phase2_outputs,
            final_synthesis=final_synthesis,
            agent_results=agent_results,
            total_latency_ms=(time.perf_counter() - started) * 1000.0,
            topology_used="legion-swarm",
        )


async def run_legion_swarm(
    task: str,
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> SwarmReport:
    """Convenience function to run the Legion swarm."""

    async def llm_call(model: str, system: str, user: str) -> str:
        from llm_client import chat

        result, _ = await chat(user, agent_key="general", system_prompt=system)
        return result

    orchestrator = LegionSwarmOrchestrator(llm_call=llm_call, progress_fn=progress_fn)
    return await orchestrator.run(task)
