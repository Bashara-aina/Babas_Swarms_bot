"""Agent 10: HeadRecoveryAgent — freezing/unfreezing, reinit, LR changes."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

FREEZE_RE = re.compile(r"(?:freez|unfreez|frozen)", re.IGNORECASE)
REINIT_RE = re.compile(r"(?:reinit|re-initialize|reset.*head|head.*reset)", re.IGNORECASE)
LR_RE = re.compile(r"lr[=:]\s*([\d.eE+-]+)")
LR_DECAY_RE = re.compile(r"(?:lr.*decay|decay.*lr|lr.*schedule)", re.IGNORECASE)


class HeadRecoveryAgent(BaseAgent):
    """Tracks head freezing, reinitialization, and learning rate changes."""

    def __init__(self):
        super().__init__("HeadRecovery")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        freezes = FREEZE_RE.findall(log_text)
        reinits = REINIT_RE.findall(log_text)
        lr_vals = [float(m.group(1)) for m in LR_RE.finditer(log_text)]
        lr_decays = LR_DECAY_RE.findall(log_text)

        # E01: Heads reinitializing properly
        if reinits:
            checks.append(CheckResult("E01", "HeadRecovery", "Head reinitialization events",
                                      Verdict.INFO, f"{len(reinits)} reinit event(s)"))
        else:
            checks.append(CheckResult("E01", "HeadRecovery", "Head reinitialization events",
                                      Verdict.INFO, "No reinit events"))

        # E02: Learning rate is positive and reasonable
        if lr_vals:
            latest_lr = lr_vals[-1]
            reasonable = 1e-8 < latest_lr < 1.0
            checks.append(CheckResult("E02", "HeadRecovery", "Learning rate is reasonable",
                                      Verdict.PASS if reasonable else Verdict.WARN,
                                      f"Latest LR: {latest_lr:.2e}"))
        else:
            checks.append(CheckResult("E02", "HeadRecovery", "Learning rate is reasonable",
                                      Verdict.INFO))

        # E03: LR decay/scheduling active
        if lr_decays:
            checks.append(CheckResult("E03", "HeadRecovery", "LR decay/scheduling active",
                                      Verdict.PASS, f"{len(lr_decays)} decay event(s)"))
        elif len(lr_vals) >= 3:
            decreasing = lr_vals[-1] < lr_vals[0]
            checks.append(CheckResult("E03", "HeadRecovery", "LR decay/scheduling active",
                                      Verdict.PASS if decreasing else Verdict.INFO,
                                      f"LR trend: {lr_vals[0]:.2e} → {lr_vals[-1]:.2e}"))
        else:
            checks.append(CheckResult("E03", "HeadRecovery", "LR decay/scheduling active",
                                      Verdict.INFO, "Not enough LR data"))

        # E04: Freeze/unfreeze events present
        if freezes:
            checks.append(CheckResult("E04", "HeadRecovery", "Freeze/unfreeze events detected",
                                      Verdict.INFO, f"{len(freezes)} freeze/unfreeze event(s)"))
        else:
            checks.append(CheckResult("E04", "HeadRecovery", "Freeze/unfreeze events detected",
                                      Verdict.INFO, "No freeze events"))

        # E05: Head recovery after being dead
        dead_then_alive = re.findall(r"head (\w+).*?(?:DEAD|ALIVE)", log_text, re.IGNORECASE)
        if dead_then_alive:
            checks.append(CheckResult("E05", "HeadRecovery", "Head status changes tracked",
                                      Verdict.INFO, f"Head status transitions: {len(dead_then_alive)}"))

        # E06: LR not stuck at 0
        if lr_vals:
            nonzero = all(lr > 0 for lr in lr_vals[-5:])
            checks.append(CheckResult("E06", "HeadRecovery", "Learning rate not stuck at zero",
                                      Verdict.FAIL if not nonzero else Verdict.PASS,
                                      "LR is zero" if not nonzero else "LR positive",
                                      blocking=not nonzero))
        else:
            checks.append(CheckResult("E06", "HeadRecovery", "Learning rate not stuck at zero",
                                      Verdict.INFO))

        return AgentResult(self.name, checks)
