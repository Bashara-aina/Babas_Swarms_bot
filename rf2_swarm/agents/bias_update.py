"""Agent 22: BiasUpdateAgent — monitors bias parameter update rates.

Verifies that the detection head bias parameters are actually being updated
at the expected rate. The cls_preds stagnation bug was caused by bias params
getting stuck due to BIAS_LR_FACTOR=0.3. This agent tracks bias values over
time and alerts if the update rate deviates from expectations.
"""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text

# Match param group lr output: "det_head_bias=5x, bias=0.3x" etc.
PARAM_GROUP_RE = re.compile(
    r"AdamW.*?differential LR.*?(\(.*?\))"
)
ALL_GROUPS_RE = re.compile(
    r"(backbone|det_head|heads|act/psr|det_head_bias|bias|videomae|loss)=([\d.]+)x"
)

# Match debug loss lines: "det_cls=1.7846 det_reg=0.0072"
DET_LOSS_RE = re.compile(r"det_cls=([\d.]+)\s+det_reg=([\d.]+)")

# Match bias gradient norms (if logged)
BIAS_GRAD_RE = re.compile(r"det_head.*?bias.*?grad.*?([\d.]+)", re.IGNORECASE)

# Match "Resumed from epoch" for bias state info
RESUME_EPOCH_RE = re.compile(r"Resumed from epoch (\d+)")

# Match any loading of cls_score.bias value
CLS_BIAS_LOAD_RE = re.compile(r"cls_score\.bias.*?([-\d.]+)")


class BiasUpdateAgent(BaseAgent):
    """Monitors bias parameter update rates for the detection head."""

    def __init__(self):
        super().__init__("BiasUpdate")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        log_head_text = ctx.get("log_head_text", "")
        run_text = current_run_text(log_text)
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        # BU01: Verify all expected param groups present in optimizer
        # Search tail first, fall back to startup head (params logged once at ~line 100)
        groups = dict(ALL_GROUPS_RE.findall(log_text))
        if not groups:
            groups = dict(ALL_GROUPS_RE.findall(log_head_text))
        expected_groups = {"backbone", "det_head", "heads", "det_head_bias", "bias"}
        missing = expected_groups - set(groups.keys())
        if missing:
            checks.append(CheckResult(
                "BU01", "BiasUpdate", "All param groups present",
                Verdict.FAIL if "det_head_bias" in missing else Verdict.WARN,
                f"Missing groups: {missing}",
                blocking="det_head_bias" in missing,
            ))
        else:
            checks.append(CheckResult(
                "BU01", "BiasUpdate", "All param groups present",
                Verdict.PASS,
                f"LR factors: {', '.join(f'{k}={v}x' for k, v in sorted(groups.items()))}",
            ))

        # BU02: det_head_bias LR factor expectation
        # Config was reverted from 5.0→1.0 (2026-06-20): 5× drove bias into background
        # equilibrium faster. The bias follows dead-feature gradients, not stuck.
        # See config.py DET_BIAS_LR_FACTOR comment.
        bias_factor = groups.get("det_head_bias")
        if bias_factor is not None:
            bias_ok = float(bias_factor) >= 0.5
            checks.append(CheckResult(
                "BU02", "BiasUpdate", "det_head_bias LR factor sufficient",
                Verdict.PASS if bias_ok else Verdict.FAIL,
                f"det_head_bias={bias_factor}x",
                blocking=not bias_ok,
            ))
        else:
            checks.append(CheckResult(
                "BU02", "BiasUpdate", "det_head_bias LR factor sufficient",
                Verdict.SKIP,
            ))

        # BU03: det_cls loss trending downward (indicates bias is learning)
        det_losses = [(float(m.group(1)), float(m.group(2)))
                      for m in DET_LOSS_RE.finditer(run_text)]
        if len(det_losses) >= 10:
            # Compare first 5 vs last 5
            early = sum(d[0] for d in det_losses[:5]) / 5
            late = sum(d[0] for d in det_losses[-5:]) / 5
            decreasing = late < early * 0.9  # At least 10% decrease
            checks.append(CheckResult(
                "BU03", "BiasUpdate", "det_cls loss trending downward",
                Verdict.PASS if decreasing else Verdict.WARN,
                f"det_cls: {early:.4f} → {late:.4f} "
                f"({'decreasing' if decreasing else 'flat/increasing'})",
            ))
        elif det_losses:
            checks.append(CheckResult(
                "BU03", "BiasUpdate", "det_cls loss trending downward",
                Verdict.INFO, f"Only {len(det_losses)} samples so far",
            ))
        else:
            checks.append(CheckResult(
                "BU03", "BiasUpdate", "det_cls loss trending downward",
                Verdict.INFO, "No det_cls loss entries in current run",
            ))

        # BU04: Running epoch from state vs last resume epoch
        resume_epochs = [int(m.group(1)) for m in RESUME_EPOCH_RE.finditer(log_text)]
        current_epoch = state.get("epoch", 0)
        if resume_epochs:
            last_resume = max(resume_epochs)
            if current_epoch > last_resume:
                checks.append(CheckResult(
                    "BU04", "BiasUpdate", "Training advancing past resume point",
                    Verdict.PASS,
                    f"Resumed at epoch {last_resume}, now at epoch {current_epoch}",
                ))
            else:
                checks.append(CheckResult(
                    "BU04", "BiasUpdate", "Training advancing past resume point",
                    Verdict.INFO, f"At epoch {current_epoch} (resumed from {last_resume})",
                ))
        else:
            checks.append(CheckResult(
                "BU04", "BiasUpdate", "Training advancing past resume point",
                Verdict.INFO, "No resume detected",
            ))

        # BU05: Positive predictions ratio improving over time (cross-cycle)
        prev = ctx.get("prev_results", {}).get("BiasUpdate", [])
        probe_dicts = self._parse_probes(run_text)
        if probe_dicts:
            preds_05 = [p.get("preds>0.05", 0) for p in probe_dicts]
            preds_01 = [p.get("preds>0.01", 1) for p in probe_dicts]
            ratios = [a / max(b, 1) for a, b in zip(preds_05, preds_01)]
            latest_ratio = ratios[-1] if ratios else 0
            # Compare with previous cycle
            prev_ratio = None
            for c in prev:
                if c.get("uid") == "BU05":
                    try:
                        prev_ratio = float(c.get("detail", "0").split("=")[-1])
                    except (ValueError, IndexError):
                        pass
            improving = prev_ratio is not None and latest_ratio > prev_ratio * 1.05
            checks.append(CheckResult(
                "BU05", "BiasUpdate", "Positive prediction ratio improving",
                Verdict.PASS if improving else Verdict.INFO,
                f"preds>0.05 ratio={latest_ratio*100:.2f}% "
                f"({'improving' if improving else 'stable/declining'})"
                + (f" (prev={prev_ratio*100:.2f}%)" if prev_ratio else ""),
            ))
        else:
            checks.append(CheckResult(
                "BU05", "BiasUpdate", "Positive prediction ratio improving",
                Verdict.INFO, "No DET_PROBE data",
            ))

        return AgentResult(self.name, checks)

    def _parse_probes(self, text: str) -> list[dict[str, Any]]:
        """Parse DET_PROBE JSON from log text."""
        import json
        results = []
        for m in re.finditer(r"\[DET_PROBE\s+\S+\]\s+(\{.*?\})\s+\| verdict:", text):
            try:
                results.append(json.loads(m.group(1)))
            except (json.JSONDecodeError, KeyError):
                continue
        return results
