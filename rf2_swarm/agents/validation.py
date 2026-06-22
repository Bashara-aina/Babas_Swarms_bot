"""Agent 09: ValidationAgent — val runs, metric consistency, NaN in val metrics."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text

VAL_OK_RE = re.compile(r"\[VAL_OK\] epoch (\d+) val completed")
VAL_METRICS_RE = re.compile(
    r"Val:.*det_mAP50=([\d.]+).*forward_angular_MAE_deg=([\d.]+)"
)
VAL_NAN_RE = re.compile(r"Val:.*NaN", re.IGNORECASE)


class ValidationAgent(BaseAgent):
    """Monitors validation run health and consistency."""

    def __init__(self):
        super().__init__("Validation")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        run_text = current_run_text(log_text)  # current run only — filter stale crash data
        checks: list[CheckResult] = []

        val_oks = [int(m.group(1)) for m in VAL_OK_RE.finditer(run_text)]
        val_metrics = VAL_METRICS_RE.findall(run_text)
        val_nans = VAL_NAN_RE.findall(run_text)

        # V01: Validation runs completing
        if val_oks:
            latest_epoch = max(val_oks)
            checks.append(CheckResult("V01", "Validation", "Validation runs completing",
                                      Verdict.PASS, f"{len(val_oks)} val runs, latest at epoch {latest_epoch}"))
        else:
            # Early in a resumed run — no epoch-end validation has completed yet
            checks.append(CheckResult("V01", "Validation", "Validation runs completing",
                                      Verdict.INFO, "No validation runs in current run yet — expected before first epoch completes", blocking=False))

        # V02: Validation at expected frequency
        if val_oks:
            if len(val_oks) >= 2:
                gaps = [val_oks[i] - val_oks[i - 1] for i in range(1, len(val_oks))]
                avg_gap = sum(gaps) / len(gaps)
                consistent = all(1 <= g <= 3 for g in gaps)
                checks.append(CheckResult("V02", "Validation", "Validation at expected frequency",
                                          Verdict.PASS if consistent else Verdict.WARN,
                                          f"Avg gap: {avg_gap:.1f} epochs"))
            else:
                checks.append(CheckResult("V02", "Validation", "Validation at expected frequency",
                                          Verdict.INFO, "Single val run so far"))
        else:
            checks.append(CheckResult("V02", "Validation", "Validation at expected frequency",
                                      Verdict.SKIP))

        # V03: No NaN in validation metrics
        checks.append(CheckResult("V03", "Validation", "No NaN in validation metrics",
                                  Verdict.FAIL if val_nans else Verdict.PASS,
                                  "NaN in val metrics" if val_nans else "No val NaN"))

        # V04: Validation metrics complete (both mAP50 and MAE)
        if val_metrics:
            latest = val_metrics[-1]
            map50, mae = float(latest[0]), float(latest[1])
            complete = map50 > 0 and mae > 0
            checks.append(CheckResult("V04", "Validation", "Validation metrics complete",
                                      Verdict.PASS if complete else Verdict.WARN,
                                      f"mAP50={map50:.4f}  MAE={mae:.2f}°"))
        else:
            checks.append(CheckResult("V04", "Validation", "Validation metrics complete",
                                      Verdict.INFO))

        # V05: Consistent metric format
        malformed = re.search(r"Val:.*?(?:mAP50|MAE)\s*=\s*[^\d.]+", log_text)
        checks.append(CheckResult("V05", "Validation", "Validation metrics parseable",
                                  Verdict.WARN if malformed else Verdict.PASS,
                                  "Malformed metrics detected" if malformed else "All metrics parseable"))

        # V06: Validation timeouts
        timeout = re.search(r"val.*timeout|validation.*timeout", log_text, re.IGNORECASE)
        checks.append(CheckResult("V06", "Validation", "No validation timeouts",
                                  Verdict.FAIL if timeout else Verdict.PASS,
                                  "Val timeout detected" if timeout else "No val timeout"))

        return AgentResult(self.name, checks)
