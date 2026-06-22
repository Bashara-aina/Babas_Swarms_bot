"""Agent 05: ConvergenceAgent — loss plateau, metric stagnation, oscillation detection."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict
from ..config import CONV

VAL_MAP_RE = re.compile(r"Val:.*det_mAP50=([\d.]+)")
LOSS_RE = re.compile(r"det_cls_loss[=:](\d+\.\d+)")


class ConvergenceAgent(BaseAgent):
    """Checks if training is converging properly."""

    def __init__(self):
        super().__init__("Convergence")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        patience = CONV["patience_epochs"]
        min_improve = CONV["min_improvement"]

        map_vals = [float(m.group(1)) for m in VAL_MAP_RE.finditer(log_text)]
        loss_vals = [float(m.group(1)) for m in LOSS_RE.finditer(log_text)]

        # S01: det_mAP50 not plateaued
        if len(map_vals) >= patience:
            recent = map_vals[-patience:]
            plateau = max(recent) - min(recent) < min_improve
            checks.append(CheckResult("S01", "Convergence", "det_mAP50 not plateaued",
                                      Verdict.WARN if plateau else Verdict.PASS,
                                      f"Range over last {patience}: {max(recent) - min(recent):.4f}"))
        else:
            checks.append(CheckResult("S01", "Convergence", "det_mAP50 not plateaued",
                                      Verdict.INFO, f"Need {patience} epochs, have {len(map_vals)}"))

        # S02: det_cls loss decreasing
        if len(loss_vals) >= patience:
            recent = loss_vals[-patience:]
            decreasing = recent[-1] < recent[0]
            checks.append(CheckResult("S02", "Convergence", "det_cls loss decreasing over recent epochs",
                                      Verdict.PASS if decreasing else Verdict.WARN,
                                      f"{recent[0]:.4f} → {recent[-1]:.4f}"))
        else:
            checks.append(CheckResult("S02", "Convergence", "det_cls loss decreasing over recent epochs",
                                      Verdict.INFO))

        # S03: No oscillation in det_mAP50
        if len(map_vals) >= 4:
            recent = map_vals[-4:]
            alternating = (recent[0] < recent[1] > recent[2] < recent[3]) or \
                          (recent[0] > recent[1] < recent[2] > recent[3])
            checks.append(CheckResult("S03", "Convergence", "No oscillation in det_mAP50",
                                      Verdict.WARN if alternating else Verdict.PASS,
                                      f"{recent}"))
        else:
            checks.append(CheckResult("S03", "Convergence", "No oscillation in det_mAP50",
                                      Verdict.INFO))

        # S04: Loss curve still descending
        if len(loss_vals) >= 3:
            first_half = sum(loss_vals[:len(loss_vals)//2]) / max(len(loss_vals)//2, 1)
            second_half = sum(loss_vals[len(loss_vals)//2:]) / max(len(loss_vals) - len(loss_vals)//2, 1)
            descending = second_half < first_half
            checks.append(CheckResult("S04", "Convergence", "Loss curve generally descending",
                                      Verdict.PASS if descending else Verdict.WARN,
                                      f"First half avg={first_half:.4f}  Second half avg={second_half:.4f}"))
        else:
            checks.append(CheckResult("S04", "Convergence", "Loss curve generally descending",
                                      Verdict.INFO))

        # S05: mAP50 improving over last 2 epochs
        if len(map_vals) >= 2:
            improving = map_vals[-1] >= map_vals[-2]
            checks.append(CheckResult("S05", "Convergence", "det_mAP50 improving epoch-to-epoch",
                                      Verdict.PASS if improving else Verdict.WARN,
                                      f"{map_vals[-2]:.4f} → {map_vals[-1]:.4f}"))
        else:
            checks.append(CheckResult("S05", "Convergence", "det_mAP50 improving epoch-to-epoch",
                                      Verdict.INFO))

        # S06: Current val is best or near-best
        if len(map_vals) >= 3:
            best = max(map_vals)
            current = map_vals[-1]
            near_best = current >= best - 2 * min_improve
            checks.append(CheckResult("S06", "Convergence", "Current val is best or near-best",
                                      Verdict.PASS if near_best else Verdict.WARN,
                                      f"Current={current:.4f}  Best={best:.4f}"))
        else:
            checks.append(CheckResult("S06", "Convergence", "Current val is best or near-best",
                                      Verdict.INFO))

        return AgentResult(self.name, checks)
