"""Agent evaluator — lightweight quality scoring without LLM judge.

Evaluates agent responses using heuristic signals:
- Response length (too short = likely incomplete, too long = verbose)
- Error indicators (tracebacks, "I can't", "I don't have access")
- Code quality signals (syntax errors, incomplete snippets)
- Latency (fast = good for simple tasks)
- User feedback (thumbs up/down from Telegram inline buttons)

Does NOT use LLM-as-judge to avoid additional cost.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating an agent response."""

    task_id: str
    agent_name: str
    overall_score: float  # 0.0 to 1.0
    signals: Dict[str, float] = field(default_factory=dict)
    passed: bool = True
    notes: List[str] = field(default_factory=list)


# Negative signals in agent output
_FAILURE_PATTERNS = [
    r"i (?:can't|cannot|don't have|am unable to)",
    r"as an ai",
    r"i don't have access",
    r"error:|traceback|exception:",
    r"i apologize",
    r"unfortunately",
]


class AgentEvaluator:
    """Evaluate agent response quality using heuristics.

    Tracks per-agent quality scores over time for monitoring.
    """

    def __init__(self) -> None:
        self._evaluations: List[EvaluationResult] = []
        self._user_feedback: Dict[str, int] = {}  # task_id → rating (1-5)

    def evaluate(
        self,
        task_id: str,
        agent_name: str,
        task_description: str,
        response: str,
        latency_ms: int = 0,
        success: bool = True,
    ) -> EvaluationResult:
        """Evaluate an agent response.

        Args:
            task_id: Unique task identifier.
            agent_name: Agent that produced the response.
            task_description: Original task.
            response: Agent's response text.
            latency_ms: Execution time.
            success: Whether the call succeeded.

        Returns:
            EvaluationResult with quality signals and score.
        """
        signals: Dict[str, float] = {}
        notes: List[str] = []

        if not success or not response:
            return EvaluationResult(
                task_id=task_id,
                agent_name=agent_name,
                overall_score=0.0,
                signals={"success": 0.0},
                passed=False,
                notes=["Execution failed or empty response"],
            )

        # Signal 1: Response completeness (length relative to task)
        task_len = len(task_description)
        resp_len = len(response)
        if resp_len < 20:
            signals["completeness"] = 0.2
            notes.append("Very short response")
        elif resp_len < task_len * 0.3:
            signals["completeness"] = 0.5
        elif resp_len > task_len * 50:
            signals["completeness"] = 0.7
            notes.append("Very verbose response")
        else:
            signals["completeness"] = 1.0

        # Signal 2: Absence of failure patterns
        resp_lower = response.lower()
        failure_count = sum(
            1 for pat in _FAILURE_PATTERNS
            if re.search(pat, resp_lower)
        )
        signals["no_failures"] = max(0.0, 1.0 - failure_count * 0.3)
        if failure_count > 0:
            notes.append(f"Detected {failure_count} failure pattern(s)")

        # Signal 3: Code quality (if response contains code)
        if "```" in response or "def " in response or "class " in response:
            signals["code_quality"] = self._score_code_quality(response)
        else:
            signals["code_quality"] = 1.0  # N/A

        # Signal 4: Latency (relative to task complexity)
        if latency_ms > 0:
            if latency_ms < 2000:
                signals["latency"] = 1.0
            elif latency_ms < 10000:
                signals["latency"] = 0.8
            elif latency_ms < 30000:
                signals["latency"] = 0.5
            else:
                signals["latency"] = 0.3
                notes.append(f"Slow response: {latency_ms}ms")

        # Signal 5: User feedback (if available)
        feedback = self._user_feedback.get(task_id)
        if feedback is not None:
            signals["user_feedback"] = feedback / 5.0

        # Calculate overall score (weighted average)
        weights = {
            "completeness": 0.25,
            "no_failures": 0.30,
            "code_quality": 0.20,
            "latency": 0.10,
            "user_feedback": 0.15,
        }

        total_weight = 0.0
        weighted_sum = 0.0
        for signal_name, weight in weights.items():
            if signal_name in signals:
                weighted_sum += signals[signal_name] * weight
                total_weight += weight

        overall = weighted_sum / total_weight if total_weight > 0 else 0.5

        result = EvaluationResult(
            task_id=task_id,
            agent_name=agent_name,
            overall_score=round(overall, 3),
            signals=signals,
            passed=overall >= 0.5,
            notes=notes,
        )

        self._evaluations.append(result)
        if len(self._evaluations) > 2000:
            self._evaluations = self._evaluations[-2000:]

        return result

    def record_feedback(self, task_id: str, rating: int) -> None:
        """Record user feedback for a task.

        Args:
            task_id: Task identifier.
            rating: User rating (1-5).
        """
        self._user_feedback[task_id] = max(1, min(5, rating))

    def _score_code_quality(self, response: str) -> float:
        """Score code quality heuristics.

        Returns a score 0.0 to 1.0.
        """
        score = 1.0

        # Check for truncated code (incomplete blocks)
        open_blocks = response.count("```")
        if open_blocks % 2 != 0:
            score -= 0.3  # Unclosed code block

        # Check for common syntax issues
        if "SyntaxError" in response or "IndentationError" in response:
            score -= 0.4

        # Check for TODO/FIXME/placeholder
        if "TODO" in response or "FIXME" in response or "..." in response:
            score -= 0.1

        return max(0.0, score)

    def get_agent_scores(self) -> Dict[str, Dict[str, float]]:
        """Get average scores per agent.

        Returns:
            Dict mapping agent_name → {avg_score, count, pass_rate}.
        """
        agent_data: Dict[str, List[EvaluationResult]] = {}
        for ev in self._evaluations:
            agent_data.setdefault(ev.agent_name, []).append(ev)

        result = {}
        for agent, evals in agent_data.items():
            scores = [e.overall_score for e in evals]
            passed = sum(1 for e in evals if e.passed)
            result[agent] = {
                "avg_score": round(sum(scores) / len(scores), 3),
                "count": len(evals),
                "pass_rate": round(passed / len(evals), 3),
            }

        return result

    def format_scores_html(self) -> str:
        """Format agent quality scores as HTML for Telegram."""
        scores = self.get_agent_scores()

        if not scores:
            return "<b>Agent Quality:</b> No evaluations yet"

        lines = ["<b>Agent Quality Scores</b>\n"]

        for agent, data in sorted(
            scores.items(), key=lambda x: x[1]["avg_score"], reverse=True
        ):
            bar_len = int(data["avg_score"] * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            lines.append(
                f"<code>{agent:12s}</code> {bar} "
                f"{data['avg_score']*100:.0f}% "
                f"({data['count']} tasks, "
                f"{data['pass_rate']*100:.0f}% pass)"
            )

        return "\n".join(lines)
