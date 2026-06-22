"""Agent 11: MetricsLoggerAgent — subprocess.log parser, metrics.jsonl completeness."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

METRIC_KEYS = {"det_mAP50", "det_mAP50_95", "forward_angular_MAE_deg",
               "det_cls_loss", "det_box_loss", "asd_loss", "psr_loss"}


class MetricsLoggerAgent(BaseAgent):
    """Validates structured metrics output completeness and consistency."""

    def __init__(self):
        super().__init__("MetricsLogger")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        metrics = ctx.get("metrics", [])
        state = ctx.get("state", {})
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        # M01: metrics.jsonl has entries
        if metrics:
            checks.append(CheckResult("M01", "MetricsLogger", "metrics.jsonl has entries",
                                      Verdict.PASS, f"{len(metrics)} records"))
        else:
            checks.append(CheckResult("M01", "MetricsLogger", "metrics.jsonl has entries",
                                      Verdict.INFO, "No metrics.jsonl records"))

        # M02: All expected metric keys present in latest record
        if metrics:
            latest = metrics[-1]
            missing = METRIC_KEYS - set(latest.keys())
            if missing:
                checks.append(CheckResult("M02", "MetricsLogger", "All expected metric keys present",
                                          Verdict.WARN, f"Missing: {missing}"))
            else:
                checks.append(CheckResult("M02", "MetricsLogger", "All expected metric keys present",
                                          Verdict.PASS, f"{len(METRIC_KEYS)} keys present"))
        else:
            checks.append(CheckResult("M02", "MetricsLogger", "All expected metric keys present",
                                      Verdict.SKIP))

        # M03: State.json metrics_history not empty
        metric_history = state.get("metric_history", [])
        if metric_history:
            checks.append(CheckResult("M03", "MetricsLogger", "State metric_history populated",
                                      Verdict.PASS, f"{len(metric_history)} entries"))
        else:
            checks.append(CheckResult("M03", "MetricsLogger", "State metric_history populated",
                                      Verdict.WARN, "metric_history is empty — state not updating"))

        # M04: Cross-stage memory present
        cross = state.get("cross_stage_memory", {})
        if cross:
            checks.append(CheckResult("M04", "MetricsLogger", "Cross-stage memory present",
                                      Verdict.PASS, f"{len(cross)} fields"))
        else:
            checks.append(CheckResult("M04", "MetricsLogger", "Cross-stage memory present",
                                      Verdict.INFO, "No cross-stage memory"))

        # M05: Training log contains ETA
        eta = re.search(r"ETA[=:]\s*([\w.:]+)", log_text, re.IGNORECASE)
        checks.append(CheckResult("M05", "MetricsLogger", "Training log has ETA estimates",
                                  Verdict.PASS if eta else Verdict.INFO,
                                  f"ETA: {eta.group(1)}" if eta else "No ETA found"))

        # M06: Log size manageable for scanning
        lines = ctx.get("log_lines", [])
        if lines:
            checks.append(CheckResult("M06", "MetricsLogger", "Log size manageable",
                                      Verdict.PASS if len(lines) < 500_000 else Verdict.WARN,
                                      f"{len(lines)} lines"))
        else:
            checks.append(CheckResult("M06", "MetricsLogger", "Log size manageable",
                                      Verdict.INFO))

        return AgentResult(self.name, checks)
