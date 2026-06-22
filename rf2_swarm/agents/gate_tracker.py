"""Agent 01: GateTrackerAgent — gate metric thresholds, best-vs-current, gate_passed flag.

Uses RF2-only validation data to avoid RF1 data pollution.
"""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text
from ..config import GATE, LR_RESTART, VAL_FLOORS

VAL_RE = re.compile(
    r"Val:.*det_mAP50=([\d.]+).*forward_angular_MAE_deg=([\d.]+)"
)
VAL_MAP50_95_RE = re.compile(r"Val:.*det_mAP50_95=([\d.]+)")
BEST_RE = re.compile(r"New best model.*combined=([\d.]+)")


class GateTrackerAgent(BaseAgent):
    """Tracks primary gate metrics against targets."""

    def __init__(self):
        super().__init__("GateTracker")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        # Current run validation data (filters out old runs)
        run_text = current_run_text(log_text)
        val_lines = VAL_RE.findall(run_text)
        map50_95_lines = VAL_MAP50_95_RE.findall(run_text)

        best_lines = BEST_RE.findall(log_text)

        latest_map50 = float(val_lines[-1][0]) if val_lines else None
        latest_mae = float(val_lines[-1][1]) if val_lines else None
        latest_map50_95 = float(map50_95_lines[-1]) if map50_95_lines else None

        current_epoch = state.get("epoch", 0)
        max_epochs = state.get("max_epochs", 21)
        gate_passed = state.get("gate_passed", False)
        has_rf2_val = len(val_lines) > 0

        # G01: Has any RF2 validation occurred?
        if has_rf2_val:
            checks.append(CheckResult("G01", "GateTracker", "RF2 validation has occurred",
                                      Verdict.PASS, f"{len(val_lines)} RF2 val result(s)"))
        else:
            checks.append(CheckResult("G01", "GateTracker", "RF2 validation has occurred",
                                      Verdict.INFO, "No RF2 validation data yet — in-progress",
                                      blocking=False))

        # G02: det_mAP50 gate target (non-blocking — expected to be unmet mid-training)
        if latest_map50 is not None:
            detail = f"det_mAP50={latest_map50:.4f}  target≥{GATE['det_mAP50']}  [RF2]"
            if latest_map50 >= GATE["det_mAP50"]:
                checks.append(CheckResult("G02", "GateTracker", "det_mAP50 meets gate target",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("G02", "GateTracker", "det_mAP50 meets gate target",
                                          Verdict.WARN, detail))
        else:
            checks.append(CheckResult("G02", "GateTracker", "det_mAP50 meets gate target",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G03: det_mAP50_95 gate target
        mAP50_95_target = GATE.get("det_mAP50_95")
        if mAP50_95_target is not None and latest_map50_95 is not None:
            detail = f"det_mAP50_95={latest_map50_95:.4f}  target≥{mAP50_95_target}"
            if latest_map50_95 >= mAP50_95_target:
                checks.append(CheckResult("G03", "GateTracker", "det_mAP50_95 meets gate target",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("G03", "GateTracker", "det_mAP50_95 meets gate target",
                                          Verdict.FAIL, detail, blocking=True))
        else:
            checks.append(CheckResult("G03", "GateTracker", "det_mAP50_95 meets gate target",
                                      Verdict.INFO, "No RF2 data or no target configured"))

        # G04: MAE gate target
        if latest_mae is not None:
            detail = f"MAE={latest_mae:.2f}°  target≤{GATE['forward_angular_MAE_deg']}°  [RF2]"
            if latest_mae <= GATE["forward_angular_MAE_deg"]:
                checks.append(CheckResult("G04", "GateTracker", "Forward angular MAE meets gate target",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("G04", "GateTracker", "Forward angular MAE meets gate target",
                                          Verdict.FAIL, detail, blocking=True))
        else:
            checks.append(CheckResult("G04", "GateTracker", "Forward angular MAE meets gate target",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G05: det_mAP50 above val floor
        if latest_map50 is not None:
            detail = f"det_mAP50={latest_map50:.4f}  floor≥{VAL_FLOORS['det_mAP50']}  [RF2]"
            if latest_map50 >= VAL_FLOORS["det_mAP50"]:
                checks.append(CheckResult("G05", "GateTracker", "det_mAP50 above validation floor",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("G05", "GateTracker", "det_mAP50 above validation floor",
                                          Verdict.WARN, detail))
        else:
            checks.append(CheckResult("G05", "GateTracker", "det_mAP50 above validation floor",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G06: MAE below val floor
        if latest_mae is not None:
            detail = f"MAE={latest_mae:.2f}°  floor≤{VAL_FLOORS['forward_angular_MAE_deg']}°  [RF2]"
            if latest_mae <= VAL_FLOORS["forward_angular_MAE_deg"]:
                checks.append(CheckResult("G06", "GateTracker", "MAE below validation floor",
                                          Verdict.PASS, detail))
            else:
                checks.append(CheckResult("G06", "GateTracker", "MAE below validation floor",
                                          Verdict.WARN, detail))
        else:
            checks.append(CheckResult("G06", "GateTracker", "MAE below validation floor",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G07: Gate passed flag
        if gate_passed:
            checks.append(CheckResult("G07", "GateTracker", "Gate passed flag is set",
                                      Verdict.PASS, "Training has passed all gate criteria"))
        else:
            checks.append(CheckResult("G07", "GateTracker", "Gate passed flag is set",
                                      Verdict.INFO, "Gate not yet passed"))

        # G08: Epochs remaining
        remaining = max_epochs - current_epoch
        if remaining >= 0:
            checks.append(CheckResult("G08", "GateTracker", "Sufficient epochs remain for gate",
                                      Verdict.PASS if remaining >= 3 else Verdict.WARN,
                                      f"{remaining}/{max_epochs} epochs remaining"))
        else:
            checks.append(CheckResult("G08", "GateTracker", "Sufficient epochs remain for gate",
                                      Verdict.FAIL, f"Epoch {current_epoch} exceeds max {max_epochs}", blocking=True))

        # G09: Best det_mAP50 trend
        if len(best_lines) >= 2:
            best_vals = [float(x) for x in best_lines]
            best_val = max(best_vals)
            improving = best_vals[-1] >= best_vals[-2]
            checks.append(CheckResult("G09", "GateTracker", "Best det_mAP50 is improving",
                                      Verdict.PASS if improving else Verdict.WARN,
                                      f"Best={best_val:.4f}  {'up' if improving else 'flat/down'}"))
        elif best_lines:
            best_val = float(best_lines[-1])
            checks.append(CheckResult("G09", "GateTracker", "Best det_mAP50 is improving",
                                      Verdict.INFO, f"Best so far: {best_val:.4f}"))
        else:
            checks.append(CheckResult("G09", "GateTracker", "Best det_mAP50 is improving",
                                      Verdict.INFO, "No best model records yet"))

        # G10: Combined metric (RF2 data only)
        if latest_map50 is not None and latest_mae is not None:
            mae_norm = max(0, 1 - latest_mae / 180)
            combined = latest_map50 * 0.6 + mae_norm * 0.4
            checks.append(CheckResult("G10", "GateTracker", "Combined gate metric",
                                      Verdict.PASS if combined >= 0.3 else Verdict.WARN,
                                      f"combined={combined:.4f}  [RF2]"))
        else:
            checks.append(CheckResult("G10", "GateTracker", "Combined gate metric",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G11: RF2-only mAP50 trend
        if len(val_lines) >= 3:
            recent = [float(v[0]) for v in val_lines[-3:]]
            trend = "↑" if recent[-1] > recent[0] else "↓" if recent[-1] < recent[0] else "→"
            checks.append(CheckResult("G11", "GateTracker", "det_mAP50 trend over last 3 vals",
                                      Verdict.PASS if trend == "↑" else Verdict.WARN,
                                      f"3-epoch RF2 trend: {recent[0]:.4f} → {recent[-1]:.4f} ({trend})"))
        elif len(val_lines) > 0:
            checks.append(CheckResult("G11", "GateTracker", "det_mAP50 trend over last 3 vals",
                                      Verdict.INFO, f"{len(val_lines)} RF2 val point(s) — need 3"))
        else:
            checks.append(CheckResult("G11", "GateTracker", "det_mAP50 trend over last 3 vals",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G12: RF2-only MAE trend
        if len(val_lines) >= 3:
            recent_mae = [float(v[1]) for v in val_lines[-3:]]
            improving = recent_mae[-1] <= recent_mae[0]
            checks.append(CheckResult("G12", "GateTracker", "MAE trend over last 3 vals",
                                      Verdict.PASS if improving else Verdict.WARN,
                                      f"MAE: {recent_mae[0]:.1f}° → {recent_mae[-1]:.1f}°  [RF2]"))
        elif len(val_lines) > 0:
            checks.append(CheckResult("G12", "GateTracker", "MAE trend over last 3 vals",
                                      Verdict.INFO, f"{len(val_lines)} RF2 val point(s) — need 3"))
        else:
            checks.append(CheckResult("G12", "GateTracker", "MAE trend over last 3 vals",
                                      Verdict.INFO, "No RF2 val data yet"))

        # G13: LR scheduler restart guard
        t_0 = LR_RESTART["t_0"]
        grace = LR_RESTART["grace_epochs"]
        in_restart = abs(current_epoch - t_0) < grace
        if in_restart:
            checks.append(CheckResult("G13", "GateTracker", "LR restart grace window",
                                      Verdict.INFO,
                                      f"LR restart at E{t_0} ±{grace-1} epochs — gate checks relaxed",
                                      blocking=False))
            # Downgrade any FAIL/WARN gate checks (G02-G06) to INFO during restart
            for c in checks:
                if c.uid in ("G02", "G03", "G04", "G05", "G06") and c.verdict in (Verdict.FAIL, Verdict.WARN):
                    c.verdict = Verdict.INFO
        else:
            next_restart = t_0
            while next_restart <= current_epoch:
                next_restart += t_0  # T_0 repeats for CosineAnnealingWarmRestarts
            checks.append(CheckResult("G13", "GateTracker", "LR restart grace window",
                                      Verdict.PASS,
                                      f"Next LR restart at ~E{next_restart}"))

        return AgentResult(self.name, checks)
