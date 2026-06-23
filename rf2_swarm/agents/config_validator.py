"""Agent 17: ConfigValidatorAgent — training config consistency, model architecture params.

Reads config from two sources:
  1. log_head_text (first 5K lines of log — config printed at startup)
  2. log_text (tail) for fallback / live patterns
"""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

# Key config patterns emitted by the training script at startup
BATCH_SIZE_RE = re.compile(r"(?:batch[_ ]?size)\s*\"?\s*[:=]\s*(\d+)", re.IGNORECASE)
LR_RE = re.compile(r"(?:base_lr|learning_rate|learning rate|LR|lr)\s*\"?\s*[:=]\s*([\d.e+\-]+)", re.IGNORECASE)
SUBSET_RE = re.compile(r"(?:subset[_\s]*ratio|subset[_\s]*size)\s*\"?\s*[:=]\s*([\d.]+)", re.IGNORECASE)
EPOCHS_RE = re.compile(r"(?:max_epochs?|epochs?)\s*\"?\s*[:=]\s*(\d+)", re.IGNORECASE)
ACCUM_RE = re.compile(r"(?:accum[_\s]*steps?|gradient_accumulation)\s*\"?\s*[:=]\s*(\d+)", re.IGNORECASE)
ACCUM_X_RE = re.compile(r"(?:batch|accum)[_\s]*size[^=]*[:=].*?x\s*(\d+)", re.IGNORECASE)

HEAD_CFG_RE = re.compile(r"(?:active_heads|heads)\s*\"?\s*[:=]\s*\"?([a-z_,\s]+)", re.IGNORECASE)
BACKBONE_RE = re.compile(r"backbone", re.IGNORECASE)
AMP_RE = re.compile(r"(?:amp|precision|fp16)", re.IGNORECASE)


class ConfigValidatorAgent(BaseAgent):
    """Validates training configuration consistency and model architecture."""

    def __init__(self):
        super().__init__("ConfigValidator")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_head = ctx.get("log_head_text", "")
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        # Head text has the startup config lines; tail text is fallback
        search_text = log_head if log_head else log_text

        # CV01: Batch size
        batch_size = self._find_value(search_text, BATCH_SIZE_RE)
        accum = self._find_value(search_text, ACCUM_RE)
        if accum is None:
            accum = self._find_value(search_text, ACCUM_X_RE)
        if batch_size is not None and accum is not None:
            effective = int(batch_size * accum)
            checks.append(CheckResult(
                "CV01", "ConfigValidator", "Effective batch size",
                Verdict.PASS if effective >= 16 else Verdict.WARN if effective >= 8 else Verdict.FAIL,
                f"Effective batch: {batch_size} × {accum} = {effective}"
            ))
        elif batch_size is not None:
            checks.append(CheckResult(
                "CV01", "ConfigValidator", "Effective batch size",
                Verdict.INFO, f"Batch size: {batch_size} (accum steps not found)"
            ))
        else:
            checks.append(CheckResult(
                "CV01", "ConfigValidator", "Effective batch size",
                Verdict.INFO, "Batch size not found in log"
            ))

        # CV02: Learning rate sanity
        lr = self._find_value(search_text, LR_RE)
        if lr is not None:
            checks.append(CheckResult(
                "CV02", "ConfigValidator", "Learning rate sanity",
                Verdict.PASS if 1e-6 <= lr <= 1e-3 else Verdict.FAIL if lr < 1e-6 else Verdict.WARN,
                f"LR: {lr:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "CV02", "ConfigValidator", "Learning rate sanity",
                Verdict.INFO, "LR not found in log"
            ))

        # CV03: Subset ratio
        subset = self._find_value(search_text, SUBSET_RE)
        if subset is not None:
            checks.append(CheckResult(
                "CV03", "ConfigValidator", "Subset ratio",
                Verdict.PASS if subset >= 0.3 else Verdict.WARN,
                f"Subset ratio: {subset:.2f}"
            ))
        else:
            checks.append(CheckResult(
                "CV03", "ConfigValidator", "Subset ratio",
                Verdict.INFO, "Subset ratio not found"
            ))

        # CV04: Max epochs consistency
        max_epochs = self._find_value(search_text, EPOCHS_RE)
        stage_max = 30
        if max_epochs is not None:
            checks.append(CheckResult(
                "CV04", "ConfigValidator", "Max epochs",
                Verdict.PASS if max_epochs >= stage_max else Verdict.WARN,
                f"Max epochs: {int(max_epochs)} (stage RF2: {stage_max})"
            ))
        else:
            checks.append(CheckResult(
                "CV04", "ConfigValidator", "Max epochs",
                Verdict.INFO, "max_epochs not found"
            ))

        # CV05: Active heads
        state = ctx.get("state", {})
        active_heads = state.get("active_heads", "")
        if active_heads:
            checks.append(CheckResult(
                "CV05", "ConfigValidator", "Active heads",
                Verdict.PASS if "det" in active_heads.lower() else Verdict.WARN,
                f"Active heads: {active_heads}"
            ))
        else:
            checks.append(CheckResult(
                "CV05", "ConfigValidator", "Active heads",
                Verdict.INFO, "active_heads not in state"
            ))

        # CV06: Backbone config printed
        backbone_lines = [line for line in search_text.split("\n") if BACKBONE_RE.search(line)]
        checks.append(CheckResult(
            "CV06", "ConfigValidator", "Backbone config",
            Verdict.PASS if backbone_lines else Verdict.INFO,
            backbone_lines[-1][:80] if backbone_lines else "Not found in log"
        ))

        # CV07: Precision / AMP
        amp_lines = [line for line in search_text.split("\n") if AMP_RE.search(line)]
        checks.append(CheckResult(
            "CV07", "ConfigValidator", "Training precision",
            Verdict.PASS if amp_lines else Verdict.INFO,
            amp_lines[-1][:80] if amp_lines else "Not found in log"
        ))

        return AgentResult(self.name, checks)

    @staticmethod
    def _find_value(text: str, pattern: re.Pattern) -> float | None:
        m = pattern.search(text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        return None
