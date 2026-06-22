"""Agent 02: ProbeAnalyzerAgent — DET_PROBE diagnostics, step validation, detector progress."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

# DET_PROBE: [DET_PROBE b0] {'tag': 'b0', ...} | verdict: LOCALIZING
PROBE_VERDICT_RE = re.compile(
    r"\[DET_PROBE\s+\S+\]\s+\{.*?\}\s+\|\s+verdict:\s*(\S+)"
)
# STEP VAL: [STEP VAL gs=1000] det_mAP50=0.0000  act_F1=0.0000  psr_F1=0.0000  pose_MAE=0.0000
STEP_VAL_RE = re.compile(
    r"\[STEP VAL gs=(\d+)\]\s+det_mAP50=([\d.]+)\s+act_F1=([\d.]+)\s+psr_F1=([\d.]+)\s+pose_MAE=([\d.]+)"
)
# DET_PROBE JSON field extraction
PROBE_PREDS_RE = re.compile(r"'preds>0\.05':\s*(\d+)")
PROBE_IOU_RE = re.compile(r"'bestIoU>0\.5':\s*(\d+)")
PROBE_IOU_MAX_RE = re.compile(r"'bestIoU_max':\s*([\d.]+)")


class ProbeAnalyzerAgent(BaseAgent):
    """Analyzes DET_PROBE diagnostics and step-level validation results."""

    def __init__(self):
        super().__init__("ProbeAnalyzer")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        # P01: DET_PROBE verdicts
        verdicts = PROBE_VERDICT_RE.findall(log_text)
        if verdicts:
            unique = set(verdicts)
            all_ok = all(v.upper() in ("LOCALIZING", "LEARNING", "ALIVE", "OK") for v in unique)
            summary = ", ".join(f"{v}={verdicts.count(v)}" for v in sorted(unique))
            checks.append(CheckResult(
                "P01", "ProbeAnalyzer", "DET_PROBE verdicts",
                Verdict.PASS if all_ok else Verdict.WARN,
                f"{len(verdicts)} probes: {summary}"
            ))
        else:
            checks.append(CheckResult(
                "P01", "ProbeAnalyzer", "DET_PROBE verdicts",
                Verdict.INFO, "No DET_PROBE verdicts found (early training)"
            ))

        # P02: Step validation mAP
        step_vals = STEP_VAL_RE.findall(log_text)
        if step_vals:
            latest = step_vals[-1]
            gs, map50, act_f1, psr_f1, pose_mae = latest
            # First step val typically shows 0.0000 mAP (early training)
            first_val = float(map50) == 0 and len(step_vals) <= 1
            checks.append(CheckResult(
                "P02", "ProbeAnalyzer", "Step validation mAP",
                Verdict.INFO if first_val else Verdict.PASS if float(map50) > 0 else Verdict.FAIL,
                f"gs={gs}  det_mAP50={map50}  act_F1={act_f1}  psr_F1={psr_f1}  pose_MAE={pose_mae}"
            ))

            # P03: Step validation mAP trend
            if len(step_vals) >= 2:
                vals = [float(s[1]) for s in step_vals]
                improving = vals[-1] >= vals[0]
                checks.append(CheckResult(
                    "P03", "ProbeAnalyzer", "Step validation mAP trend",
                    Verdict.PASS if improving else Verdict.WARN,
                    f"mAP50: {vals[0]} → {vals[-1]}"
                ))
            else:
                checks.append(CheckResult(
                    "P03", "ProbeAnalyzer", "Step validation mAP trend",
                    Verdict.INFO, f"Single step val: mAP50={map50}"
                ))

            # P04: Pose MAE
            pose_vals = [float(s[4]) for s in step_vals]
            checks.append(CheckResult(
                "P04", "ProbeAnalyzer", "Pose MAE from step val",
                Verdict.INFO, f"Pose MAE: {pose_vals[-1]}"
            ))
        else:
            for uid, desc in [("P02", "Step validation mAP"),
                              ("P03", "Step validation mAP trend"),
                              ("P04", "Pose MAE from step val")]:
                checks.append(CheckResult(uid, "ProbeAnalyzer", desc,
                                          Verdict.INFO, "No step val data yet"))

        # P05: DET_PROBE prediction counts
        preds = [int(m) for m in PROBE_PREDS_RE.findall(log_text)]
        if preds:
            avg_preds = sum(preds) / len(preds)
            any_zero = any(p == 0 for p in preds)
            checks.append(CheckResult(
                "P05", "ProbeAnalyzer", "DET_PROBE prediction counts",
                Verdict.FAIL if any_zero else Verdict.PASS,
                f"preds>0.05: avg={avg_preds:.0f}  min={min(preds)}  max={max(preds)}"
            ))
        else:
            checks.append(CheckResult(
                "P05", "ProbeAnalyzer", "DET_PROBE prediction counts",
                Verdict.INFO, "No probe prediction data"
            ))

        # P06: Probe bestIoU statistics
        iou_vals = [int(m) for m in PROBE_IOU_RE.findall(log_text)]
        iou_max_vals = [float(m) for m in PROBE_IOU_MAX_RE.findall(log_text)]
        if iou_vals:
            avg_iou = sum(iou_vals) / len(iou_vals)
            best_iou = max(iou_max_vals) if iou_max_vals else 0
            checks.append(CheckResult(
                "P06", "ProbeAnalyzer", "Probe bestIoU statistics",
                Verdict.PASS if avg_iou > 100 else Verdict.INFO,
                f"avg bestIoU>0.5: {avg_iou:.0f}  max bestIoU_max: {best_iou:.2f}"
            ))
        else:
            checks.append(CheckResult(
                "P06", "ProbeAnalyzer", "Probe bestIoU statistics",
                Verdict.INFO, "No probe IoU data"
            ))

        # P07: DET_PROBE fires per eval batch
        eval_batches = len(re.findall(r"\[EVAL batch", log_text))
        probe_entries = len(re.findall(r"\[DET_PROBE", log_text))
        probe_vs_eval = probe_entries / max(eval_batches, 1) if eval_batches > 0 else 0
        if eval_batches > 0:
            checks.append(CheckResult(
                "P07", "ProbeAnalyzer", "DET_PROBE frequency",
                Verdict.PASS if probe_vs_eval >= 1 else Verdict.WARN,
                f"{probe_entries} probes across {eval_batches} eval batches ({probe_vs_eval:.1f}x)"
            ))
        else:
            checks.append(CheckResult(
                "P07", "ProbeAnalyzer", "DET_PROBE frequency",
                Verdict.INFO, "No eval batches yet"
            ))

        return AgentResult(self.name, checks)
