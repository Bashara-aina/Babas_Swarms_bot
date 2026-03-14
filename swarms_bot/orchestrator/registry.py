"""Agent registry builder — creates LLM-backed agents from existing config.

Wraps the existing agents.py / core/agent_registry.py infrastructure
into Agent instances that the ChiefOfStaff can route to.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from swarms_bot.orchestrator.agent_base import Agent, AgentResponse

logger = logging.getLogger(__name__)


class LLMAgent(Agent):
    """Agent backed by llm_client.chat() — wraps existing infrastructure.

    Each LLMAgent maps to an agent_key in agents.py (coding, debug, etc.)
    and delegates execution to the existing chat() function with fallback chains.
    """

    async def execute(self, task: "Task") -> AgentResponse:
        """Execute task using llm_client.chat()."""
        from llm_client import chat

        start = time.monotonic()
        try:
            thread_id = task.context.get("thread_id")
            result, model = await chat(
                task.description,
                agent_key=self.agent_key,
                thread_id=thread_id,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

            return AgentResponse(
                success=True,
                result=result,
                agent_name=self.name,
                execution_time_ms=elapsed_ms,
                metadata={"model": model, "agent_key": self.agent_key},
            )
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            self.logger.error("Execution failed: %s", e)
            return AgentResponse(
                success=False,
                result=str(e),
                agent_name=self.name,
                execution_time_ms=elapsed_ms,
                metadata={"error": str(e), "agent_key": self.agent_key},
            )


class AgenticLoopAgent(Agent):
    """Agent that uses the full agentic tool-calling loop.

    For tasks requiring computer control (screenshots, clicks, commands).
    """

    async def execute(self, task: "Task") -> AgentResponse:
        from llm_client import agent_loop

        start = time.monotonic()
        try:
            thread_id = task.context.get("thread_id")
            result, model = await agent_loop(
                task.description,
                max_iterations=task.context.get("max_iterations", 15),
                thread_id=thread_id,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AgentResponse(
                success=True,
                result=result,
                agent_name=self.name,
                execution_time_ms=elapsed_ms,
                metadata={"model": model, "agent_key": self.agent_key},
            )
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AgentResponse(
                success=False,
                result=str(e),
                agent_name=self.name,
                execution_time_ms=elapsed_ms,
                metadata={"error": str(e)},
            )


class CodeReviewAgent(Agent):
    """Specialized code review agent using tools/code_reviewer.py."""

    async def execute(self, task: "Task") -> AgentResponse:
        from tools.code_reviewer import review_code, review_file

        start = time.monotonic()
        try:
            file_path = task.context.get("file_path")
            review_type = task.context.get("review_type", "general")

            if file_path:
                result = await review_file(file_path, review_type=review_type)
            else:
                code = task.context.get("code", task.description)
                language = task.context.get("language", "python")
                result = await review_code(
                    code, language=language, review_type=review_type,
                )

            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AgentResponse(
                success=True,
                result=result,
                agent_name=self.name,
                execution_time_ms=elapsed_ms,
                metadata={"review_type": review_type},
            )
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AgentResponse(
                success=False,
                result=str(e),
                agent_name=self.name,
                execution_time_ms=elapsed_ms,
                metadata={"error": str(e)},
            )


def build_agent_registry() -> Dict[str, Agent]:
    """Build the full agent registry from existing config.

    Creates Agent instances for each agent key in agents.py,
    plus specialized agents for code review and computer control.
    """
    agents: Dict[str, Agent] = {}

    # Standard LLM agents (map to existing agent keys)
    standard_keys = [
        ("coding", "Code Generator"),
        ("debug", "Debugger"),
        ("math", "Math Expert"),
        ("architect", "System Architect"),
        ("analyst", "Data Analyst"),
        ("researcher", "Researcher"),
        ("general", "General Assistant"),
        ("marketer", "Content Marketer"),
        ("devops", "DevOps Engineer"),
        ("pm", "Project Manager"),
        ("humanizer", "Text Humanizer"),
        ("reviewer", "Code Reviewer (LLM)"),
    ]

    for agent_key, name in standard_keys:
        agents[agent_key] = LLMAgent(
            name=name,
            agent_key=agent_key,
        )

    # Specialized agents
    agents["computer"] = AgenticLoopAgent(
        name="Computer Controller",
        agent_key="computer",
    )
    agents["code_review"] = CodeReviewAgent(
        name="Code Review Pipeline",
        agent_key="coding",
    )

    logger.info("Built agent registry: %d agents", len(agents))
    return agents
