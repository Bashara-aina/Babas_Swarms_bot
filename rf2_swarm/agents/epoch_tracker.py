"""Agent 14: EpochTrackerAgent — progression rate, ETA, batch throughput."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict, current_run_text

EPOCH_DUR_RE = re.compile(r"\[(\d+):(\d+)(?::(\d+))?\s*<")
EPOCH_PROGRESS_RE = re.compile(r"Epoch\s+(\d+)/(\d+)")
STEPS_PER_EPOCH_MAX = 5000


class EpochTrackerAgent(BaseAgent):
    """Tracks epoch progression: rate, ETA to completion, batch throughput."""

    def __init__(self):
        super().__init__("EpochTracker")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_text = ctx.get("log_text", "")
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        run_text = current_run_text(log_text)

        current_epoch = state.get("epoch", 0) or 0
        current_step = state.get("step", 0) or 0
        max_epochs = state.get("max_epochs", 30)

        # ET01: Epoch progression
        if current_epoch > 0:
            pct = current_epoch / max_epochs * 100
            remaining = max_epochs - current_epoch
            checks.append(CheckResult(
                "ET01", "EpochTracker", "Epoch progression",
                Verdict.FAIL if pct >= 100 else Verdict.WARN if pct >= 90 else Verdict.PASS,
                f"Epoch {current_epoch}/{max_epochs} ({pct:.0f}%, {remaining} remaining)"
            ))
        else:
            # Check log for any epoch progress if state shows 0
            ep_match = EPOCH_PROGRESS_RE.findall(run_text)
            if ep_match:
                latest = int(ep_match[-1][0])
                total = int(ep_match[-1][1])
                pct = latest / total * 100
                checks.append(CheckResult(
                    "ET01", "EpochTracker", "Epoch progression",
                    Verdict.PASS if latest > 0 else Verdict.INFO,
                    f"Epoch {latest}/{total} ({pct:.0f}%) [from log]"
                ))
            else:
                checks.append(CheckResult(
                    "ET01", "EpochTracker", "Epoch progression",
                    Verdict.INFO, "No epoch data yet"
                ))

        # ET02: Epoch timing from tqdm output — [MM:SS< or [H:MM:SS<
        epoch_durations = self._parse_epoch_timing(run_text)
        if epoch_durations:
            recent = epoch_durations[-5:]
            avg_time = sum(recent) / len(recent)
            avg_min = avg_time / 60
            if avg_time < 5400:
                v = Verdict.PASS
            elif avg_time < 7200:
                v = Verdict.WARN
            else:
                v = Verdict.FAIL
            detail = f"Avg: {avg_min:.1f} min/epoch over last {len(recent)} epochs"
            if len(recent) > 1:
                detail += f"  Recent: {[f'{t/60:.1f}m' for t in recent]}"
            checks.append(CheckResult(
                "ET02", "EpochTracker", "Epoch duration",
                v, detail
            ))
        else:
            checks.append(CheckResult(
                "ET02", "EpochTracker", "Epoch duration",
                Verdict.INFO, "No epoch timing data in log"
            ))

        # ET03: ETA to completion
        if epoch_durations and current_epoch > 0:
            avg_epoch_sec = sum(epoch_durations[-5:]) / len(epoch_durations[-5:]) if len(epoch_durations) >= 5 else epoch_durations[-1]
            remaining = max_epochs - current_epoch
            eta_hours = remaining * avg_epoch_sec / 3600
            checks.append(CheckResult(
                "ET03", "EpochTracker", "Training ETA",
                Verdict.PASS if eta_hours < 12 else Verdict.WARN if eta_hours < 48 else Verdict.FAIL,
                f"ETA: ~{eta_hours:.1f}h ({remaining} epochs × {avg_epoch_sec/60:.1f} min avg)"
            ))
        else:
            checks.append(CheckResult(
                "ET03", "EpochTracker", "Training ETA",
                Verdict.INFO, "Cannot compute ETA yet"
            ))

        # ET04: Batch throughput from step timing in tqdm
        step_time_re = re.findall(r"(\d+\.?\d*)s/it", run_text)
        if step_time_re:
            step_times = [float(t) for t in step_time_re[-10:]]
            avg_step_time = sum(step_times) / len(step_times)
            throughput = 1.0 / avg_step_time if avg_step_time > 0 else 0
            checks.append(CheckResult(
                "ET04", "EpochTracker", "Batch throughput",
                Verdict.PASS if throughput > 2.0 else Verdict.WARN if throughput > 0.5 else Verdict.FAIL,
                f"Throughput: {throughput:.2f} steps/s ({avg_step_time:.2f} s/it)"
            ))
        else:
            checks.append(CheckResult(
                "ET04", "EpochTracker", "Batch throughput",
                Verdict.INFO, "No step timing data"
            ))

        # ET05: Step consistency from state
        if current_step > 0:
            checks.append(CheckResult(
                "ET05", "EpochTracker", "Step consistency",
                Verdict.PASS,
                f"Current step: {current_step}"
            ))
        else:
            checks.append(CheckResult(
                "ET05", "EpochTracker", "Step consistency",
                Verdict.INFO, "No step data"
            ))

        return AgentResult(self.name, checks)

    def _parse_epoch_timing(self, text: str) -> list[float]:
        """Parse epoch elapsed time from tqdm progress lines.

        Matches tqdm elapsed format: [MM:SS< or [H:MM:SS< before the rate.
        Returns epoch durations in seconds.
        """
        times = []
        for m in EPOCH_DUR_RE.finditer(text):
            try:
                h = int(m.group(1)) if m.group(3) else 0
                m_val = int(m.group(2)) if m.group(3) else int(m.group(1))
                s = int(m.group(3)) if m.group(3) else int(m.group(2))
                total_sec = h * 3600 + m_val * 60 + s
                if 10 < total_sec < 72000:  # sanity: 10s-20h per epoch
                    times.append(float(total_sec))
            except ValueError:
                pass
        return times
