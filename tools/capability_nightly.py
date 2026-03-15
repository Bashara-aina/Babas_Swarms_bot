"""Nightly capability regression loop.

Runs benchmark+red-team suite daily and sends report to Telegram.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _seconds_until(hour: int, minute: int) -> float:
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return max(5.0, (target - now).total_seconds())


async def run_nightly_capability_once(bot, user_id: int) -> None:
    """Execute one full nightly capability suite and send report."""
    from tools.capability_benchmark import run_capability_suite, render_suite_report_html
    from tools.capability_metrics import render_capability_summary_html

    report = await run_capability_suite(user_id=str(user_id), include_redteam=True)
    text = render_suite_report_html(report, title="Nightly Capability + Red-Team")
    summary = render_capability_summary_html(hours=168)

    for chunk in [text, "\n\n" + summary]:
        chunk = chunk.strip()
        if not chunk:
            continue
        for i in range(0, len(chunk), 3800):
            await bot.send_message(user_id, chunk[i : i + 3800], parse_mode="HTML")


async def schedule_nightly_capability_report(
    bot,
    user_id: int,
    *,
    hour: int = 3,
    minute: int = 40,
) -> None:
    """Background loop to run nightly capability regression reports."""
    logger.info("Nightly capability regression scheduled for %02d:%02d", hour, minute)
    while True:
        wait_s = _seconds_until(hour, minute)
        await asyncio.sleep(wait_s)
        try:
            await run_nightly_capability_once(bot, user_id)
        except Exception as exc:
            logger.warning("Nightly capability report failed (non-fatal): %s", exc)
        await asyncio.sleep(2)
