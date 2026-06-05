"""core/integrations/langgraph_orchestrator.py — LangGraph stateful agent orchestration.

Wraps langgraph SDK for stateful multi-step agent graphs.
Single model: MiniMax via litellm (OpenAI-compatible endpoint).

Architecture:
    SwarmBot → LangGraphAgent → MiniMax/OpenAI-compatible API
                   ↓
            MemorySaver (checkpointing)
                   ↓
            ReAct agent loop with tools

Graph types:
    - react_agent: ReAct (Reason + Act + Observe) loop
    - plan_execute: Plan → Execute → Verify

Usage:
    agent = LangGraphAgent(graph_type="react_agent")
    result = await agent.run(task="implement auth system", thread_id="user-123")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "minimax-coding-plan/MiniMax-M3"


class AgentState(TypedDict, total=False):
    messages: list[dict]
    next_action: str
    plan: list[str]
    current_step: int
    task: str
    result: str
    error: str | None


@dataclass
class LangGraphConfig:
    graph_type: str = "react_agent"
    max_steps: int = 20
    max_plan_steps: int = 10
    model: str | None = None
    checkpointer_enabled: bool = True
    tool_calling_mode: str = "auto"


def _configure_minimax_env() -> None:
    """Set environment variables for MiniMax OpenAI-compatible API."""
    os.environ.setdefault("OPENAI_BASE_URL", "https://api.minimax.io/v1")
    os.environ.setdefault("OPENAI_API_KEY", os.getenv("MINIMAX_API_KEY", "dummy"))


class LangGraphAgent:
    """Stateful LangGraph agent with checkpointing via MemorySaver."""

    def __init__(self, config: LangGraphConfig | None = None) -> None:
        self.config = config or LangGraphConfig()
        self.model = self.config.model or DEFAULT_MODEL
        self._agent = None
        self._checkpointer = None
        _configure_minimax_env()

    def _create_llm(self) -> ChatOpenAI:
        """Create a ChatOpenAI instance configured for MiniMax via OpenAI-compatible endpoint."""
        model_name = self.model
        if "/" in model_name:
            model_name = model_name.split("/", 1)[1]
        return ChatOpenAI(
            model=model_name,
            api_key=os.getenv("MINIMAX_API_KEY", "dummy"),  # type: ignore[reportArgumentType]
            base_url="https://api.minimax.io/v1",
            timeout=30.0,
            max_retries=2,
        )

    def _get_tools(self) -> list[dict]:
        """Return tool definitions for the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file at the given path",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the content of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_python",
                    "description": "Execute Python code and return the output",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                        },
                        "required": ["code"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Run a bash command and return stdout/stderr",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search long-term memory for relevant context",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "plan_task",
                    "description": "Create a plan with ordered steps to accomplish a task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "constraints": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["task"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate",
                    "description": "Escalate to human review when task is blocked",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string"},
                            "context": {"type": "string"},
                        },
                        "required": ["reason"],
                    },
                },
            },
        ]

    def _system_prompt(self) -> str:
        base = (
            "You are a LangGraph agent running inside SwarmBot. "
            "You have access to tools: write_file, read_file, run_python, bash, "
            "search_memory, plan_task, escalate. "
            "Use tools to complete tasks. If blocked, escalate. "
            "Think step-by-step. Verify results before reporting done."
        )
        if self.config.graph_type == "plan_execute":
            base += (
                "\n\nPlan before executing. For each step: "
                "1) Plan the step 2) Execute 3) Verify 4) Update plan."
            )
        return base

    async def _setup_agent(self) -> Any:
        """Lazily create the LangGraph react agent."""
        if self._agent is not None:
            return self._agent

        _configure_minimax_env()

        checkpointer = None
        if self.config.checkpointer_enabled:
            try:
                checkpointer = MemorySaver()
                self._checkpointer = checkpointer
                logger.info("LangGraph checkpointer: MemorySaver enabled")
            except Exception as exc:
                logger.warning("Checkpointer unavailable: %s", exc)
                checkpointer = None
                self._checkpointer = None

        try:
            from langchain.agents import create_agent

            self._agent = create_agent(
                model=self._create_llm(),
                tools=self._get_tools(),
                system_prompt=self._system_prompt(),
                checkpointer=checkpointer,
            )
            logger.info("LangGraph agent created: graph_type=%s model=%s checkpointer=%s",
                      self.config.graph_type, self.model, checkpointer is not None)
        except Exception as exc:
            logger.error("Failed to create LangGraph agent: %s", exc)
            raise

        return self._agent

    async def run(self, task: str, thread_id: str | None = None) -> str:
        """Run the agent on a task with optional checkpointing."""
        agent = await self._setup_agent()

        config: dict[str, Any] = {"recursion_limit": self.config.max_steps}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}
        elif self._checkpointer is not None:
            import uuid
            config["configurable"] = {"thread_id": f"default-{uuid.uuid4().hex[:8]}"}

        try:
            result = await agent.ainvoke(
                {"messages": [("user", task)]},
                config,
            )
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                return last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            return "(empty result)"
        except Exception as exc:
            logger.error("LangGraph agent run failed: %s", exc)
            return f"[LangGraph error: {exc}]"

    async def run_plan(self, task: str, thread_id: str | None = None) -> dict[str, Any]:
        """Run plan_execute mode — returns structured plan + execution trace."""
        agent = await self._setup_agent()
        config: dict[str, Any] = {"recursion_limit": self.config.max_plan_steps}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        try:
            result = await agent.ainvoke(
                {
                    "messages": [
                        ("system", self._system_prompt() + "\n\nPlan mode: decompose task into steps."),
                        ("user", task),
                    ]
                },
                config,
            )
            messages = result.get("messages", [])
            return {
                "messages": messages,
                "final": messages[-1].content if messages else "",
            }
        except Exception as exc:
            logger.error("LangGraph plan_execute failed: %s", exc)
            return {"error": str(exc)}


async def run_langgraph_task(
    task: str,
    graph_type: str = "react_agent",
    thread_id: str | None = None,
    max_steps: int = 20,
) -> str:
    """Convenience function for one-off LangGraph agent runs."""
    config = LangGraphConfig(graph_type=graph_type, max_steps=max_steps)
    agent = LangGraphAgent(config)
    return await agent.run(task, thread_id)


async def run_langgraph_plan(
    task: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Convenience for plan_execute mode."""
    config = LangGraphConfig(graph_type="plan_execute", max_steps=15)
    agent = LangGraphAgent(config)
    return await agent.run_plan(task, thread_id)
