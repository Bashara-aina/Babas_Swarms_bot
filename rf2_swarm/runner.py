"""Main monitoring loop — runs on timer, manages lifecycle.

FIX 2026-06-20: Added training death auto-restart watchdog. When PH01 has been
FAIL for N consecutive cycles, the runner calls restart_rf2_training.sh to
auto-recover the training process instead of waiting for manual intervention.
"""

from __future__ import annotations
import os
import signal
import subprocess
import time
from datetime import datetime

from .base_agent import BaseAgent, Verdict
from .config import (
    LOG, STATE, METRICS, CONFIG_FILE,
    RESULTS_JSON, REPORT_TXT, SWARM_LOG,
    DEFAULT_INTERVAL, LOG_TAIL_SIZE,
)
from .data_sources import reload_all
from .coordinator import Coordinator
from .alerting import AlertingEngine
from .reporter import write_results

# ├── Auto-restart watchdog ─────────────────────────────────────────────
RESTART_SCRIPT = "/media/newadmin/master/POPW/working/code/industreal_improved/scripts/restart_rf2_training.sh"
FALLBACK_RESTART_PATHS = [
    RESTART_SCRIPT,
    "/media/newadmin/master/POPW/working/code/industreal_improved/src/runs/rf_stages/auto_restart.sh",
]
AUTO_RESTART_CYCLES = 3      # restart after this many consecutive dead cycles
AUTO_RESTART_COOLDOWN = 600   # minimum seconds between restarts (10 min)
# ────────────────────────────────────────────────────────────────────────


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _find_restart_script() -> str | None:
    """Find the restart script in any of the known locations."""
    for p in [RESTART_SCRIPT] + FALLBACK_RESTART_PATHS:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None


class Runner:
    """Top-level monitoring loop."""

    def __init__(
        self,
        agents: list[BaseAgent],
        interval: int = DEFAULT_INTERVAL,
        log_tail: int = LOG_TAIL_SIZE,
    ):
        self.agents = agents
        self.interval = interval
        self.log_tail = log_tail
        self.coordinator = Coordinator(agents)
        self.alerts = AlertingEngine(SWARM_LOG)
        self._running = True
        self._cycle = 0
        # Auto-restart state
        self._dead_cycles = 0
        self._last_restart_time = 0.0

    def _log(self, msg: str):
        ts = _timestamp()
        line = f"[{ts}] {msg}"
        print(line)
        with open(SWARM_LOG, "a") as f:
            f.write(line + "\n")

    def _handle_signal(self, signum, frame):
        self._log(f"Signal {signum} received — shutting down after current cycle.")
        self._running = False

    def _auto_restart(self):
        """Attempt to restart training if dead for too long."""
        now = time.time()
        if now - self._last_restart_time < AUTO_RESTART_COOLDOWN:
            self._log(f"  Auto-restart skipped — cooldown active ({AUTO_RESTART_COOLDOWN}s)")
            return

        script = _find_restart_script()
        if script is None:
            self._log("  Auto-restart FAILED — no restart script found")
            return

        self._log(f"  Auto-restart triggered — running {script}")
        self._last_restart_time = now
        try:
            result = subprocess.run(
                ["bash", script],
                capture_output=True, text=True, timeout=120,
                cwd="/media/newadmin/master/POPW/working/code/industreal_improved",
            )
            if result.returncode == 0:
                self._log("  Auto-restart OK — training relaunched")
            else:
                self._log(f"  Auto-restart FAILED (exit={result.returncode}): {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            self._log("  Auto-restart timed out after 120s")
        except Exception as e:
            self._log(f"  Auto-restart error: {e}")

    def run_forever(self):
        """Infinite monitoring loop. Ctrl-C / SIGTERM to stop."""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        self._log(f"RF2 Swarm started — {len(self.agents)} agents, interval={self.interval}s")
        self._log(f"Output → {RESULTS_JSON}")
        restart_script = _find_restart_script()
        if restart_script:
            self._log(f"Auto-restart enabled — script={restart_script} (after {AUTO_RESTART_CYCLES} dead cycles)")
        else:
            self._log("Auto-restart NOT available — no restart script found")

        while self._running:
            self._cycle += 1
            self._run_one_cycle()

            if not self._running:
                break
            time.sleep(self.interval)

        self._log("RF2 Swarm stopped.")

    def run_once(self):
        """Single cycle, no loop."""
        self._run_one_cycle()

    def _run_one_cycle(self):
        start = time.time()
        ctx = reload_all(LOG, STATE, METRICS, CONFIG_FILE, self.log_tail)
        state = ctx["state"]

        self._log(f"Cycle #{self._cycle} — epoch={state.get('epoch','?')}  ETA ?")

        results = self.coordinator.run_cycle(ctx)

        # Alert on deltas
        deltas = self.coordinator.compute_deltas(results)
        for d in deltas:
            if d.worsened:
                self.alerts.warn(f"Check worsened: {d.uid}  {d.prev} → {d.curr}")
            elif d.improved:
                self.alerts.info(f"Check improved: {d.uid}  {d.prev} → {d.curr}")

        # Alert on blockers
        for ar in results:
            for c in ar.checks:
                if c.verdict == Verdict.FAIL and c.blocking:
                    self.alerts.error(f"BLOCKER: {c.uid} — {c.desc}", c.detail)

        # Write reports
        write_results(results, state, RESULTS_JSON, REPORT_TXT, self._cycle)

        elapsed = time.time() - start
        total = sum(len(r.checks) for r in results)
        passed = sum(r.passed for r in results)
        failed = sum(r.failed for r in results)
        warned = sum(r.warned for r in results)
        blocking = sum(r.blocking for r in results)

        self._log(
            f"Cycle #{self._cycle} done in {elapsed:.1f}s — "
            f"{total} checks: {passed}P {warned}W {failed}F {blocking}B"
        )

        # ── Auto-restart watchdog ──
        # Check if PH01 (training PID alive) is FAIL
        ph01_fail = any(
            c.uid == "PH01" and c.verdict == Verdict.FAIL and c.blocking
            for ar in results for c in ar.checks
        )
        if ph01_fail:
            self._dead_cycles += 1
            self._log(f"  Training DEAD cycle #{self._dead_cycles}/{AUTO_RESTART_CYCLES}")
            if self._dead_cycles >= AUTO_RESTART_CYCLES:
                self._auto_restart()
                self._dead_cycles = 0  # reset to prevent rapid re-restart
        else:
            if self._dead_cycles > 0:
                self._log("  Training alive again — resetting dead counter")
            self._dead_cycles = 0
