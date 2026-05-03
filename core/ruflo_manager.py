"""Ruflo sidecar process manager with health monitoring.

Stores the ruflo subprocess handle and runs periodic health checks.
"""

import asyncio
import logging
import subprocess
from urllib import request as urlrequest

logger = logging.getLogger(__name__)

# Global ruflo process handle
_ruflo_process: subprocess.Popen | None = None
_ruflo_monitor_task: asyncio.Task | None = None


def _restart_health_monitor() -> None:
    """Restart the ruflo health monitor if it has died."""
    global _ruflo_monitor_task
    if _ruflo_monitor_task is None or _ruflo_monitor_task.done():
        _ruflo_monitor_task = asyncio.create_task(ruflo_health_monitor())
        _ruflo_monitor_task.add_done_callback(
            lambda t: logger.error("Ruflo health monitor died: %s", t.exception()) if not t.cancelled() and t.exception() else None
        )
        logger.info("Ruflo health monitor restarted")


def set_ruflo_process(proc: subprocess.Popen) -> None:
    """Store the ruflo process handle."""
    global _ruflo_process
    _ruflo_process = proc
    logger.info("Ruflo process handle stored (PID: %s)", proc.pid)


def get_ruflo_process() -> subprocess.Popen | None:
    """Get the current ruflo process handle."""
    return _ruflo_process


def _ruflo_health_probe_sync(url: str = "http://127.0.0.1:7834/health") -> bool:
    """Synchronous health probe for ruflo sidecar."""
    try:
        req = urlrequest.Request(url=url, method="GET")
        with urlrequest.urlopen(req, timeout=2) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return response.status == 200 and '"ok":true' in body.replace(" ", "")
    except Exception:
        return False


async def check_ruflo_health() -> bool:
    """Check if ruflo sidecar is healthy."""
    return await asyncio.to_thread(_ruflo_health_probe_sync)


async def ruflo_health_monitor() -> None:
    """Background task that pings ruflo health every 5 minutes.

    P0-3: Add health-check ping every 5 minutes.
    """
    interval_seconds = 300  # 5 minutes

    while True:
        await asyncio.sleep(interval_seconds)

        if _ruflo_process is None:
            logger.debug("Ruflo health check: no process handle stored")
            continue

        # Check if process is still running
        if _ruflo_process.poll() is not None:
            logger.warning("Ruflo process has died (exit code: %s)", _ruflo_process.returncode)
            continue

        # Ping health endpoint
        try:
            healthy = await check_ruflo_health()
            if healthy:
                logger.info("✅ Ruflo health check: OK (PID: %s)", _ruflo_process.pid)
            else:
                logger.warning("⚠️ Ruflo health check failed but process is running")
        except Exception as e:
            logger.warning("Ruflo health check error: %s", e)


def start_health_monitor() -> asyncio.Task:
    """Start the ruflo health monitor background task.

    Returns:
        The asyncio Task handle.
    """
    global _ruflo_monitor_task
    if _ruflo_monitor_task is not None and not _ruflo_monitor_task.done():
        return _ruflo_monitor_task
    _ruflo_monitor_task = asyncio.create_task(ruflo_health_monitor())
    _ruflo_monitor_task.add_done_callback(
        lambda t: (
            logger.error("Ruflo health monitor died: %s", t.exception())
            if not t.cancelled() and t.exception() else None
        )
    )
    logger.info("Ruflo health monitor started (5-minute interval)")
    return _ruflo_monitor_task
