"""Agent 20: SummaryAgent — executive summary, trend direction, recommended actions.

Uses RF2-only validation data to avoid RF1 data polluting trend analysis.
"""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text
from ..config import GATE

VAL_MAP50_RE = re.compile(r"Val:.*det_mAP50=([\d.]+)")
VAL_MAE_RE = re.compile(r"Val:.*forward_angular_MAE_deg=([\d.]+)")


def _current_run_vals(log_text: str, regex: re.Pattern) -> list[float]:
    """Extract validation metric values from the current training run only."""
    run_text = current_run_text(log_text)
    return [float(m.group(1)) for m in regex.finditer(run_text)]


class SummaryAgent(BaseAgent):
    """Produces an executive summary of overall swarm health."""

    def __init__(self):
        super().__init__("Summary")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        prev_results = ctx.get("prev_results", {})
        state = ctx.get("state", {})
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        # Collect all verdicts from previous cycle
        all_checks: list[dict] = []
        for agent_checks in prev_results.values():
            if isinstance(agent_checks, list):
                all_checks.extend(agent_checks)

        total = len(all_checks)
        failed = sum(1 for c in all_checks if c.get("verdict") == Verdict.FAIL)
        warned = sum(1 for c in all_checks if c.get("verdict") == Verdict.WARN)
        blocking = sum(1 for c in all_checks if c.get("verdict") == Verdict.FAIL and c.get("blocking"))

        # Current-run validation data
        map50_vals = _current_run_vals(log_text, VAL_MAP50_RE)
        mae_vals = _current_run_vals(log_text, VAL_MAE_RE)

        latest_map50 = map50_vals[-1] if map50_vals else None
        latest_mae = mae_vals[-1] if mae_vals else None
        current_epoch = state.get("epoch", 0)
        max_epochs = state.get("max_epochs", 21)
        gate_passed = state.get("gate_passed", False)

        # SA01: Executive health status
        if total == 0:
            checks.append(CheckResult("SA01", "Summary", "Executive health status",
                                      Verdict.INFO, "First cycle — aggregating data"))
        elif blocking > 0:
            checks.append(CheckResult("SA01", "Summary", "Executive health status",
                                      Verdict.FAIL, f"BLOCKED — {blocking} blocking failures",
                                      blocking=True))
        elif failed > 0:
            checks.append(CheckResult("SA01", "Summary", "Executive health status",
                                      Verdict.WARN,
                                      f"DEGRADED — {failed} non-blocking failures, {warned} warnings"))
        elif warned > 5:
            checks.append(CheckResult("SA01", "Summary", "Executive health status",
                                      Verdict.WARN, f"ATTENTION — {warned} warnings to review"))
        else:
            checks.append(CheckResult("SA01", "Summary", "Executive health status",
                                      Verdict.PASS, f"HEALTHY — all {total} checks passing"))

        # SA02: Trend direction (RF2 data only)
        if len(map50_vals) >= 3:
            recent = map50_vals[-3:]
            if recent[-1] > recent[0] * 1.01:
                trend = "improving"
            elif recent[-1] < recent[0] * 0.99:
                trend = "degrading"
            else:
                trend = "stable"
            checks.append(CheckResult("SA02", "Summary", "Training trend direction",
                                      Verdict.PASS if trend != "degrading" else Verdict.WARN,
                                      f"det_mAP50 trend: {trend} ({recent[0]:.4f} → {recent[-1]:.4f})  [RF2]"))
        elif len(map50_vals) > 0:
            checks.append(CheckResult("SA02", "Summary", "Training trend direction",
                                      Verdict.INFO,
                                      f"{len(map50_vals)} RF2 val point(s) — need 3 for trend"))
        else:
            checks.append(CheckResult("SA02", "Summary", "Training trend direction",
                                      Verdict.INFO, "No RF2 validation data yet"))

        # SA03: Gate progress summary (RF2 data only)
        if latest_map50 is not None:
            map50_gap = GATE["det_mAP50"] - latest_map50
            mae_gap = latest_mae - GATE["forward_angular_MAE_deg"] if latest_mae else 0
            remaining = max_epochs - current_epoch

            parts = []
            if map50_gap > 0:
                parts.append(f"mAP50 needs +{map50_gap:.3f}")
            else:
                parts.append("mAP50 target MET")
            if mae_gap is not None and mae_gap > 0:
                parts.append(f"MAE needs -{mae_gap:.1f}°")
            elif mae_gap is not None:
                parts.append("MAE target MET")

            if gate_passed:
                summary = "GATE PASSED — all targets met!"
            else:
                gap_str = ", ".join(parts) if parts else "no RF2 metrics yet"
                summary = f"Gate not yet passed — {gap_str} ({remaining} epochs remain)"

            checks.append(CheckResult("SA03", "Summary", "Gate progress summary",
                                      Verdict.PASS if gate_passed else Verdict.INFO,
                                      summary))
        else:
            checks.append(CheckResult("SA03", "Summary", "Gate progress summary",
                                      Verdict.INFO, "No RF2 validation data yet"))

        return AgentResult(self.name, checks)
