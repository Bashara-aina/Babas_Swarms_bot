"""Agent 03: HeadHealthAgent — DET/ASD/PSR head liveness, gradient norms, NaN weights."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

# LIVENESS_GRAD: detection_head:ALIVE[6.61e-03]/ALIVE[7.53e-02] | head_pose_head:ALIVE[6.76e-03]/ALIVE[3.28e-04]
# Note: backbone and fpn have NO `_head` suffix (bare `backbone:ALIVE[val|n=N]`)
GRAD_NORM_RE = re.compile(
    r"(detection|head_pose|activity|psr|backbone|fpn|pose)(?:_head)?:(?:ALIVE|DEAD)\[([\d.e+\-]+)"
)
# LIVENESS (non-GRAD): det=1.33e+00 ALIVE | act=0.00e+00 DEAD | psr=0.00e+00 DEAD | head_pose=3.52e-01 ALIVE
LIVENESS_HEAD_RE = re.compile(
    r"(det|act|psr|head_pose)\s*=\s*([\d.e+\-]+)\s+(ALIVE|DEAD)"
)
NAN_GRAD_RE = re.compile(r"NaN.*grad", re.IGNORECASE)
DET_HEALTH_RE = re.compile(r"(?:det|detection).*?(ALIVE|DEAD)", re.IGNORECASE)
DEAD_HISTORY_RE = re.compile(r"(?:DEAD|dead)", re.IGNORECASE)

# Head name mapping for GRAD_NORM_RE (long → short)
_HEAD_NAME_MAP = {
    "detection": "det",
    "head_pose": "hp",
    "activity": "act",
    "psr": "psr",
    "backbone": "backbone",
}


class HeadHealthAgent(BaseAgent):
    """Monitors all network heads for liveness, gradient health, and balance."""

    def __init__(self):
        super().__init__("HeadHealth")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        # HH01: Parse gradient norms from LIVENESS_GRAD log lines
        grad_norms = self._parse_grad_norms(log_text)
        det_norm = grad_norms.get("det")
        hp_norm = grad_norms.get("hp")
        act_norm = grad_norms.get("act")
        psr_norm = grad_norms.get("psr")
        bb_norm = grad_norms.get("backbone")

        # DET head grad norm
        if det_norm is not None:
            checks.append(CheckResult(
                "HH01", "HeadHealth", "DET head grad norm",
                Verdict.PASS if det_norm > 1e-6 else Verdict.FAIL,
                f"DET grad norm: {det_norm:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "HH01", "HeadHealth", "DET head grad norm",
                Verdict.INFO, "No DET grad norm data"
            ))

        # HH02: Head-Pose grad norm
        if hp_norm is not None:
            checks.append(CheckResult(
                "HH02", "HeadHealth", "HP head grad norm",
                Verdict.PASS if hp_norm > 1e-6 else Verdict.FAIL,
                f"HP grad norm: {hp_norm:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "HH02", "HeadHealth", "HP head grad norm",
                Verdict.INFO, "No HP grad norm data"
            ))

        # HH03: Activity head grad norm
        if act_norm is not None:
            checks.append(CheckResult(
                "HH03", "HeadHealth", "Activity head grad norm",
                Verdict.PASS if act_norm > 1e-8 else Verdict.WARN,
                f"Activity grad norm: {act_norm:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "HH03", "HeadHealth", "Activity head grad norm",
                Verdict.INFO, "No activity grad norm"
            ))

        # HH04: PSR head grad norm
        if psr_norm is not None:
            checks.append(CheckResult(
                "HH04", "HeadHealth", "PSR head grad norm",
                Verdict.PASS if psr_norm > 1e-8 else Verdict.WARN,
                f"PSR grad norm: {psr_norm:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "HH04", "HeadHealth", "PSR head grad norm",
                Verdict.INFO, "No PSR grad norm"
            ))

        # HH05: Backbone grad norm
        if bb_norm is not None:
            checks.append(CheckResult(
                "HH05", "HeadHealth", "Backbone grad norm",
                Verdict.PASS if bb_norm > 1e-5 else Verdict.WARN,
                f"Backbone grad norm: {bb_norm:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "HH05", "HeadHealth", "Backbone grad norm",
                Verdict.INFO, "No backbone grad norm"
            ))

        # HH06: Head balance (DET vs HP) — cross-architecture aware
        if det_norm is not None and hp_norm is not None and hp_norm > 0:
            ratio = det_norm / hp_norm
            both_alive = det_norm > 1e-6 and hp_norm > 1e-6
            if both_alive and ratio > 100:
                v = Verdict.WARN
            elif ratio < 0.1 or ratio > 10:
                v = Verdict.FAIL
            else:
                v = Verdict.PASS
            checks.append(CheckResult(
                "HH06", "HeadHealth", "Head grad balance",
                v,
                f"DET/HP ratio: {ratio:.2f} (both alive={both_alive})  "
                f"DET={det_norm:.2e}  HP={hp_norm:.2e}"
            ))
        else:
            checks.append(CheckResult(
                "HH06", "HeadHealth", "Head grad balance",
                Verdict.INFO, "Insufficient data for head balance"
            ))

        # HH07: NaN gradients
        nan_grads = NAN_GRAD_RE.findall(log_text)
        checks.append(CheckResult(
            "HH07", "HeadHealth", "NaN gradients",
            Verdict.FAIL if nan_grads else Verdict.PASS,
            f"{len(nan_grads)} NaN gradient events" if nan_grads else "No NaN gradients"
        ))

        # HH08: DET head liveness from state
        det_health = state.get("det_health", "")
        if det_health:
            alive = "ALIVE" in str(det_health).upper()
            checks.append(CheckResult(
                "HH08", "HeadHealth", "DET head liveness",
                Verdict.PASS if alive else Verdict.FAIL,
                f"DET head: {det_health}"
            ))
        else:
            checks.append(CheckResult(
                "HH08", "HeadHealth", "DET head liveness",
                Verdict.INFO, "det_health not in state"
            ))

        # HH09: Consecutive dead epochs
        dead_history = state.get("det_health_history", [])
        if dead_history:
            recent_dead = sum(1 for h in dead_history[-5:] if DEAD_HISTORY_RE.search(str(h)))
            max_dead = state.get("max_consecutive_dead", 5)
            checks.append(CheckResult(
                "HH09", "HeadHealth", "Consecutive dead epochs",
                Verdict.FAIL if recent_dead >= max_dead else Verdict.WARN if recent_dead >= 3 else Verdict.PASS,
                f"{recent_dead} dead in last {min(5, len(dead_history))} epochs (max: {max_dead})"
            ))
        else:
            checks.append(CheckResult(
                "HH09", "HeadHealth", "Consecutive dead epochs",
                Verdict.INFO, "det_health_history not available"
            ))

        # HH10: Kendall precision cap from state
        kendall_active = state.get("kendall_hp_prec_cap", None)
        if kendall_active is not None:
            checks.append(CheckResult(
                "HH10", "HeadHealth", "Kendall HP precision cap",
                Verdict.PASS if kendall_active else Verdict.WARN,
                f"Kendall cap active: {kendall_active}"
            ))
        else:
            checks.append(CheckResult(
                "HH10", "HeadHealth", "Kendall HP precision cap",
                Verdict.INFO, "Kendall cap status unknown"
            ))

        # HH11: Head liveness from LIVENESS log lines
        liveness = self._parse_liveness_heads(log_text)
        if liveness:
            parts = [f"{h}={s['status']}({s['value']:.2e})" for h, s in liveness.items()]
            any_dead = any(s["status"] == "DEAD" for s in liveness.values())
            checks.append(CheckResult(
                "HH11", "HeadHealth", "Head liveness from log",
                Verdict.WARN if any_dead else Verdict.PASS,
                " | ".join(parts)
            ))
        else:
            checks.append(CheckResult(
                "HH11", "HeadHealth", "Head liveness from log",
                Verdict.INFO, "No LIVENESS entries in log"
            ))

        return AgentResult(self.name, checks)

    @staticmethod
    def _parse_grad_norms(text: str) -> dict[str, float]:
        """Parse gradient norms from LIVENESS_GRAD log lines.

        Format: detection_head:ALIVE[6.61e-03]/ALIVE[7.53e-02]
        Returns first value (shared weight grad norm) keyed by short head name.
        """
        norms: dict[str, float] = {}
        for m in GRAD_NORM_RE.finditer(text):
            key = _HEAD_NAME_MAP.get(m.group(1))
            if key:
                try:
                    norms[key] = float(m.group(2))
                except ValueError:
                    pass
        return norms

    @staticmethod
    def _parse_liveness_heads(text: str) -> dict[str, dict[str, Any]]:
        """Parse latest LIVENESS (non-GRAD) line for per-head ALIVE/DEAD status.

        Format: [LIVENESS step=N] det=1.33e+00 ALIVE | act=0.00e+00 DEAD | ...
        """
        results: dict[str, dict[str, Any]] = {}
        lines = re.findall(r"\[LIVENESS\s+step=\d+\].*", text)
        if not lines:
            return results
        latest = lines[-1]
        for m in LIVENESS_HEAD_RE.finditer(latest):
            results[m.group(1)] = {
                "value": float(m.group(2)),
                "status": m.group(3),
            }
        return results
