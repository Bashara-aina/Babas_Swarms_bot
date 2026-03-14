"""Orchestrator — ChiefOfStaff pattern for multi-agent task routing."""

from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff, Task, TaskType, AgentResponse
from swarms_bot.orchestrator.agent_base import Agent
from swarms_bot.orchestrator.registry import build_agent_registry

__all__ = [
    "ChiefOfStaff",
    "Task",
    "TaskType",
    "AgentResponse",
    "Agent",
    "build_agent_registry",
]
