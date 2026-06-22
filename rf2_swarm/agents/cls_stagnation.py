"""Agent 21: ClsStagnationAgent — detects detection classifier stagnation patterns.

This agent specifically watches for the cls_preds stagnation bug that was found:
low confidence scores (score_p50 ~0.02), zero predictions above 0.30 threshold,
and narrow score distribution. It tracks these metrics across cycles to detect
when the classifier gets stuck producing near-uniform background predictions.
"""

from __future__ import annotations
import json
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text

DET_PROBE_RE = re.compile(
    r"\[DET_PROBE\s+\S+\]\s+(\{.*?\})\s+\| verdict:"
)
SCORE_BIAS_RE = re.compile(
    r"detection_head\.cls_score\.bias.*?\[([-\d.e+,\s]+)\]"
)
OPTIMIZER_BIAS_RE = re.compile(
    r"det_head_bias.*?([\d.]+)x"
)


class ClsStagnationAgent(BaseAgent):
    """Detects when the detection classifier confidence is stuck or regressing."""

    def __init__(self):
        super().__init__("ClsStagnation")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        log_head_text = ctx.get("log_head_text", "")
        run_text = current_run_text(log_text)
        checks: list[CheckResult] = []

        # Parse per-batch DET_PROBE results
        probe_dicts = self._parse_probes(run_text)

        # CS01: score_p50 trend — median confidence increasing?
        if probe_dicts:
            p50s = [p.get("score_p50", 0) for p in probe_dicts]
            avg_p50 = sum(p50s) / len(p50s)
            max_p50 = max(p50s)
            min_p50 = min(p50s)
            # Check if ALL probes have nearly identical score_p50 (stagnation signal)
            p50_range = max_p50 - min_p50
            stuck = p50_range < 0.001 and len(p50s) >= 5
            checks.append(CheckResult(
                "CS01", "ClsStagnation", "score_p50 confidence trend",
                Verdict.FAIL if stuck else Verdict.PASS,
                f"p50_range={p50_range:.6f}, avg_p50={avg_p50:.6f}, max_p50={max_p50:.6f}"
                + (" — STUCK: all probes near-identical p50" if stuck else ""),
                blocking=stuck,
            ))
        else:
            checks.append(CheckResult(
                "CS01", "ClsStagnation", "score_p50 confidence trend",
                Verdict.INFO, "No DET_PROBE results in current run",
            ))

        # CS02: any predictions above 0.30 confidence?
        if probe_dicts:
            preds_above_30 = [p.get("preds>0.30", 0) for p in probe_dicts]
            total_above_30 = sum(preds_above_30)
            verdict = Verdict.PASS if total_above_30 > 0 else Verdict.WARN
            checks.append(CheckResult(
                "CS02", "ClsStagnation", "Predictions above 0.30 confidence",
                verdict,
                f"Total preds>0.30 across {len(probe_dicts)} probes: {total_above_30}"
                + (" — ZERO confident predictions, classifier stuck" if total_above_30 == 0 else ""),
            ))
        else:
            checks.append(CheckResult(
                "CS02", "ClsStagnation", "Predictions above 0.30 confidence",
                Verdict.INFO,
            ))

        # CS03: score distribution health — ratio of preds>0.05 to total preds
        if probe_dicts:
            ratios = []
            for p in probe_dicts:
                total = p.get("preds>0.01", 1)
                above_05 = p.get("preds>0.05", 0)
                ratios.append(above_05 / max(total, 1))
            avg_ratio = sum(ratios) / len(ratios)
            # Healthy: >3% of predictions above 0.05
            # Stuck: <3% (means almost all predictions are in the noise floor)
            healthy = avg_ratio > 0.03
            checks.append(CheckResult(
                "CS03", "ClsStagnation", "Score distribution health (preds>0.05 ratio)",
                Verdict.PASS if healthy else Verdict.WARN,
                f"Avg preds>0.05 ratio: {avg_ratio*100:.2f}% "
                f"(range: {min(ratios)*100:.2f}%-{max(ratios)*100:.2f}%)",
            ))
        else:
            checks.append(CheckResult(
                "CS03", "ClsStagnation", "Score distribution health",
                Verdict.INFO,
            ))

        # CS04: score_max trend — max confidence increasing?
        if probe_dicts:
            max_scores = [p.get("score_max", 0) for p in probe_dicts]
            best_max = max(max_scores)
            improving = len(max_scores) >= 2 and max_scores[-1] > max_scores[0] * 1.1
            checks.append(CheckResult(
                "CS04", "ClsStagnation", "score_max confidence trend",
                Verdict.PASS if (best_max > 0.3 or improving) else Verdict.WARN,
                f"best score_max={best_max:.4f}, "
                f"latest={max_scores[-1]:.4f}, "
                f"trend={'improving' if improving else 'flat/declining'}",
            ))
        else:
            checks.append(CheckResult(
                "CS04", "ClsStagnation", "score_max confidence trend",
                Verdict.INFO,
            ))

        # CS05: cls_score bias values from optimizer/checkpoint logs
        bias_matches = SCORE_BIAS_RE.findall(log_text)
        if bias_matches:
            latest_bias_str = bias_matches[-1]
            bias_vals = [float(x.strip()) for x in latest_bias_str.split(",") if x.strip()]
            if bias_vals:
                avg_bias = sum(bias_vals) / len(bias_vals)
                min_bias = min(bias_vals)
                max_bias = max(bias_vals)
                # With pi=0.05 initialization, bias ≈ -2.944
                # After fix with 5x LR, bias should move toward -1.5 to -2.0
                # Stuck bias near -4.595 (old pi=0.01 init) indicates problem
                bias_improving = avg_bias > -3.5  # moving away from pi=0.01 init
                checks.append(CheckResult(
                    "CS05", "ClsStagnation", "cls_score bias values",
                    Verdict.PASS if bias_improving else Verdict.WARN,
                    f"avg_bias={avg_bias:.4f}, range=[{min_bias:.4f}, {max_bias:.4f}], "
                    f"{len(bias_vals)} bias values",
                ))
            else:
                checks.append(CheckResult(
                    "CS05", "ClsStagnation", "cls_score bias values",
                    Verdict.INFO, "Bias values found but unparseable",
                ))
        else:
            checks.append(CheckResult(
                "CS05", "ClsStagnation", "cls_score bias values",
                Verdict.INFO, "No bias values in log (expected during training)",
            ))

        # CS06: det_head_bias param group active in optimizer
        opt_bias = OPTIMIZER_BIAS_RE.search(log_text)
        if not opt_bias and log_head_text:
            opt_bias = OPTIMIZER_BIAS_RE.search(log_head_text)
        checks.append(CheckResult(
            "CS06", "ClsStagnation", "det_head_bias param group active",
            Verdict.PASS if opt_bias else Verdict.FAIL,
            f"det_head_bias={opt_bias.group(1)}x" if opt_bias else "det_head_bias param group NOT found",
            blocking=opt_bias is None,
        ))

        return AgentResult(self.name, checks)

    def _parse_probes(self, text: str) -> list[dict[str, Any]]:
        """Parse per-batch DET_PROBE JSON dicts from log text."""
        results = []
        for m in DET_PROBE_RE.finditer(text):
            try:
                data = json.loads(m.group(1))
                results.append(data)
            except (json.JSONDecodeError, KeyError):
                continue
        return results
