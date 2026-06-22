"""Base abstractions: Verdict enum, CheckResult, AgentResult, BaseAgent ABC."""

from __future__ import annotations
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


TRAIN_RUN_START_RE = re.compile(
    r"^.*?(?:Starting training|Resumed from epoch)", re.MULTILINE
)
"""Match the beginning of a training run — either fresh start or resume."""


def current_run_text(log_text: str) -> str:
    """Return only the log portion from the most recent training run.

    Finds the LAST ``Starting training`` or ``Resumed from epoch`` marker
    and returns everything after it.  This filters out data from old runs
    when the training has been restarted.
    """
    matches = list(TRAIN_RUN_START_RE.finditer(log_text))
    if not matches:
        return log_text
    return log_text[matches[-1].start():]


class Verdict:
    """String constants for check verdicts (no enum overhead for JSON serialization)."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    INFO = "INFO"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    """Single check produced by an agent."""
    uid: str
    category: str
    desc: str
    verdict: str = Verdict.INFO
    detail: str = ""
    blocking: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "category": self.category,
            "desc": self.desc,
            "verdict": self.verdict,
            "detail": self.detail,
            "blocking": self.blocking,
        }


@dataclass
class AgentResult:
    """Result produced by one agent in a cycle."""
    agent_name: str
    checks: list[CheckResult] = field(default_factory=list)
    error: str | None = None

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.PASS)

    @property
    def warned(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.WARN)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.FAIL)

    @property
    def blocking(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.FAIL and c.blocking)


class BaseAgent(ABC):
    """Every monitoring agent subclasses this."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, ctx: dict[str, Any]) -> AgentResult:
        """Run this agent's checks against the shared context.

        ``ctx`` is populated by the Coordinator and contains:
            - log_lines : list[str] — tail of subprocess.log
            - log_text  : str — full text of subprocess.log tail
            - state     : dict — parsed rf_stage_state.json
            - metrics   : list[dict] — parsed metrics.jsonl
            - config    : dict — parsed training config.py
            - prev_results : list[dict] — results from previous cycle
        """
        ...
