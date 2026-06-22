"""M3 Swarm Utilities — anti-loop, confidence gating, evidence hierarchy, thinking protocol.

Shared components for swarm orchestration patterns:
- AntiLoopGuard: tracks repeated actions, fires stop signal
- ConfidenceGate: checks threshold before irreversible operations
- EvidenceFormatter: formats P1-P6 confidence-labeled output
- ThinkingProtocol: interleaved thinking between tool calls
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Anti-Loop Guard
# ---------------------------------------------------------------------------


class StopSignal(StrEnum):
    """Reasons why a swarm agent should stop."""
    SAME_PROPOSAL = "same_proposal"
    SAME_FILE_READ = "same_file_read"
    SAME_COMMAND = "same_command"
    SAME_RESULT = "same_result"
    MAX_ROUNDS = "max_rounds"
    MAX_TOOL_CALLS = "max_tool_calls"
    CONVERGED = "converged"


@dataclass
class LoopRecord:
    """A single action attempt in the loop detector."""
    action: str
    result_hash: str
    timestamp: float


class AntiLoopGuard:
    """Tracks repeated actions and fires stop signals.

    Usage:
        guard = AntiLoopGuard()

        # Track an action
        guard.track("read_file", "tools/read.py", "hash_abc123")

        # Check if stopped
        if guard.should_stop():
            print(f"Stop: {guard.stop_reason()}")
            guard.reset()
    """

    def __init__(
        self,
        max_same_actions: int = 2,
        max_tool_calls: int = 8,
        max_rounds: int = 3,
    ) -> None:
        self.max_same_actions = max_same_actions
        self.max_tool_calls = max_tool_calls
        self.max_rounds = max_rounds

        self._action_counts: dict[str, int] = {}
        self._result_hashes: list[str] = []
        self._tool_call_count: int = 0
        self._round_count: int = 0
        self._stop_signal: StopSignal | None = None
        self._stop_context: str = ""

    def track(self, action_type: str, action_value: str, result_hash: str = "") -> None:
        """Track a single action attempt."""
        key = f"{action_type}:{action_value}"
        self._action_counts[key] = self._action_counts.get(key, 0) + 1

        if result_hash:
            self._result_hashes.append(result_hash)
            # Keep only last 10 hashes
            if len(self._result_hashes) > 10:
                self._result_hashes = self._result_hashes[-10:]

        self._tool_call_count += 1
        self._check_stops(action_type, action_value)

    def track_round(self) -> None:
        """Increment round counter."""
        self._round_count += 1
        if self._round_count >= self.max_rounds:
            self._stop_signal = StopSignal.MAX_ROUNDS
            self._stop_context = f"Round {self._round_count} reached max {self.max_rounds}"

    def _check_stops(self, action_type: str, action_value: str) -> None:
        """Check all stop conditions."""
        key = f"{action_type}:{action_value}"

        # Same action repeated
        if self._action_counts.get(key, 0) > self.max_same_actions:
            self._stop_signal = StopSignal.SAME_PROPOSAL
            self._stop_context = f"Action '{action_value}' repeated >{self.max_same_actions}x"
            return

        # Too many tool calls
        if self._tool_call_count >= self.max_tool_calls:
            self._stop_signal = StopSignal.MAX_TOOL_CALLS
            self._stop_context = f"{self._tool_call_count} tool calls with no progress"
            return

        # Same result hash 3 times in a row
        if len(self._result_hashes) >= 3:
            if self._result_hashes[-1] == self._result_hashes[-2] == self._result_hashes[-3]:
                self._stop_signal = StopSignal.SAME_RESULT
                self._stop_context = "3 identical results in a row"
                return

    def should_stop(self) -> bool:
        """Return True if a stop condition has been triggered."""
        return self._stop_signal is not None

    def stop_reason(self) -> str:
        """Return the stop context."""
        return self._stop_context

    def stop_signal(self) -> StopSignal | None:
        """Return the stop signal type."""
        return self._stop_signal

    def reset(self) -> None:
        """Reset all counters and stop state."""
        self._action_counts.clear()
        self._result_hashes.clear()
        self._tool_call_count = 0
        self._round_count = 0
        self._stop_signal = None
        self._stop_context = ""

    def summary(self) -> dict[str, Any]:
        """Return loop guard state for debugging."""
        return {
            "tool_calls": self._tool_call_count,
            "rounds": self._round_count,
            "stopped": self._stop_signal is not None,
            "signal": self._stop_signal.value if self._stop_signal else None,
            "context": self._stop_context,
            "action_counts": dict(self._action_counts),
        }


# ---------------------------------------------------------------------------
# Confidence Gate
# ---------------------------------------------------------------------------


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ConfidenceCheck:
    """Result of a confidence gate check."""
    passed: bool
    level: ConfidenceLevel
    threshold: float
    blockers: list[str] = field(default_factory=list)


class ConfidenceGate:
    """Checks confidence threshold before irreversible operations.

    Usage:
        gate = ConfidenceGate(threshold=0.85)

        check = gate.check(
            confidence=0.72,
            context={"action": "delete_file", "path": "/important.txt"}
        )
        if not check.passed:
            print(f"Blocked: {check.blockers}")
    """

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    def check(
        self,
        confidence: float,
        context: dict[str, Any] | None = None,
    ) -> ConfidenceCheck:
        """Check if confidence meets threshold for an action."""
        blockers: list[str] = []

        if confidence < self.threshold:
            blockers.append(
                f"Confidence {confidence:.0%} below {self.threshold:.0%} threshold"
            )

        # Check for irreversible action markers
        if context:
            action = context.get("action", "")
            irreversible_markers = ["delete", "drop", "truncate", "rm ", "remove"]
            if any(m in action.lower() for m in irreversible_markers):
                if confidence < 0.90:
                    blockers.append(
                        f"Irreversible action '{action}' requires ≥90% confidence"
                    )

        level = ConfidenceLevel.HIGH if confidence >= 0.90 else (
            ConfidenceLevel.MEDIUM if confidence >= self.threshold else ConfidenceLevel.LOW
        )

        return ConfidenceCheck(
            passed=len(blockers) == 0,
            level=level,
            threshold=self.threshold,
            blockers=blockers,
        )


# ---------------------------------------------------------------------------
# Evidence Hierarchy Formatter
# ---------------------------------------------------------------------------


class EvidencePriority(StrEnum):
    P1 = "P1"  # Files/code in context — absolute
    P2 = "P2"  # Explicit user instructions — absolute
    P3 = "P3"  # Stable language/math facts — high
    P4 = "P4"  # Documented library behavior — medium
    P5 = "P5"  # Pattern/training inference — low
    P6 = "P6"  # Unknown/out-of-distribution — explicitly flag


@dataclass
class EvidenceItem:
    """A single piece of evidence with priority."""
    claim: str
    priority: EvidencePriority
    source: str = ""  # file:line or "test output" etc.
    basis: str = ""   # Why we believe this


class EvidenceFormatter:
    """Formats output with P1-P6 evidence hierarchy.

    Usage:
        formatter = EvidenceFormatter()
        formatted = formatter.format([
            EvidenceItem("sqlite3 is thread-safe", EvidencePriority.P4, "docs.python.org/3/library/sqlite3.html"),
            EvidenceItem("fn requires asyncio", EvidencePriority.P1, "core/interpreter_bridge.py:142"),
        ])
        print(formatted)
    """

    def format(self, items: list[EvidenceItem]) -> str:
        """Format evidence items into sections."""
        if not items:
            return ""

        sections: dict[EvidencePriority, list[str]] = {
            EvidencePriority.P1: [],
            EvidencePriority.P2: [],
            EvidencePriority.P3: [],
            EvidencePriority.P4: [],
            EvidencePriority.P5: [],
            EvidencePriority.P6: [],
        }

        for item in items:
            line = f"- {item.claim}"
            if item.source:
                line += f" (@ {item.source})"
            if item.basis:
                line += f" — {item.basis}"
            sections[item.priority].append(line)

        parts = []
        for priority in [EvidencePriority.P1, EvidencePriority.P2, EvidencePriority.P3]:
            if sections[priority]:
                parts.append(f"**{priority.value} CONFIRMED:**\n" + "\n".join(sections[priority]))

        for priority in [EvidencePriority.P4, EvidencePriority.P5]:
            if sections[priority]:
                parts.append(f"**{priority.value} INFERRED:**\n" + "\n".join(sections[priority]))

        if sections[EvidencePriority.P6]:
            parts.append(f"**{EvidencePriority.P6} NEEDS VERIFICATION:**\n" + "\n".join(sections[EvidencePriority.P6]))

        return "\n\n".join(parts)

    def format_text(self, text: str, claims: list[str]) -> str:
        """Format plain text output with inline evidence labels."""
        if not claims:
            return text

        return f"{text}\n\n---\n**EVIDENCE SUMMARY:**\n" + self.format([
            EvidenceItem(claim=c, priority=self._classify_claim(c))
            for c in claims
        ])

    def _classify_claim(self, claim: str) -> EvidencePriority:
        """Classify a claim's evidence priority."""
        claim_lower = claim.lower()
        if any(kw in claim_lower for kw in ["verified", "confirmed", "tested", "proven"]):
            return EvidencePriority.P3
        if any(kw in claim_lower for kw in ["probably", "likely", "might", "seems"]):
            return EvidencePriority.P5
        if any(kw in claim_lower for kw in ["unknown", "unclear", "not sure", "need to verify"]):
            return EvidencePriority.P6
        return EvidencePriority.P4


