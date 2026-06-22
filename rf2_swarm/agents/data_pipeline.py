"""Agent 06: DataPipelineAgent — DataLoader workers, batch timing, cache hits."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

BATCH_TIME_RE = re.compile(r"batch.*?(\d+\.?\d*)s.*?(?:batch|step)\s*(\d+)/\s*(\d+)", re.IGNORECASE)
DATALOADER_RE = re.compile(r"(?:DataLoader|dataloader).*?(\d+)\s*worker", re.IGNORECASE)
DATASET_RE = re.compile(r"dataset.*?(\d+)\s*(?:sample|image|item)", re.IGNORECASE)


class DataPipelineAgent(BaseAgent):
    """Monitors data loading pipeline health."""

    def __init__(self):
        super().__init__("DataPipeline")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        batch_times = BATCH_TIME_RE.findall(log_text)
        dataloaders = DATALOADER_RE.findall(log_text)
        datasets = DATASET_RE.findall(log_text)

        # D01: Batch processing time reasonable
        if batch_times:
            times = [float(t[0]) for t in batch_times]
            avg_time = sum(times) / len(times)
            checks.append(CheckResult("D01", "DataPipeline", "Batch processing time reasonable",
                                      Verdict.PASS if avg_time < 30 else Verdict.WARN,
                                      f"Avg batch time: {avg_time:.2f}s (over {len(times)} batches)"))
        else:
            checks.append(CheckResult("D01", "DataPipeline", "Batch processing time reasonable",
                                      Verdict.INFO, "No batch timing entries"))

        # D02: DataLoader workers configured
        if dataloaders:
            workers = int(dataloaders[-1])
            checks.append(CheckResult("D02", "DataPipeline", "DataLoader workers configured",
                                      Verdict.PASS if workers > 0 else Verdict.WARN,
                                      f"{workers} workers"))
        else:
            checks.append(CheckResult("D02", "DataPipeline", "DataLoader workers configured",
                                      Verdict.INFO, "No DataLoader worker info"))

        # D03: No dataloader bottleneck warnings
        bottleneck = re.search(r"(?:dataloader.*slow|bottleneck|timeout.*worker)", log_text, re.IGNORECASE)
        checks.append(CheckResult("D03", "DataPipeline", "No DataLoader bottleneck warnings",
                                  Verdict.PASS if not bottleneck else Verdict.WARN,
                                  "Bottleneck detected" if bottleneck else "No bottlenecks"))

        # D04: Dataset has samples
        if datasets:
            n_samples = int(datasets[-1])
            checks.append(CheckResult("D04", "DataPipeline", "Dataset has sufficient samples",
                                      Verdict.PASS if n_samples > 0 else Verdict.FAIL,
                                      f"{n_samples} samples", blocking=n_samples == 0))
        else:
            checks.append(CheckResult("D04", "DataPipeline", "Dataset has sufficient samples",
                                      Verdict.INFO))

        # D05: Batch progression (step advancing)
        if batch_times:
            last_batch = batch_times[-1]
            current = int(last_batch[1])
            total = int(last_batch[2])
            pct = current / total * 100 if total > 0 else 0
            checks.append(CheckResult("D05", "DataPipeline", "Batch progression advancing",
                                      Verdict.PASS if current > 0 else Verdict.FAIL,
                                      f"Batch {current}/{total} ({pct:.0f}%)"))
        else:
            checks.append(CheckResult("D05", "DataPipeline", "Batch progression advancing",
                                      Verdict.INFO))

        # D06: No OOM in data loading (non-blocking — killed workers from SIGTERM are benign)
        oom = re.search(r"(?:CUDA.*out of memory|OOM|DataLoader.*killed)", log_text, re.IGNORECASE)
        checks.append(CheckResult("D06", "DataPipeline", "No OOM in data loading",
                                  Verdict.PASS if not oom else Verdict.WARN,
                                  "OOM/worker killed" if oom else "No OOM"))

        return AgentResult(self.name, checks)
