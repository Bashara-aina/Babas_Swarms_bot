"""Agent 15: NanDetectorAgent — NaN/inf in loss values, metrics, weights."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

NAN_LOSS_RE = re.compile(r"(?:loss|metric).*?\b(?:NaN|Inf|nan|inf)\b")
NAN_WEIGHT_RE = re.compile(r"(?:weight|param|grad).*?\b(?:nan|inf)\b", re.IGNORECASE)
NAN_METRIC_RE = re.compile(r"(?:mAP|MAE|AP).*?\b(?:NaN|nan|inf)\b")
DIV_ZERO_RE = re.compile(r"divide.*zero|division.*zero|RuntimeError.*zero", re.IGNORECASE)
# Exclude efficiency stat lines (Params: nanM, GFLOPs: nanG, EVAL NaN/Inf) that are not training NaNs
EFFICIENCY_RE = re.compile(
    r"(?:Params:\s*nan|GFLOPs:\s*nan|EVAL NaN|FPS.*nan|pipeline.*nan"
    r"|eff_gflops=nan|step_time=nan|eff.*?=nan)"
)


class NanDetectorAgent(BaseAgent):
    """Scans for NaN/inf values in all training signals."""

    def __init__(self):
        super().__init__("NanDetector")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        all_lines = log_text.split("\n")
        nan_losses = [line for line in all_lines if NAN_LOSS_RE.search(line) and not EFFICIENCY_RE.search(line)]
        nan_weights = [line for line in all_lines if NAN_WEIGHT_RE.search(line) and not EFFICIENCY_RE.search(line)]
        nan_metrics = [line for line in all_lines if NAN_METRIC_RE.search(line) and not EFFICIENCY_RE.search(line)]
        div_zeros = DIV_ZERO_RE.findall(log_text)

        # ND01: No NaN in loss values
        checks.append(CheckResult("ND01", "NanDetector", "No NaN in loss values",
                                  Verdict.FAIL if nan_losses else Verdict.PASS,
                                  f"{len(nan_losses)} NaN loss occurrences" if nan_losses else "No loss NaN",
                                  blocking=bool(nan_losses)))

        # ND02: No NaN in weights/gradients
        checks.append(CheckResult("ND02", "NanDetector", "No NaN in weights/gradients",
                                  Verdict.FAIL if nan_weights else Verdict.PASS,
                                  f"{len(nan_weights)} weight NaN occurrences" if nan_weights else "No weight NaN",
                                  blocking=bool(nan_weights)))

        # ND03: No NaN in metrics
        checks.append(CheckResult("ND03", "NanDetector", "No NaN in metrics",
                                  Verdict.FAIL if nan_metrics else Verdict.PASS,
                                  f"{len(nan_metrics)} metric NaN" if nan_metrics else "No metric NaN"))

        # ND04: No divide-by-zero errors
        checks.append(CheckResult("ND04", "NanDetector", "No divide-by-zero errors",
                                  Verdict.FAIL if div_zeros else Verdict.PASS,
                                  f"{len(div_zeros)} div-by-zero" if div_zeros else "No div-by-zero",
                                  blocking=bool(div_zeros)))

        return AgentResult(self.name, checks)
