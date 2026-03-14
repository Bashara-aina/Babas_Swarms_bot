"""Agent base class — standard interface for all specialized agents.

Every agent implements execute() and optionally get_cost_estimate().
Agents are registered in the AgentRegistry and routed by ChiefOfStaff.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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


class Agent(ABC):
    """Base interface for all specialized agents.

    Subclasses must implement execute(). The agent receives a Task
    and returns an AgentResponse with results, cost, and metadata.
    """

    def __init__(
        self,
        name: str,
        agent_key: str,
        model_config: Dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.agent_key = agent_key
        self.model_config = model_config or {}
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, task: "Task") -> AgentResponse:
        """Execute a task and return a response.

        Must be implemented by all agent subclasses.
        """
        ...

    async def get_cost_estimate(self, task: "Task") -> float:
        """Estimate cost before execution (optional override)."""
        estimated_tokens = len(task.description.split()) * 2
        price_per_token = self.model_config.get("price_per_token", 0.000001)
        return estimated_tokens * price_per_token

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.agent_key})>"