# ---------------------------------------------------------------------------
# Thinking Protocol
# ---------------------------------------------------------------------------


class ThinkingProtocol:
    """Interleaved thinking between tool calls.

    Usage:
        thinker = ThinkingProtocol()

        # Before each tool call:
        thought = thinker.think(
            last_result="File read successfully, 142 lines",
            expectation="Should see imports at the top",
            goal="Find the authenticate() function",
            previous_actions=["read_file tools/auth.py", "read_file core/nexus.py"],
        )
        print(thought)  # Injected into agent prompt
    """

    PROMPT_TEMPLATE = """
THINKING PROTOCOL — Before Your Next Action:
1. Last result: {last_result}
2. Expectation: {expectation}
3. Next action: {next_action}
4. Risk of repeating: {repeating_risk}

{anti_loop_warning}
""".strip()

    ANTI_LOOP_WARNING = "⚠️ ANTI-LOOP: If repeating same action 2+ times, STOP and try a different approach."

    def think(
        self,
        last_result: str,
        expectation: str,
        goal: str,
        previous_actions: list[str] | None = None,
    ) -> str:
        """Generate a thinking prompt before the next action."""
        # Determine repeating risk
        repeating_risk = "none"
        if previous_actions:
            if len(previous_actions) >= 3 and previous_actions[-1] == previous_actions[-2] == previous_actions[-3]:
                repeating_risk = "HIGH — same action 3 times"
            elif len(previous_actions) >= 2 and previous_actions[-1] == previous_actions[-2]:
                repeating_risk = "MEDIUM — same action twice"

        # Determine next action hint
        next_action = "Take the single most important next step toward the goal."

        # Build anti-loop warning
        anti_loop = self.ANTI_LOOP_WARNING if repeating_risk != "none" else ""

        return self.PROMPT_TEMPLATE.format(
            last_result=last_result[:200] if last_result else "(none yet)",
            expectation=expectation[:200] if expectation else "(not set)",
            next_action=next_action,
            repeating_risk=repeating_risk,
            anti_loop_warning=anti_loop,
        )

    def inject_into_prompt(self, prompt: str, last_result: str = "") -> str:
        """Inject thinking protocol into an existing prompt."""
        thinking = self.think(
            last_result=last_result,
            expectation="Continue toward the task goal",
            goal="Complete the assigned task",
        )
        return f"{prompt}\n\n{thinking}"


