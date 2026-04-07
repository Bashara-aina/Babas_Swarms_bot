"""Proactive system monitors that can alert the user when thresholds are exceeded."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class MonitorSnapshot:
    cpu_pct: float
    ram_used_gb: float
    ram_total_gb: float
    disk_used_pct: float
    gpu_temp_c: float | None


async def get_snapshot() -> MonitorSnapshot:
    """Collect a compact snapshot of system state."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    gpu_temp: float | None = None
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            raw = (result.stdout or "").strip().splitlines()
            if raw:
                gpu_temp = float(raw[0].strip())
    except Exception:
        gpu_temp = None

    return MonitorSnapshot(
        cpu_pct=psutil.cpu_percent(interval=0.2),
        ram_used_gb=mem.used / (1024 ** 3),
        ram_total_gb=mem.total / (1024 ** 3),
        disk_used_pct=disk.percent,
        gpu_temp_c=gpu_temp,
    )


async def monitor_loop(bot: Any, user_id: int, interval_seconds: int = 300) -> None:
    """Background alert loop — routes through ProactiveInitiator for friend-like messages."""
    if os.getenv("ENABLE_PROACTIVE_MONITORS", "true").lower() not in {"1", "true", "yes", "on"}:
        return

    from core.proactive.proactive_initiator import ProactiveInitiator

    async def _notify(text: str) -> None:
        await bot.send_message(user_id, text, parse_mode="HTML")

    initiator = ProactiveInitiator(notify_fn=_notify)

    while True:
        try:
            snap = await get_snapshot()
            await initiator.check_triggers(snap=snap)
        except Exception as exc:
            logger.debug("monitor loop error: %s", exc)
        await asyncio.sleep(interval_seconds)


async def start_monitors(bot: Any, user_id: int) -> list[asyncio.Task]:
    """Start proactive monitors."""
    if os.getenv("ENABLE_PROACTIVE_MONITORS", "true").lower() not in {"1", "true", "yes", "on"}:
        return []
    task = asyncio.create_task(monitor_loop(bot, user_id))
    return [task]
