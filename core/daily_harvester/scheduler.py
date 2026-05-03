"""DailyHarvesterScheduler — runs HarvestPipeline when Legion bot starts and every 24h."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime

import pytz

logger = logging.getLogger(__name__)

WIB = pytz.timezone("Asia/Jakarta")
HARVEST_HOUR = 4  # 04:00 WIB
HARVEST_MINUTE = 0


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
        """Run harvest pipeline at 04:00 WIB every 24h."""
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

            await self._run_harvest()

    async def _run_harvest(self) -> None:
        """Execute one harvest pipeline run."""
        from core.daily_harvester.harvest_pipeline import HarvestPipeline

        logger.info("DailyHarvesterScheduler: starting harvest pipeline")
        try:
            pipeline = HarvestPipeline()
            result = await pipeline.run_full_pipeline()
            if self._notify and result.get("report"):
                await self._notify(result["report"][:4000])
            logger.info(
                "Harvest complete: %d accepted, %d rejected, %d conflicts",
                result.get("accepted_count", 0),
                result.get("rejected_count", 0),
                result.get("conflicts_count", 0),
            )
        except Exception as e:
            logger.error("Harvest pipeline failed: %s", e, exc_info=True)
            if self._notify:
                await self._notify(f"Harvest failed: {e}"[:4000])
