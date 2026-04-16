"""M2.7 Drift Detector — error accumulation prevention.

Monitors whether current work has drifted from the original goal.
Today's LLM failures in long agentic runs are NOT intelligence failures —
they are ERROR ACCUMULATION (Facebook AI research, 2025).

This module implements drift detection checkpoints every 5 tool calls:
  1. ORIGINAL GOAL: [restate exactly]
  2. CURRENT STATE: [what is actually true]
  3. DELTA CHECK: [is current state moving toward original goal?]

RED FLAGS that trigger ABORT:
  ✗ Work no longer connects to original task
  ✗ "Temporary fix" has become the permanent approach
  ✗ Scope has silently expanded beyond original request
  ✗ An assumption made early has been invalidated by new information
  ✗ The solution is more complex than the problem requires

Reference: M2.7 Full Capability Activation — Error Accumulation Prevention (Section E3)
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from core.context_health import HealthLevel


# ---------------------------------------------------------------------------
# Drift report
# ---------------------------------------------------------------------------


class DriftStatus(str, Enum):
    OK = "OK"           # On track
    DRIFTING = "DRIFTING"  # Some concern
    ABORT = "ABORT"     # Critical drift — stop


@dataclass
class DriftReport:
    """Result of drift detection check."""

    status: DriftStatus
    original_goal: str
    current_state: str
    delta_assessment: str
    red_flags: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    checked_at: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()
    )


# ---------------------------------------------------------------------------
# Drift Detector
# ---------------------------------------------------------------------------


class DriftDetector:
    """Error accumulation prevention — tracks whether work stays on goal.

    Usage:
        detector = DriftDetector()

        # At task start:
        detector.set_goal("Add /budget command to show API spend")

        # After every 5 tool calls (or every major step):
        report = detector.check_drift()
        if detector.should_abort():
            detector.raise_abort()

        # Track state changes:
        detector.add_state("Modified handlers/admin.py — added BudgetHandler")
        detector.add_state("Modified swarms_bot/routing/budget_manager.py — added spend tracking")
    """

    def __init__(self) -> None:
        self.original_goal: Optional[str] = None
        self.accumulated_state: list[str] = []
        self.tool_call_count: int = 0
        self.last_check_at: Optional[str] = None
        self._aborted: bool = False

    def set_goal(self, goal: str) -> None:
        """Set the original goal (call at task start)."""
        self.original_goal = goal
        self.accumulated_state = []
        self.tool_call_count = 0
        self._aborted = False
        self.last_check_at = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()

    def add_state(self, state_description: str) -> None:
        """Record a state change (call after each file modification or significant action)."""
        if self.original_goal is None:
            raise RuntimeError("Must call set_goal() before add_state()")
        self.accumulated_state.append(state_description)

    def increment_tool_calls(self, count: int = 1) -> None:
        """Increment tool call counter."""
        self.tool_call_count += count

    def check_drift(self) -> DriftReport:
        """Run drift detection check.

        Returns DriftReport with status, red flags, and recommendations.
        Call this every 5 tool calls or after each major step.
        """
        if self.original_goal is None:
            return DriftReport(
                status=DriftStatus.OK,
                original_goal="(no goal set)",
                current_state="(no state)",
                delta_assessment="No goal set — cannot assess drift.",
            )

        self.last_check_at = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat()

        red_flags: list[str] = []
        recommendations: list[str] = []

        # Build current state summary
        state_entries = self.accumulated_state[-5:]
        state_parts = [
            f"[{len(self.accumulated_state)} state changes recorded]"
        ]
        for i, s in enumerate(state_entries):
            state_parts.append(f"  {i+1}. {s}")
        current_state = "\n".join(state_parts)


        # Check 1: Is work connected to original goal?
        goal_lower = self.original_goal.lower()
        state_text = " ".join(s.lower() for s in self.accumulated_state)

        # Extract key nouns from goal
        goal_keywords = set(
            w for w in goal_lower.split()
            if len(w) > 4 and w not in {"which", "where", "there", "their", "would", "should", "could"}
        )

        if goal_keywords:
            overlap = goal_keywords & set(state_text.split())
            if len(overlap) < 2 and len(self.accumulated_state) > 2:
                red_flags.append(
                    "Work no longer connects to original goal — "
                    "low keyword overlap between goal and current state."
                )
                recommendations.append("Return to original goal scope or formally redefine it.")

        # Check 2: Has "temporary fix" become permanent?
        temp_fix_indicators = ["hack", "workaround", "TODO", " FIXME", "HACK", "quick fix"]
        temp_count = sum(1 for s in self.accumulated_state for t in temp_fix_indicators if t in s)
        if temp_count > 2:
            red_flags.append(
                f"Multiple temporary fixes ({temp_count}) accumulated — "
                "risk of permanent technical debt."
            )
            recommendations.append("Flag temporary fixes explicitly in next checkpoint.")

        # Check 3: Has scope expanded?
        scope_expand_indicators = ["also ", "additionally", "while we're at it", "might as well"]
        scope_expands = sum(
            1 for s in self.accumulated_state for kw in scope_expand_indicators if kw in s.lower()
        )
        if scope_expands > 3:
            red_flags.append(
                f"Silent scope expansion detected ({scope_expands} instances) — "
                "original task may be lost."
            )
            recommendations.append("Freeze scope. Log expanded scope for next session.")

        # Check 4: Is solution more complex than problem?
        if len(self.accumulated_state) > 12:
            red_flags.append(
                f"Solution has grown to {len(self.accumulated_state)} state changes — "
                "may be over-engineered."
            )
            recommendations.append(
                "Question: is every state change essential? "
                "Can it be done in fewer files/steps?"
            )

        # Determine status
        if red_flags:
            # Count critical red flags (first 3 types above are critical)
            critical_count = sum(
                1 for rf in red_flags
                if any(
                    kw in rf
                    for kw in ["no longer connects", "temporary fix", "scope expansion"]
                )
            )
            if critical_count >= 2:
                status = DriftStatus.ABORT
            else:
                status = DriftStatus.DRIFTING
        else:
            status = DriftStatus.OK

        # Build delta assessment
        if status == DriftStatus.OK:
            delta = f"On track — {len(self.accumulated_state)} state changes, goal maintained."
        elif status == DriftStatus.DRIFTING:
            delta = f"Drifting — {len(red_flags)} concern(s) flagged."
        else:
            delta = f"CRITICAL DRIFT — {len(red_flags)} red flag(s). Recommend abort."

        return DriftReport(
            status=status,
            original_goal=self.original_goal,
            current_state=current_state,
            delta_assessment=delta,
            red_flags=red_flags,
            recommendations=recommendations,
        )

    def should_abort(self) -> bool:
        """Return True if drift is critical — should stop current approach."""
        report = self.check_drift()
        return report.status == DriftStatus.ABORT

    def raise_abort(self) -> None:
        """Raise exception if critical drift detected."""
        report = self.check_drift()
        if report.status == DriftStatus.ABORT:
            self._aborted = True
            raise DriftAbortError(
                f"DRIFT ABORT: {report.delta_assessment}\n"
                + "\n".join(f"  ⚠️ {rf}" for rf in report.red_flags)
                + "\nRealign to original goal or formally redefine scope."
            )

    def get_tool_calls_since_checkpoint(self) -> int:
        """Return number of tool calls since last drift check."""
        return self.tool_call_count

    def format_drift_summary(self) -> str:
        """Format a one-line drift summary for CLAUDE.md reporting."""
        report = self.check_drift()
        emoji = {
            DriftStatus.OK: "🟢",
            DriftStatus.DRIFTING: "🟡",
            DriftStatus.ABORT: "🔴",
        }.get(report.status, "⚪")
        return (
            f"{emoji} {report.status.value} | "
            f"{len(self.accumulated_state)} state changes | "
            f"{len(report.red_flags)} red flags"
        )


class DriftAbortError(Exception):
    """Raised when drift detector triggers ABORT."""
    pass


# ---------------------------------------------------------------------------
# Convenience decorator for drift-tracked functions
# ---------------------------------------------------------------------------


def track_drift(detector: DriftDetector):
    """Decorator that auto-increments tool call counter on every tool use.

    Usage:
        detector = DriftDetector()
        detector.set_goal("Add /budget command")

        @track_drift(detector)
        async def my_tool_call():
            ...
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            detector.increment_tool_calls()
            # Auto-check every 5 calls
            if detector.tool_call_count % 5 == 0:
                report = detector.check_drift()
                if report.status == DriftStatus.ABORT:
                    raise DriftAbortError(
                        f"Drift check at tool call {detector.tool_call_count}: "
                        f"{report.delta_assessment}"
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator
