"""Agent 19: BlockerAssessmentAgent — cross-cutting blocker summary, P0-P3 classification."""

from __future__ import annotations
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict


P0_CONDITIONS = [
    "process_health:PH01 is FAIL",       # no training process
    "nan_detector:ND01 is FAIL",          # NaN in losses
    "nan_detector:ND02 is FAIL",          # NaN in weights
    "gate_tracker:G02 is FAIL",           # mAP50 below target AND no improvement
    "process_health:PH03 is FAIL",         # zombie process
]
P1_CONDITIONS = [
    "gate_tracker:G04 is FAIL",           # MAE above target
    "cuda_health:CU02 is FAIL",           # CUDA runtime errors
    "log_anomaly:LA03 is FAIL",           # critical/fatal errors
    "log_anomaly:LA04 is FAIL",           # stack traces
]
P2_CONDITIONS = [
    "loss_health:L06 is FAIL",            # loss spikes
    "checkpoint:C06 is FAIL",             # checkpoint corruption
    "data_pipeline:D06 is FAIL",          # data loading OOM
]
P3_CONDITIONS = [
    "head_health:H04 is WARN",            # persistently DEAD heads (non-DET)
    "convergence:S01 is WARN",            # plateau
    "gate_tracker:G11 is WARN",           # mAP50 not trending up
]


class BlockerAssessmentAgent(BaseAgent):
    """Cross-cutting blocker analysis — classifies blocking issues by severity P0-P3."""

    def __init__(self):
        super().__init__("BlockerAssessment")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        prev_results = ctx.get("prev_results", {})
        checks: list[CheckResult] = []

        # Collect all check verdicts from all agents into flat uid → verdict map
        verdicts: dict[str, str] = {}
        for agent_checks in prev_results.values():
            if isinstance(agent_checks, list):
                for c in agent_checks:
                    uid = c.get("uid", "")
                    if uid:
                        verdicts[f"{uid.lower()}"] = c.get("verdict", Verdict.PASS)

        def check_condition(cond_str: str) -> bool:
            """Evaluate a condition string like 'process_health:PH01 is FAIL'."""
            parts = cond_str.split(" is ")
            if len(parts) != 2:
                return False
            uid_part = parts[0].strip().lower()
            expected = parts[1].strip()
            actual = verdicts.get(uid_part.split(":")[-1] if ":" in uid_part else uid_part, Verdict.PASS)
            return actual == expected

        # BA01: P0 blockers (training cannot continue)
        p0_active = [c for c in P0_CONDITIONS if check_condition(c)]
        if p0_active:
            checks.append(CheckResult("BA01", "BlockerAssessment", "P0 blockers present",
                                      Verdict.FAIL, f"{len(p0_active)} P0 condition(s) active: {p0_active}",
                                      blocking=True))
        else:
            checks.append(CheckResult("BA01", "BlockerAssessment", "No P0 blockers",
                                      Verdict.PASS, "All P0 conditions clear"))

        # BA02: P1-P2 blockers (gate cannot be met, intervention needed)
        p1_active = [c for c in P1_CONDITIONS if check_condition(c)]
        p2_active = [c for c in P2_CONDITIONS if check_condition(c)]
        total_intervention = len(p1_active) + len(p2_active)
        if total_intervention > 0:
            checks.append(CheckResult("BA02", "BlockerAssessment", "P1/P2 intervention needed",
                                      Verdict.WARN,
                                      f"P1={len(p1_active)} P2={len(p2_active)} conditions active"))
        else:
            checks.append(CheckResult("BA02", "BlockerAssessment", "P1/P2 intervention needed",
                                      Verdict.PASS, "No P1/P2 interventions needed"))

        # BA03: P3 warnings (monitoring advisories)
        p3_active = [c for c in P3_CONDITIONS if check_condition(c)]
        checks.append(CheckResult("BA03", "BlockerAssessment", "P3 advisory warnings",
                                  Verdict.WARN if p3_active else Verdict.PASS,
                                  f"{len(p3_active)} P3 advisory" if p3_active else "No P3 advisories"))

        return AgentResult(self.name, checks)