# ---------------------------------------------------------------------------
# Self-Audit Footer
# ---------------------------------------------------------------------------


@dataclass
class AuditResult:
    """Result of a self-audit check."""
    confidence: ConfidenceLevel
    verified: bool  # True if P1/P2, False if P5/P6
    items_needing_verification: list[str]
    reasoning: str


def apply_self_audit(
    result: str,
    context: str = "",
    confidence: float = 0.8,
) -> str:
    """Add a LEGIONA SELF-AUDIT footer to a result.

    Args:
        result: The agent's output text.
        context: Brief description of what was worked on.
        confidence: Estimated confidence 0.0-1.0.

    Returns:
        Result with self-audit footer appended.
    """
    if confidence >= 0.90:
        conf_level = "HIGH"
        verified = True
    elif confidence >= 0.70:
        conf_level = "MEDIUM"
        verified = True
    else:
        conf_level = "LOW"
        verified = False

    # Check for verification-needed phrases in result
    needs_verification: list[str] = []
    for phrase in ["need to verify", "unclear", "should confirm", "probably", "might be", "unknown"]:
        if phrase.lower() in result.lower():
            needs_verification.append(phrase)

    footer = f"""
---
**LEGIONA SELF-AUDIT**
- Confidence: {conf_level}
- Verified from context: {"YES" if verified else "PARTIAL"}
- Items needing verification: {", ".join(needs_verification) if needs_verification else "none"}
"""
    return result + footer


# ---------------------------------------------------------------------------
# Swarm Session Record
# ---------------------------------------------------------------------------

async def record_swarm_session(
    task: str,
    agents: list[str],
    outcome: str,
    success: bool,
    tool_call_count: int = 0,
) -> None:
    """Record a swarm session for self-evolution.

    Args:
        task: Task description.
        agents: List of agent names that participated.
        outcome: What happened.
        success: Whether the task succeeded.
        tool_call_count: Total tool calls across all agents.
    """
    try:
        from core.self_evolution import get_self_evolution_engine
        engine = get_self_evolution_engine()

        await engine.record_failure(
            task=task,
            approach=f"Swarm with {len(agents)} agents: {', '.join(agents[:3])}{'...' if len(agents) > 3 else ''}",
            failure_mode=outcome[:100] if not success else "swarm_completed",
            root_cause="swarm_agent_execution",
            fix_applied="none",
            prevention_rule="Track swarm sessions for self-evolution",
            title=f"Swarm {'failure' if not success else 'completion'}: {task[:50]}",
        )

    except Exception as exc:
        # Non-fatal — swarm should not crash on self-evolution failure
        import logging
        logging.getLogger(__name__).warning(f"Failed to record swarm session: {exc}")