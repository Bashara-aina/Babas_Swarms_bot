"""Agent 04: LossHealthAgent — loss values, plateau detection, divergence checking."""

from __future__ import annotations
import math
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

# DEBUG lines: det_cls=0.6179  det_reg=0.4364  head_pose=0.0190  act=0.0000  psr=0.0000
LOSS_RE = re.compile(
    r"(det_cls|det_reg|head_pose|act|psr)\s*=\s*([\d.]+)"
)
# Inline tqdm: det=1.2386(c=0.5381,g=0.3502) — c→det_cls, g→det_reg
INLINE_LOSS_RE = re.compile(r"(?:^|\s|\()(c|g)\s*=\s*([\d.]+)")
# Total from DEBUG: total=3.7136  or tqdm: loss=2.6158
TOTAL_LOSS_RE = re.compile(r"(?:total|loss)\s*=\s*([\d.]+)")
# Statistical outlier detection replaces keyword-based spike matching.
# A spike is defined as a loss value > mean + SPIKE_STD_THRESH * std.
SPIKE_STD_THRESH = 3.0


class LossHealthAgent(BaseAgent):
    """Monitors all training loss values."""

    def __init__(self):
        super().__init__("LossHealth")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        losses = LOSS_RE.findall(log_text)
        # Parse tqdm inline components: c=det_cls, g=det_reg
        inline_map = {'c': 'det_cls', 'g': 'det_reg'}
        for m in INLINE_LOSS_RE.finditer(log_text):
            losses.append((inline_map[m.group(1)], m.group(2)))
        total_losses = [float(m.group(1)) for m in TOTAL_LOSS_RE.finditer(log_text)]

        # Group loss values by name
        loss_by_name: dict[str, list[float]] = {}
        for name, val in losses:
            loss_by_name.setdefault(name, []).append(float(val))

        # L01: det_cls loss finite and reasonable
        det_cls = loss_by_name.get("det_cls", [])
        if det_cls:
            latest = det_cls[-1]
            reasonable = 0 < latest < 10.0
            checks.append(CheckResult("L01", "LossHealth", "det_cls loss reasonable",
                                      Verdict.PASS if reasonable else Verdict.WARN,
                                      f"latest={latest:.4f}"))
        else:
            checks.append(CheckResult("L01", "LossHealth", "det_cls loss reasonable",
                                      Verdict.INFO, "No det_cls loss entries"))

        # L02: det_reg (box regression) loss finite and reasonable
        det_reg = loss_by_name.get("det_reg", [])
        if det_reg:
            latest = det_reg[-1]
            reasonable = 0 < latest < 10.0
            checks.append(CheckResult("L02", "LossHealth", "det_reg loss reasonable",
                                      Verdict.PASS if reasonable else Verdict.WARN,
                                      f"latest={latest:.4f}"))
        else:
            checks.append(CheckResult("L02", "LossHealth", "det_reg loss reasonable",
                                      Verdict.INFO, "No det_reg loss entries"))

        # L03: Head pose loss finite
        head_pose = loss_by_name.get("head_pose", [])
        if head_pose:
            latest = head_pose[-1]
            finite = 0 < latest < 20.0
            checks.append(CheckResult("L03", "LossHealth", "Head pose loss finite",
                                      Verdict.PASS if finite else Verdict.WARN,
                                      f"latest={latest:.4f}"))
        else:
            checks.append(CheckResult("L03", "LossHealth", "Head pose loss finite",
                                      Verdict.INFO))

        # L04: PSR loss finite
        psr = loss_by_name.get("psr", [])
        if psr:
            latest = psr[-1]
            finite = 0 < latest < 20.0
            checks.append(CheckResult("L04", "LossHealth", "PSR loss finite",
                                      Verdict.PASS if finite else Verdict.WARN,
                                      f"latest={latest:.4f}"))
        else:
            checks.append(CheckResult("L04", "LossHealth", "PSR loss finite",
                                      Verdict.INFO))

        # L05: Total loss not NaN/inf
        if total_losses:
            latest = total_losses[-1]
            ok = not (math.isnan(latest) or math.isinf(latest))
            checks.append(CheckResult("L05", "LossHealth", "Total loss is finite",
                                      Verdict.PASS if ok else Verdict.FAIL,
                                      f"total_loss={latest}", blocking=not ok))
        else:
            checks.append(CheckResult("L05", "LossHealth", "Total loss is finite",
                                      Verdict.INFO))

        # L06: No loss spikes — statistical outlier detection
        if len(total_losses) >= 10:
            mean = sum(total_losses) / len(total_losses)
            variance = sum((v - mean) ** 2 for v in total_losses) / len(total_losses)
            std = math.sqrt(variance)
            threshold = mean + SPIKE_STD_THRESH * std
            outliers = [v for v in total_losses if v > threshold]
            if outliers:
                checks.append(CheckResult("L06", "LossHealth", "No loss spikes or divergence",
                                          Verdict.WARN,
                                          f"{len(outliers)}/{len(total_losses)} outliers "
                                          f"({SPIKE_STD_THRESH}σ threshold={threshold:.2f}, "
                                          f"mean={mean:.4f}, std={std:.4f})",
                                          blocking=False))
            else:
                checks.append(CheckResult("L06", "LossHealth", "No loss spikes or divergence",
                                          Verdict.PASS,
                                          f"mean={mean:.4f}, std={std:.4f}, "
                                          f"{SPIKE_STD_THRESH}σ threshold={threshold:.2f}"))
        elif total_losses:
            checks.append(CheckResult("L06", "LossHealth", "No loss spikes or divergence",
                                      Verdict.INFO, f"Only {len(total_losses)} samples (< 10 needed)"))
        else:
            checks.append(CheckResult("L06", "LossHealth", "No loss spikes or divergence",
                                      Verdict.INFO))

        # L07: det_cls loss decreasing trend (last vs first)
        if len(det_cls) >= 3:
            decreasing = det_cls[-1] < det_cls[0] * 0.9
            checks.append(CheckResult("L07", "LossHealth", "det_cls loss decreasing",
                                      Verdict.PASS if decreasing else Verdict.WARN,
                                      f"{det_cls[0]:.4f} → {det_cls[-1]:.4f}"))
        else:
            checks.append(CheckResult("L07", "LossHealth", "det_cls loss decreasing",
                                      Verdict.INFO))

        # L08: All loss entries positive
        all_loss_vals = [v for vals in loss_by_name.values() for v in vals]
        if all_loss_vals:
            neg = sum(1 for v in all_loss_vals if v <= 0)
            checks.append(CheckResult("L08", "LossHealth", "All loss values positive",
                                      Verdict.WARN if neg > 0 else Verdict.PASS,
                                      f"{neg} non-positive loss values"))
        else:
            checks.append(CheckResult("L08", "LossHealth", "All loss values positive",
                                      Verdict.INFO))

        return AgentResult(self.name, checks)
