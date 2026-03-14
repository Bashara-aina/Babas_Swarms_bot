"""Auto-cleanup for temporary screenshot files.

Screenshots in /tmp/legion_*.png accumulate indefinitely.
This module provides both a manual cleanup and an async periodic task.

Usage:
    from core.tmp_cleanup import cleanup_screenshots, start_cleanup_task
    asyncio.create_task(start_cleanup_task(interval_seconds=300))
"""
import asyncio
import glob
import logging
import os
import time

logger = logging.getLogger(__name__)

SCREENSHOT_PATTERN = "/tmp/legion_*.png"
MAX_AGE_SECONDS = 30 * 60  # 30 minutes


def cleanup_screenshots(max_age_seconds: int = MAX_AGE_SECONDS) -> int:
    """Delete screenshot files older than max_age_seconds. Returns count deleted."""
    deleted = 0
    cutoff = time.time() - max_age_seconds
    for path in glob.glob(SCREENSHOT_PATTERN):
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
                deleted += 1
                logger.debug("Deleted stale screenshot: %s", path)
        except OSError as e:
            logger.warning("Could not delete %s: %s", path, e)
    return deleted


async def start_cleanup_task(interval_seconds: int = 300) -> None:
    """Async background task: clean up old screenshots every interval_seconds."""
    logger.info("Screenshot cleanup task started (interval=%ds)", interval_seconds)
    while True:
        try:
            n = cleanup_screenshots()
            if n:
                logger.info("Cleaned up %d stale screenshot(s)", n)
        except Exception as e:
            logger.warning("Screenshot cleanup error: %s", e)
        await asyncio.sleep(interval_seconds)
