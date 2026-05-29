"""DailyHarvesterScheduler — runs HarvestPipeline when Legion bot starts and every 24h."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable, Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any

import pytz

logger = logging.getLogger(__name__)

WIB = pytz.timezone("Asia/Jakarta")
HARVEST_HOUR = 4  # 04:00 WIB
HARVEST_MINUTE = 0

# Default 10-minute inactivity limit; HERMES_CRON_TIMEOUT env var overrides
_CRON_TIMEOUT_ENV = "HERMES_CRON_TIMEOUT"
_DEFAULT_INACTIVITY_LIMIT = 600.0  # seconds

# Pre-harvest script hook with path traversal protection (hermes pattern)
_HARVEST_SCRIPT_ENV = "HERMES_HARVEST_SCRIPT"


def _parse_wake_gate(script_output: str) -> bool:
    """Parse last non-empty stdout line as JSON wake gate.

    Convention (nanoclaw #1232): if the last stdout line is
    JSON like ``{"wakeAgent": false}``, skip the harvest entirely.
    Any other output means wake normally.
    """
    if not script_output:
        return True
    stripped_lines = [line for line in script_output.splitlines() if line.strip()]
    if not stripped_lines:
        return True
    last_line = stripped_lines[-1].strip()
    try:
        gate = json.loads(last_line)
        return gate.get("wakeAgent", True) is not False
    except (json.JSONDecodeError, ValueError):
        return True


def _run_precheck_script(script_path: str | None) -> tuple[bool, str]:
    """Execute pre-harvest script with path traversal protection.

    Scripts must reside within SWARM_BOT_HOME/scripts/.
    Both relative and absolute paths are resolved and validated.
    """
    if not script_path:
        return True, ""
    scripts_dir = Path(os.getcwd()) / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir_resolved = scripts_dir.resolve()

    raw = Path(script_path).expanduser()
    path = raw.resolve() if raw.is_absolute() else (scripts_dir / raw).resolve()

    try:
        path.relative_to(scripts_dir_resolved)
    except ValueError:
        return False, f"Blocked: script path resolves outside scripts dir ({scripts_dir_resolved}): {script_path!r}"

    if not path.exists():
        return False, f"Script not found: {path}"
    if not path.is_file():
        return False, f"Script path is not a file: {path}"

    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0, (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return False, f"Script timed out after 60s: {path}"
    except Exception as e:
        return False, f"Script error: {e}"


def _parse_inactivity_limit(raw: str | None) -> float | None:
    """Parse HERMES_CRON_TIMEOUT env var with safe fallback."""
    if raw:
        try:
            val = float(raw.strip())
            return val if val > 0 else None  # 0 = unlimited
        except (ValueError, TypeError):
            return _DEFAULT_INACTIVITY_LIMIT
    return _DEFAULT_INACTIVITY_LIMIT


def _wib_now() -> datetime:
    return datetime.now(WIB)


class DailyHarvesterScheduler:
    """
    Starts HarvestPipeline when Legion bot is ON and reschedules every 24h.

    Runs at 04:00 WIB every day (or immediately on startup if that time has passed).
    """

    def __init__(
        self,
        notify: Callable[[str], Coroutine] | None = None,
        user_id: int | None = None,
    ) -> None:
        self._pipeline_task: asyncio.Task | None = None
        self._notify = notify
        self._user_id = user_id
        self._running = False
        # Activity tracking (mirrors hermes cron inactivity monitor)
        self._last_activity_ts = time.time()
        self._last_activity_desc = "idle"
        self._current_tool: str | None = None
        self._api_call_count = 0
        self.max_iterations = 0

    def get_activity_summary(self) -> dict:
        """Return a snapshot of the scheduler's current activity for diagnostics."""
        elapsed = time.time() - self._last_activity_ts
        return {
            "last_activity_ts": self._last_activity_ts,
            "last_activity_desc": self._last_activity_desc,
            "seconds_since_activity": round(elapsed, 1),
            "current_tool": self._current_tool,
            "api_call_count": self._api_call_count,
            "max_iterations": self.max_iterations,
        }

    def _update_activity(self, desc: str, tool: str | None = None) -> None:
        """Mark that the scheduler is actively working."""
        self._last_activity_ts = time.time()
        self._last_activity_desc = desc
        self._current_tool = tool
        self._api_call_count += 1

    def start(self) -> None:
        """Start the 24h harvest loop."""
        if self._running:
            logger.warning("DailyHarvesterScheduler already running")
            return
        self._running = True
        self._pipeline_task = asyncio.create_task(self._run_loop())
        logger.info("DailyHarvesterScheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._pipeline_task:
            self._pipeline_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._pipeline_task
        logger.info("DailyHarvesterScheduler stopped")

    async def _run_loop(self) -> None:
        """Run harvest pipeline at 04:00 WIB every 24h with inactivity monitoring."""
        import os

        raw_timeout = os.getenv(_CRON_TIMEOUT_ENV)
        inactivity_limit = _parse_inactivity_limit(raw_timeout)
        poll_interval = 5.0

        while self._running:
            now = _wib_now()
            next_run = now.replace(hour=HARVEST_HOUR, minute=HARVEST_MINUTE, second=0, microsecond=0)
            if now.hour >= HARVEST_HOUR:
                next_run = next_run.replace(day=now.day + 1)
            seconds_until = (next_run - now).total_seconds()
            if seconds_until <= 0:
                seconds_until = 86400

            logger.info("Next harvest scheduled at %s WIB (in %.0f seconds)", next_run.isoformat(), seconds_until)

            try:
                await asyncio.sleep(seconds_until)
            except asyncio.CancelledError:
                break

            if not self._running:
                break

            # Run pre-check script with wake gate (hermes pattern)
            pre_script = os.getenv(_HARVEST_SCRIPT_ENV)
            ran_ok, script_output = _run_precheck_script(pre_script)
            if ran_ok and not _parse_wake_gate(script_output):
                logger.info(
                    "Harvest pre-check: wakeAgent=false, skipping harvest (script: %s)",
                    pre_script or "none",
                )
                continue

            await self._run_harvest_with_timeout(inactivity_limit, poll_interval)

    async def _run_harvest_with_timeout(
        self, inactivity_limit: float | None, poll_interval: float
    ) -> None:
        """Execute harvest pipeline with inactivity-based timeout (hermes pattern)."""
        from core.daily_harvester.harvest_pipeline import HarvestPipeline

        inactivity_timeout = False
        result: dict[str, Any] = {}

        async def _run():
            nonlocal result
            self._update_activity("harvest_pipeline_start")
            pipeline = HarvestPipeline()
            result = await pipeline.run_full_pipeline()

        async def _poll_inactivity():
            """Poll for inactivity timeout while pipeline runs."""
            nonlocal inactivity_timeout
            while not inactivity_timeout:
                await asyncio.sleep(poll_interval)
                if inactivity_limit is not None:
                    act = self.get_activity_summary()
                    idle = act.get("seconds_since_activity", 0.0)
                    if idle >= inactivity_limit:
                        inactivity_timeout = True
                        break

        try:
            if inactivity_limit is None:
                # Unlimited — just await
                await _run()
            else:
                # Run pipeline and inactivity poller concurrently
                poll_task = asyncio.create_task(_poll_inactivity())
                run_task = asyncio.create_task(_run())

                done, _ = await asyncio.wait(
                    {run_task, poll_task}, return_when=asyncio.FIRST_COMPLETED
                )

                for t in done:
                    if t == poll_task and not run_task.done():
                        # Inactivity timeout fired
                        run_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await run_task
                        break
                    elif t == run_task and not poll_task.done():
                        # Pipeline finished first — cancel the poller
                        poll_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await poll_task
                        break

                if inactivity_timeout:
                    act = self.get_activity_summary()
                    logger.error(
                        "Harvest idle for %.0fs (inactivity limit %.0fs) "
                        "| last_activity=%s | api_call_count=%s",
                        act.get("seconds_since_activity", 0),
                        inactivity_limit,
                        act.get("last_activity_desc", "unknown"),
                        act.get("api_call_count", 0),
                    )
                    raise TimeoutError(
                        f"Harvest idle for {int(act.get('seconds_since_activity', 0))}s "
                        f"(limit {int(inactivity_limit)}s)"
                    )

            # Pipeline completed successfully
            if self._notify and result.get("report"):
                await self._notify(result["report"][:4000])
            logger.info(
                "Harvest complete: %d accepted, %d rejected, %d conflicts",
                result.get("accepted_count", 0),
                result.get("rejected_count", 0),
                result.get("conflicts_count", 0),
            )
        except TimeoutError:
            raise
        except Exception as e:
            logger.error("Harvest pipeline failed: %s", e, exc_info=True)
            if self._notify:
                await self._notify(f"Harvest failed: {e}"[:4000])
