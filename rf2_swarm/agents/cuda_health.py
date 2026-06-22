"""Agent 16: CudaHealthAgent — CUDA errors, OOM, NCCL failures, GPU visibility."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

CUDA_ERR_RE = re.compile(r"(?:CUDA|Cuda|cuda).*?(?:error|fail|EXCEPTION)", re.IGNORECASE)
CUDA_OOM_RE = re.compile(r"(?:out of memory|CUDA OOM|OOM)", re.IGNORECASE)
NCCL_ERR_RE = re.compile(r"NCCL.*?(?:error|fail|abort|timeout)", re.IGNORECASE)
CUDA_NOT_AVAIL_RE = re.compile(r"(?:CUDA|GPU).*?(?:not.*avail|unavail|not.*found)", re.IGNORECASE)
CUDNN_RE = re.compile(r"(?:cuDNN|CUDNN).*?(?:error|fail)", re.IGNORECASE)


class CudaHealthAgent(BaseAgent):
    """Monitors CUDA runtime health."""

    def __init__(self):
        super().__init__("CudaHealth")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        cuda_errs = CUDA_ERR_RE.findall(log_text)
        ooms = CUDA_OOM_RE.findall(log_text)
        nccl_errs = NCCL_ERR_RE.findall(log_text)
        cuda_not_avail = CUDA_NOT_AVAIL_RE.findall(log_text)
        cudnn_errs = CUDNN_RE.findall(log_text)

        # CU01: CUDA available
        checks.append(CheckResult("CU01", "CudaHealth", "CUDA available",
                                  Verdict.FAIL if cuda_not_avail else Verdict.PASS,
                                  "CUDA unavailable" if cuda_not_avail else "CUDA available",
                                  blocking=bool(cuda_not_avail)))

        # CU02: No CUDA runtime errors
        checks.append(CheckResult("CU02", "CudaHealth", "No CUDA runtime errors",
                                  Verdict.FAIL if cuda_errs else Verdict.PASS,
                                  f"{len(cuda_errs)} CUDA errors" if cuda_errs else "No CUDA errors",
                                  blocking=bool(cuda_errs)))

        # CU03: No OOM events
        checks.append(CheckResult("CU03", "CudaHealth", "No CUDA OOM events",
                                  Verdict.FAIL if ooms else Verdict.PASS,
                                  f"{len(ooms)} OOM events" if ooms else "No OOM",
                                  blocking=bool(ooms)))

        # CU04: No NCCL errors
        checks.append(CheckResult("CU04", "CudaHealth", "No NCCL errors",
                                  Verdict.FAIL if nccl_errs else Verdict.PASS,
                                  f"{len(nccl_errs)} NCCL errors" if nccl_errs else "No NCCL errors",
                                  blocking=bool(nccl_errs)))

        # CU05: No cuDNN errors
        checks.append(CheckResult("CU05", "CudaHealth", "No cuDNN errors",
                                  Verdict.FAIL if cudnn_errs else Verdict.PASS,
                                  "cuDNN error" if cudnn_errs else "No cuDNN errors"))

        return AgentResult(self.name, checks)
