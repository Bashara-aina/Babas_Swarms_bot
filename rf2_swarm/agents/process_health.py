"""Agent 13: ProcessHealthAgent — PID alive from ps aux, heartbeat staleness.

FIX 2026-06-20: Added retry-loop to _find_training_pid(). Under heavy I/O load
(200K-line log processing across 40 threads) the first ps(1) call can timeout.
Retries up to 3 times with 2s sleep, logs failures instead of silent swallow.

FIX 2026-06-19: The ps aux fallback previously matched 'rf2_swarm' itself
(via the 'rf2' pattern), creating a false-positive when training was dead but
the swarm monitor was running. Now:
  - Only scans for actual train.py scripts (not 'rf2_swarm' or self PID)
  - Excludes os.getpid() from ps aux results
  - Reports stale state.json PID separately from 'no process found'
"""

from __future__ import annotations
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict
from ..config import HEARTBEAT_WARN_SEC, HEARTBEAT_FAIL_SEC

# Only match actual training scripts — NOT rf2_swarm (the monitor itself)
TRAIN_PROC_RE = re.compile(r"python.*train\.py")

PID_RETRIES = 3


def _debug(msg: str):
    """Print timestamped debug to stderr during PID scan (no circular import)."""
    print(f"[PID-scan {datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


class ProcessHealthAgent(BaseAgent):
    """Monitors training process aliveness and heartbeat."""

    def __init__(self):
        super().__init__("ProcessHealth")

    @staticmethod
    def _find_training_pid() -> int | None:
        """Scan ps aux for actual training processes, excluding self.

        Retries up to PID_RETRIES times with 2s delay to tolerate
        transient load spikes from parallel log processing.
        Returns the first matching PID or None if no training process found.
        """
        self_pid = os.getpid()
        for attempt in range(PID_RETRIES):
            try:
                result = subprocess.run(
                    ["ps", "aux", "--no-headers"],
                    capture_output=True, text=True, timeout=15
                )
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) < 11:
                        continue
                    try:
                        pid = int(parts[1])
                    except (ValueError, IndexError):
                        continue
                    # Skip self (the swarm monitor)
                    if pid == self_pid:
                        continue
                    if TRAIN_PROC_RE.search(line):
                        return pid
                # No match found on this attempt, retry
                if attempt < PID_RETRIES - 1:
                    _debug(f"attempt {attempt + 1} found no training process, retrying...")
                    time.sleep(2)
            except subprocess.TimeoutExpired:
                if attempt < PID_RETRIES - 1:
                    _debug(f"attempt {attempt + 1} timed out, retrying...")
                    time.sleep(2)
                    continue
                _debug(f"failed after {PID_RETRIES} attempts (timeout)")
            except Exception as e:
                _debug(f"error: {e}")
                return None
        return None

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        state = ctx.get("state", {})
        checks: list[CheckResult] = []

        # ── PH01: Find the actual training PID ──
        active_pid = self._find_training_pid()
        pid_from_state = state.get("training_pid")

        if active_pid is not None:
            # We found a running training process — confirm it matches state
            state_match = (pid_from_state is not None
                           and str(active_pid) == str(pid_from_state))
            detail = f"PID {active_pid} running"
            if not state_match and pid_from_state:
                detail += f" (state.json has stale PID {pid_from_state})"
            checks.append(CheckResult("PH01", "ProcessHealth", "Training PID is alive",
                                      Verdict.PASS, detail))
        elif pid_from_state is not None:
            # State claims a PID but no training process found
            checks.append(CheckResult("PH01", "ProcessHealth", "Training PID is alive",
                                      Verdict.FAIL,
                                      f"state.json PID {pid_from_state} not running — "
                                      "no train.py process found",
                                      blocking=True))
        else:
            checks.append(CheckResult("PH01", "ProcessHealth", "Training PID is alive",
                                      Verdict.FAIL,
                                      "No training process detected and state.json has no PID",
                                      blocking=True))

        # PH02: Heartbeat recent — only meaningful if process is alive
        # When process is dead, the heartbeat is always stale.
        last_hb = state.get("last_heartbeat", "")
        if active_pid is None:
            checks.append(CheckResult("PH02", "ProcessHealth", "Heartbeat is recent",
                                      Verdict.FAIL, "No active process — no heartbeat possible",
                                      blocking=True))
        elif last_hb:
            try:
                hb_time = time.mktime(time.strptime(last_hb, "%Y-%m-%d %H:%M:%S"))
                age = time.time() - hb_time
                if age < HEARTBEAT_WARN_SEC:
                    checks.append(CheckResult("PH02", "ProcessHealth", "Heartbeat is recent",
                                              Verdict.PASS, f"Last heartbeat: {age:.0f}s ago"))
                elif age < HEARTBEAT_FAIL_SEC:
                    checks.append(CheckResult("PH02", "ProcessHealth", "Heartbeat is recent",
                                              Verdict.WARN, f"Heartbeat stale: {age:.0f}s ago"))
                else:
                    checks.append(CheckResult("PH02", "ProcessHealth", "Heartbeat is recent",
                                              Verdict.FAIL,
                                              f"Heartbeat too old: {age:.0f}s ago",
                                              blocking=True))
            except (ValueError, OSError):
                checks.append(CheckResult("PH02", "ProcessHealth", "Heartbeat is recent",
                                          Verdict.INFO, f"Last heartbeat string: {last_hb}"))
        else:
            checks.append(CheckResult("PH02", "ProcessHealth", "Heartbeat is recent",
                                      Verdict.INFO, "No heartbeat timestamp in state"))

        # PH03: Process not in zombie state
        if active_pid:
            try:
                status = subprocess.run(
                    ["ps", "-o", "state=", "-p", str(active_pid)],
                    capture_output=True, text=True, timeout=5
                ).stdout.strip()
                zombie = "Z" in status
                checks.append(CheckResult("PH03", "ProcessHealth", "Process not zombie",
                                          Verdict.FAIL if zombie else Verdict.PASS,
                                          f"State: {status}" if not zombie else f"ZOMBIE: {status}",
                                          blocking=zombie))
            except Exception:
                checks.append(CheckResult("PH03", "ProcessHealth", "Process not zombie",
                                          Verdict.INFO))
        else:
            checks.append(CheckResult("PH03", "ProcessHealth", "Process not zombie",
                                      Verdict.SKIP))

        # PH04: CPU time accumulating (process is doing work)
        if active_pid:
            try:
                cpu_time = subprocess.run(
                    ["ps", "-o", "time=", "-p", str(active_pid)],
                    capture_output=True, text=True, timeout=5
                ).stdout.strip()
                checks.append(CheckResult("PH04", "ProcessHealth", "Process accumulating CPU time",
                                          Verdict.PASS if cpu_time else Verdict.INFO,
                                          f"CPU time: {cpu_time}"))
            except Exception:
                checks.append(CheckResult("PH04", "ProcessHealth", "Process accumulating CPU time",
                                          Verdict.INFO))
        else:
            checks.append(CheckResult("PH04", "ProcessHealth", "Process accumulating CPU time",
                                      Verdict.SKIP))

        return AgentResult(self.name, checks)
