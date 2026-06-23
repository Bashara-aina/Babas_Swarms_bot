"""
Swarm-inspired agent handoff for Legion.
Preserves full context across agent boundaries when routing between specialists.

Problem solved: When Legion routes a task from one agent to another,
context was being lost. SwarmHandoff preserves:
  - original_task
  - accumulated_context
  - handoff_reason
  - urgency level
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HandoffTarget(Enum):
    """Known agent targets for handoff routing."""

    CODING = "coding"
    RESEARCH = "research"
    DEBATE = "debate"
    BROWSER = "browser"
    REVIEW = "reviewer"
    GENERAL = "general"


@dataclass
class HandoffResult:
    """Result of a handoff decision."""

    target: HandoffTarget
    context: dict[str, Any]
    reason: str
    urgency: str = "normal"


class SwarmHandoff:
    """
    Manages agent-to-agent handoffs with full context preservation.
    Currently integrated into nexus_orchestrator.py route() method.
    """

    def __init__(self):
        self._handoff_log: list[HandoffResult] = []
        self._pending_handoff: HandoffResult | None = None

    def request_handoff(
        self,
        from_agent: str,
        to_target: HandoffTarget,
        context: dict[str, Any],
        reason: str,
        urgency: str = "normal",
    ) -> HandoffResult:
        """
        Request a handoff from one agent to another.
        Call this before routing to preserve full context.
        """
        result = HandoffResult(
            target=to_target,
            context={
                "source_agent": from_agent,
                "original_task": context.get("original_task", ""),
                "accumulated_context": context,
                "handoff_reason": reason,
                "urgency": urgency,
            },
            reason=reason,
            urgency=urgency,
        )
        self._handoff_log.append(result)
        self._pending_handoff = result
        return result

    def get_pending_handoff(self) -> HandoffResult | None:
        """Get the currently pending handoff, if any."""
        return self._pending_handoff

    def clear_pending_handoff(self) -> None:
        """Clear the pending handoff after it's been executed."""
        self._pending_handoff = None

    def get_handoff_history(self) -> list[HandoffResult]:
        """Get all handoffs in this session."""
        return list(self._handoff_log)

    def should_handoff(
        self, current_agent: str, target: HandoffTarget
    ) -> bool:
        """
        Determine if a handoff should happen.
        Override this for custom routing logic.
        """
        return (
            self._pending_handoff is not None
            and self._pending_handoff.target == target
        )
