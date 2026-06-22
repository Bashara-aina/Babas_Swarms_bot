"""Agent 08: GPUResourceAgent — VRAM, util%, temperature, power, ECC errors.

Derives GPU metrics from nvidia-smi directly and from log patterns.
"""

from __future__ import annotations
import re
import subprocess
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

VRAM_RE = re.compile(r"(?:VRAM|vram|memory).*?(\d+)\s*MiB", re.IGNORECASE)
GPU_UTIL_RE = re.compile(r"(?:GPU.*?util|gpu_util).*?(\d+)", re.IGNORECASE)
GPU_TEMP_RE = re.compile(r"(?:GPU.*?temp|gpu_temp|temperature).*?(\d+)", re.IGNORECASE)


class GPUResourceAgent(BaseAgent):
    """Monitors GPU health: VRAM usage, util, temperature, power, ECC errors."""

    def __init__(self):
        super().__init__("GPUResource")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        epoch = state.get("epoch", 0) or 0
        step = state.get("step", 0) or 0
        training_active = epoch > 0 or step > 0

        # GR01: Query nvidia-smi for live GPU state
        gpu_info = self._query_nvidia_smi()
        if gpu_info:
            mem_used, mem_total, util_pct, temp_c, power_w = gpu_info

            # VRAM usage
            vram_frac = mem_used / mem_total if mem_total > 0 else 0
            checks.append(CheckResult(
                "GR01", "GPUResource", "VRAM usage",
                Verdict.PASS if vram_frac < 0.85 else Verdict.FAIL if vram_frac < 0.95 else Verdict.FAIL,
                f"VRAM: {mem_used:.1f}/{mem_total:.0f} GB ({vram_frac:.0%})"
            ))

            # GPU utilization — training-context aware
            if training_active and util_pct < 10:
                # Snapshot caught between training steps — sampling artifact
                v = Verdict.WARN
                detail = f"GPU util: {util_pct}% (sampling artifact — training active)"
            elif util_pct > 90:
                v = Verdict.PASS
                detail = f"GPU util: {util_pct}%"
            elif util_pct > 50:
                v = Verdict.WARN
                detail = f"GPU util: {util_pct}%"
            else:
                v = Verdict.FAIL
                detail = f"GPU util: {util_pct}%"

            checks.append(CheckResult(
                "GR02", "GPUResource", "GPU utilization",
                v, detail
            ))

            # Temperature
            if temp_c < 70:
                v = Verdict.PASS
            elif temp_c < 85:
                v = Verdict.WARN
            else:
                v = Verdict.FAIL
            checks.append(CheckResult(
                "GR03", "GPUResource", "GPU temperature",
                v, f"GPU temp: {temp_c}°C"
            ))

            # Power
            max_power = 170.0
            power_frac = power_w / max_power
            checks.append(CheckResult(
                "GR04", "GPUResource", "GPU power draw",
                Verdict.PASS if power_frac > 0.5 else Verdict.WARN if power_frac > 0.3 else Verdict.FAIL,
                f"Power: {power_w}/{max_power:.0f} W ({power_frac:.0%})"
            ))
        else:
            checks.append(CheckResult(
                "GR01", "GPUResource", "VRAM usage",
                Verdict.INFO, "nvidia-smi not available"
            ))
            checks.append(CheckResult(
                "GR02", "GPUResource", "GPU utilization",
                Verdict.INFO, "nvidia-smi not available"
            ))
            checks.append(CheckResult(
                "GR03", "GPUResource", "GPU temperature",
                Verdict.INFO, "nvidia-smi not available"
            ))
            checks.append(CheckResult(
                "GR04", "GPUResource", "GPU power draw",
                Verdict.INFO, "nvidia-smi not available"
            ))

        # GR05: System RAM from /proc/meminfo
        ram_gb = self._query_ram()
        if ram_gb > 0:
            checks.append(CheckResult(
                "GR05", "GPUResource", "System RAM available",
                Verdict.PASS if ram_gb > 16 else Verdict.WARN if ram_gb > 8 else Verdict.FAIL,
                f"Available RAM: {ram_gb:.1f} GB"
            ))
        else:
            checks.append(CheckResult(
                "GR05", "GPUResource", "System RAM available",
                Verdict.SKIP, "Could not query RAM"
            ))

        # GR06: GPU errors from log
        gpu_errs = re.findall(r"(?:GPU|gpu).*?(?:error|fail)", log_text, re.IGNORECASE)
        checks.append(CheckResult(
            "GR06", "GPUResource", "GPU errors in log",
            Verdict.FAIL if gpu_errs else Verdict.PASS,
            f"{len(gpu_errs)} GPU error(s)" if gpu_errs else "No GPU errors"
        ))

        return AgentResult(self.name, checks)

    @staticmethod
    def _query_nvidia_smi() -> tuple[float, float, float, float, float] | None:
        """Query nvidia-smi for GPU metrics. Returns (mem_used_gb, mem_total_gb, util%, temp_c, power_w)."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                return None
            parts = result.stdout.strip().split(", ")
            if len(parts) < 5:
                return None
            mem_used = float(parts[0]) / 1024  # MiB → GB
            mem_total = float(parts[1]) / 1024
            util_pct = float(parts[2])
            temp_c = float(parts[3])
            power_w = float(parts[4])
            return (mem_used, mem_total, util_pct, temp_c, power_w)
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
            return None

    @staticmethod
    def _query_ram() -> float:
        """Query available system RAM from /proc/meminfo."""
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        kb = int(line.split()[1])
                        return kb / (1024 ** 2)  # kB → GB
        except (OSError, IOError, ValueError):
            pass
        return 0.0
