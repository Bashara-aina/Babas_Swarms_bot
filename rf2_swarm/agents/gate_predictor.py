"""Agent 12: GatePredictorAgent — linear extrapolation from RF2 validation epochs to gate targets."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text
from ..config import GATE, LR_RESTART

VAL_MAP50_RE = re.compile(r"Val:.*det_mAP50=([\d.]+)")
VAL_MAE_RE = re.compile(r"Val:.*forward_angular_MAE_deg=([\d.]+)")
VAL_MAP50_95_RE = re.compile(r"Val:.*det_mAP50_95=([\d.]+)")


def _current_run_vals(log_text: str, regex: re.Pattern) -> list[float]:
    """Extract validation metric values from the current training run only.

    Uses the ``current_run_text`` helper to filter out old runs when the
    training has been restarted.
    """
    run_text = current_run_text(log_text)
    return [float(m.group(1)) for m in regex.finditer(run_text)]


class GatePredictorAgent(BaseAgent):
    """Predicts whether gate targets will be met using linear extrapolation."""

    def __init__(self):
        super().__init__("GatePredictor")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        current_epoch = state.get("epoch", 0)
        max_epochs = state.get("max_epochs", 21)
        remaining = max_epochs - current_epoch

        # Only use current run validation data
        map50_vals = _current_run_vals(log_text, VAL_MAP50_RE)
        mae_vals = _current_run_vals(log_text, VAL_MAE_RE)
        map50_95_vals = _current_run_vals(log_text, VAL_MAP50_95_RE)

        def extrapolate(vals: list[float], target: float, epochs_left: int) -> tuple[bool, float]:
            if len(vals) < 3 or epochs_left <= 0:
                return False, 0.0
            recent = vals[-3:]
            slope = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
            predicted = recent[-1] + slope * epochs_left
            return predicted >= target, predicted

        rf2_prefix = f"[RF2] E{current_epoch}/{max_epochs} "

        # GP01: det_mAP50 gate reachable
        reachable, predicted = extrapolate(map50_vals, GATE["det_mAP50"], remaining)
        if len(map50_vals) >= 3:
            detail = f"{rf2_prefix}Predicted E{max_epochs}: {predicted:.4f}  Target: {GATE['det_mAP50']}  Remaining: {remaining}"
            if reachable:
                checks.append(CheckResult("GP01", "GatePredictor", "det_mAP50 gate reachable",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("GP01", "GatePredictor", "det_mAP50 gate reachable",
                                          Verdict.WARN if predicted > 0 else Verdict.INFO,
                                          detail, blocking=False))
        elif len(map50_vals) > 0:
            checks.append(CheckResult("GP01", "GatePredictor", "det_mAP50 gate reachable",
                                      Verdict.INFO,
                                      f"{rf2_prefix}{len(map50_vals)} RF2 val point(s) — need 3 for prediction"))
        else:
            checks.append(CheckResult("GP01", "GatePredictor", "det_mAP50 gate reachable",
                                      Verdict.INFO,
                                      "No RF2 validation data yet — prediction impossible"))

        # GP02: MAE gate reachable
        reachable, predicted = extrapolate(mae_vals, GATE["forward_angular_MAE_deg"], remaining)
        if len(mae_vals) >= 3:
            detail = f"{rf2_prefix}Predicted E{max_epochs}: {predicted:.2f}°  Target: ≤{GATE['forward_angular_MAE_deg']}°"
            if reachable:
                checks.append(CheckResult("GP02", "GatePredictor", "MAE gate reachable",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("GP02", "GatePredictor", "MAE gate reachable",
                                          Verdict.WARN if predicted > 0 else Verdict.INFO, detail))
        else:
            checks.append(CheckResult("GP02", "GatePredictor", "MAE gate reachable",
                                      Verdict.INFO))

        # GP03: det_mAP50_95 gate reachable
        if GATE.get("det_mAP50_95") is not None:
            reachable, predicted = extrapolate(map50_95_vals, GATE["det_mAP50_95"], remaining)
            if len(map50_95_vals) >= 3:
                detail = f"{rf2_prefix}Predicted E{max_epochs}: {predicted:.4f}  Target: {GATE['det_mAP50_95']}"
                if reachable:
                    checks.append(CheckResult("GP03", "GatePredictor", "det_mAP50_95 gate reachable",
                                              Verdict.PASS, detail))
                else:
                    checks.append(CheckResult("GP03", "GatePredictor", "det_mAP50_95 gate reachable",
                                              Verdict.WARN, detail))
            else:
                checks.append(CheckResult("GP03", "GatePredictor", "det_mAP50_95 gate reachable",
                                          Verdict.INFO))
        else:
            checks.append(CheckResult("GP03", "GatePredictor", "det_mAP50_95 gate reachable",
                                      Verdict.INFO, "No target configured"))

        # GP04: Rate of improvement sufficient
        if len(map50_vals) >= 3:
            recent = map50_vals[-3:]
            slope = (recent[-1] - recent[0]) / 2
            needed = (GATE["det_mAP50"] - recent[-1]) / max(remaining, 1)
            on_track = slope >= needed * 0.5 if needed > 0 else True
            checks.append(CheckResult("GP04", "GatePredictor", "Rate of improvement sufficient",
                                      Verdict.PASS if on_track else Verdict.WARN,
                                      f"{rf2_prefix}Recent slope: {slope:.4f}/epoch  Needed: {needed:.4f}/epoch"))
        else:
            checks.append(CheckResult("GP04", "GatePredictor", "Rate of improvement sufficient",
                                      Verdict.INFO))

        # GP05: Prediction is stable
        if len(map50_vals) >= 5:
            recent_var = sum((v - sum(map50_vals[-5:]) / 5) ** 2 for v in map50_vals[-5:]) / 5
            stable = recent_var < 0.01
            checks.append(CheckResult("GP05", "GatePredictor", "Prediction is stable",
                                      Verdict.PASS if stable else Verdict.WARN,
                                      f"5-epoch variance: {recent_var:.6f}"))
        else:
            checks.append(CheckResult("GP05", "GatePredictor", "Prediction is stable",
                                      Verdict.INFO))

        # GP06: Sufficient epochs at current rate
        if len(map50_vals) >= 3 and remaining > 0:
            recent = map50_vals[-3:]
            slope = (recent[-1] - recent[0]) / 2
            if slope > 0:
                epochs_needed = (GATE["det_mAP50"] - recent[-1]) / slope
                enough = epochs_needed <= remaining
                checks.append(CheckResult("GP06", "GatePredictor", "Sufficient epochs at current rate",
                                          Verdict.PASS if enough else Verdict.WARN,
                                          f"Need {epochs_needed:.1f} more epochs, have {remaining}"))
            else:
                checks.append(CheckResult("GP06", "GatePredictor", "Sufficient epochs at current rate",
                                          Verdict.INFO, "Slope is flat or negative — need more data"))
        else:
            checks.append(CheckResult("GP06", "GatePredictor", "Sufficient epochs at current rate",
                                      Verdict.INFO))

        # GP07: LR restart guard — downgrade predictions to INFO near restart
        t_0 = LR_RESTART["t_0"]
        grace = LR_RESTART["grace_epochs"]
        in_restart = abs(current_epoch - t_0) < grace
        if in_restart:
            checks.append(CheckResult("GP07", "GatePredictor", "LR restart grace window",
                                      Verdict.INFO,
                                      f"LR restart at E{t_0} ±{grace-1} epochs — predictions unreliable"))
            for c in checks:
                if c.uid in ("GP01", "GP02", "GP03", "GP04", "GP05", "GP06") and c.verdict in (Verdict.FAIL, Verdict.WARN):
                    c.verdict = Verdict.INFO
        else:
            next_restart = t_0
            while next_restart <= current_epoch:
                next_restart += t_0
            checks.append(CheckResult("GP07", "GatePredictor", "LR restart grace window",
                                      Verdict.PASS,
                                      f"Next LR restart at ~E{next_restart}"))

        return AgentResult(self.name, checks)
