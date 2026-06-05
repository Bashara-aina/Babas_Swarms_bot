"""core/integrations/crewai_orchestrator.py — crewAI multi-agent orchestration.

crewAI provides role-based agent delegation (planner/worker/reviewer).
This integrates crewAI 1.14+ agents with SwarmBot's litellm/MiniMax infrastructure.

Usage:
    crew = SwarmBotCrew()
    crew.add_agent("researcher", "Research latest AI trends", role="researcher")
    crew.add_agent("writer", "Write summary of findings", role="writer")
    result = await crew.kickoff("AI trends in 2026")
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "minimax-coding-plan/MiniMax-M3"


class SwarmBotCrew:
    """crewAI 1.14+ wrapper with MiniMax support via litellm."""

    def __init__(self, agents: list[dict] | None = None, verbose: bool = False) -> None:
        self.agents_def = agents or []
        self.verbose = verbose
        self._crew = None

    def add_agent(
        self,
        role: str,
        goal: str,
        backstory: str = "",
        allow_delegation: bool = False,
        max_iter: int = 5,
    ) -> None:
        """Add an agent definition to the crew."""
        self.agents_def.append({
            "role": role,
            "goal": goal,
            "backstory": backstory or f"You are a {role} agent. Complete tasks accurately.",
            "allow_delegation": allow_delegation,
            "max_iter": max_iter,
        })

    def _build_llm(self) -> Any:
        """Build LLM instance for crewAI 1.14+ using the LLM class."""
        from crewai import LLM
        return LLM(
            model=DEFAULT_MODEL,
            api_key=os.getenv("MINIMAX_API_KEY", "dummy"),
            base_url="https://api.minimax.io/v1",
        )

    def _build_agents(self) -> list[Any]:
        """Build crewAI Agent instances from agent definitions."""
        from crewai import Agent

        crew_agents = []
        llm = self._build_llm()
        for ag in self.agents_def:
            try:
                agent = Agent(
                    role=ag["role"],
                    goal=ag["goal"],
                    backstory=ag.get("backstory", ""),
                    verbose=self.verbose,
                    allow_delegation=ag.get("allow_delegation", False),
                    max_iter=ag.get("max_iter", 5),
                    llm=llm,
                )
                crew_agents.append(agent)
            except Exception as exc:
                logger.warning("crewAI agent creation failed for role %s: %s", ag.get("role"), exc)
        return crew_agents

    async def kickoff(self, task: str) -> str:
        """Run the crew on a task."""
        try:
            from crewai import Crew, Task
        except ImportError:
            return "[crewAI not installed — pip install crewai]"

        crew_agents = self._build_agents()
        if not crew_agents:
            return "[no crewAI agents created]"

        task_obj = Task(
            description=task,
            expected_output="A comprehensive response addressing the task.",
            agent=crew_agents[0],
        )

        try:
            crew = Crew(
                agents=crew_agents,
                tasks=[task_obj],
                verbose=self.verbose,
            )
            result = await crew.kickoff_async()
            if hasattr(result, "raw"):
                return result.raw  # type: ignore[reportAttributeAccessIssue]
            return str(result)
        except Exception as exc:
            logger.error("crewAI kickoff failed: %s", exc)
            return f"[crewAI error: {exc}]"

    async def kickoff_with_tasks(self, tasks: list[dict[str, str]]) -> str:
        """Run crew with explicit task list."""
        try:
            from crewai import Crew, Task
        except ImportError:
            return "[crewAI not installed — pip install crewai]"

        crew_agents = self._build_agents()
        if not crew_agents:
            return "[no crewAI agents created]"

        task_objs = []
        for i, t in enumerate(tasks):
            task_objs.append(Task(
                description=t.get("description", t.get("task", "")),
                expected_output=t.get("expected_output", "Complete output."),
                agent=crew_agents[min(i, len(crew_agents) - 1)],
            ))

        try:
            crew = Crew(
                agents=crew_agents,
                tasks=task_objs,
                verbose=self.verbose,
            )
            result = await crew.kickoff()  # type: ignore[reportGeneralTypeIssues]
            return str(result) if result else "(empty crew result)"
        except Exception as exc:
            logger.error("crewAI kickoff_with_tasks failed: %s", exc)
            return f"[crewAI error: {exc}]"


async def run_crewai_task(
    task: str,
    agents: list[dict[str, str]],
    verbose: bool = False,
) -> str:
    """Convenience function for one-off crewAI runs.

    Args:
        task: The task to assign to the crew
        agents: List of agent configs [{"role": "...", "goal": "...", "backstory": "..."}]
        verbose: Enable crewAI verbose logging
    """
    crew = SwarmBotCrew(agents=agents, verbose=verbose)
    return await crew.kickoff(task)


class RumahLabuhCrew:
    """Pre-configured crew for RumahLabuh business operations."""

    @staticmethod
    async def run_business_analysis(topic: str) -> str:
        """Run RumahLabuh business analysis crew."""
        agents = [
            {
                "role": "researcher",
                "goal": f"Research {topic} for RumahLabuh context. Provide data-backed insights.",
                "backstory": "You are a business researcher specializing in Indonesian context.",
            },
            {
                "role": "analyst",
                "goal": "Analyze research findings and identify opportunities.",
                "backstory": "You are a strategic analyst for business operations.",
            },
            {
                "role": "writer",
                "goal": "Write clear, actionable summary of analysis.",
                "backstory": "You write professional business reports.",
            },
        ]
        return await run_crewai_task(
            task=f"Analyze {topic} for RumahLabuh: identify opportunities, risks, and recommendations.",
            agents=agents,
        )
