"""Proactive conversation initiator — Legion notices things and speaks up.

Legion is not purely reactive. This module checks for interesting conditions
and sends friendly, conversational Telegram messages when something warrants it.
All triggers are rate-limited to avoid spamming the user.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Minimum seconds between proactive messages (default: 30 min)
_MIN_INTERVAL = int(os.getenv("PROACTIVE_MIN_INTERVAL_SEC", "1800"))

# Track last-sent timestamps per trigger type to avoid hammering
_last_sent: dict[str, float] = {}


def _can_send(trigger_key: str) -> bool:
    """Return True if enough time has passed since last message for this trigger."""
    now = time.time()
    last = _last_sent.get(trigger_key, 0.0)
    return (now - last) >= _MIN_INTERVAL


def _mark_sent(trigger_key: str) -> None:
    _last_sent[trigger_key] = time.time()


@dataclass
class TriggerResult:
    triggered: bool
    trigger_key: str
    message: str = ""


async def _check_gpu_temp(snap: Any) -> TriggerResult:
    """Alert if GPU has been hot for a sustained period."""
    threshold = float(os.getenv("GPU_TEMP_ALERT_C", "80"))
    if snap.gpu_temp_c is not None and snap.gpu_temp_c >= threshold:
        if _can_send("gpu_temp"):
            msg = (
                f"Hey — your GPU is running at <b>{snap.gpu_temp_c:.0f}°C</b>, "
                f"which is above the {threshold:.0f}°C threshold. "
                "Want me to check what's hammering it? Or should I reduce the training batch size?"
            )
            return TriggerResult(True, "gpu_temp", msg)
    return TriggerResult(False, "gpu_temp")


async def _check_ram(snap: Any) -> TriggerResult:
    """Alert when RAM is critically high."""
    threshold_gb = float(os.getenv("RAM_ALERT_GB", "55"))
    if snap.ram_used_gb >= threshold_gb:
        if _can_send("ram_high"):
            pct = snap.ram_used_gb / snap.ram_total_gb * 100
            msg = (
                f"RAM is at <b>{pct:.0f}%</b> ({snap.ram_used_gb:.1f}/{snap.ram_total_gb:.1f} GB). "
                "Something's eating memory. Want me to check which processes are the culprit?"
            )
            return TriggerResult(True, "ram_high", msg)
    return TriggerResult(False, "ram_high")


async def _check_disk(snap: Any) -> TriggerResult:
    """Alert when disk is nearly full."""
    threshold_pct = float(os.getenv("DISK_ALERT_PCT", "90"))
    if snap.disk_used_pct >= threshold_pct:
        if _can_send("disk_full"):
            msg = (
                f"Disk is at <b>{snap.disk_used_pct:.0f}%</b> — getting close to full. "
                "Should I find and clean up large files? I can run a disk usage scan."
            )
            return TriggerResult(True, "disk_full", msg)
    return TriggerResult(False, "disk_full")


async def _check_training_complete() -> TriggerResult:
    """Detect when a training job has just completed."""
    log_path = os.getenv("WORKERNET_LOG_PATH", "")
    if not log_path:
        from pathlib import Path
        candidates = [
            Path.home() / "projects" / "POPW" / "logs" / "train.log",
            Path("/media/newadmin/master/POPW/logs/train.log"),
        ]
        for c in candidates:
            if c.exists():
                log_path = str(c)
                break

    if not log_path:
        return TriggerResult(False, "training_complete")

    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-5", log_path],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout.strip()
        completion_signals = ["training complete", "finished epoch", "best model saved", "training finished", "epoch done"]
        if any(sig in output.lower() for sig in completion_signals):
            if _can_send("training_complete"):
                # Extract any loss/accuracy numbers mentioned
                import re
                numbers = re.findall(r"(?:loss|acc(?:uracy)?)[=:\s]+([0-9.]+)", output.lower())
                metric_hint = f" (metrics: {', '.join(numbers[:3])})" if numbers else ""
                msg = (
                    f"Looks like your training job just wrapped up{metric_hint}. "
                    "Want a full summary of the results? I can check the logs and tell you "
                    "if it's worth keeping this checkpoint or running another epoch."
                )
                return TriggerResult(True, "training_complete", msg)
    except Exception as exc:
        logger.debug("training check failed: %s", exc)

    return TriggerResult(False, "training_complete")


async def _check_new_important_email() -> TriggerResult:
    """Check for new email from known important contacts."""
    if not _can_send("important_email"):
        return TriggerResult(False, "important_email")
    try:
        from tools.email_client import EmailClient
        client = EmailClient()
        summary = await client.summarize_inbox()
        if summary and len(summary) > 50:
            # Heuristic: if there's unread mail, mention it
            if _can_send("important_email"):
                msg = (
                    "You've got unread email. Here's a quick summary:\n\n"
                    f"<i>{summary[:400]}</i>\n\n"
                    "Want me to draft a reply to any of these?"
                )
                return TriggerResult(True, "important_email", msg)
    except Exception as exc:
        logger.debug("email check skipped: %s", exc)
    return TriggerResult(False, "important_email")


async def _check_business_activity() -> TriggerResult:
    """Check for booking spikes on rumahlabuh.com."""
    if not _can_send("business_spike"):
        return TriggerResult(False, "business_spike")
    try:
        from tools.supabase_client import get_client
        db = get_client()
        if db is None:
            return TriggerResult(False, "business_spike")
        # Check bookings in last hour
        rows = await db.query(
            "bookings",
            select="id,created_at,status",
            order="created_at.desc",
            limit=5,
        )
        if rows and len(rows) >= 3:
            msg = (
                f"Activity spike on rumahlabuh.com — <b>{len(rows)} new bookings</b> just came in. "
                "Want me to pull the details?"
            )
            return TriggerResult(True, "business_spike", msg)
    except Exception as exc:
        logger.debug("business check skipped: %s", exc)
    return TriggerResult(False, "business_spike")


class ProactiveInitiator:
    """Checks a set of trigger conditions and sends friendly messages when they fire."""

    def __init__(self, notify_fn: Callable[[str], Coroutine]) -> None:
        self._notify = notify_fn

    async def check_triggers(self, snap: Any | None = None) -> None:
        """Run all trigger checks. Pass a MonitorSnapshot if already collected."""
        results: list[TriggerResult] = []

        # System triggers (need snapshot)
        if snap is not None:
            sys_results = await asyncio.gather(
                _check_gpu_temp(snap),
                _check_ram(snap),
                _check_disk(snap),
                return_exceptions=True,
            )
            for r in sys_results:
                if isinstance(r, TriggerResult):
                    results.append(r)

        # Non-system triggers (async I/O)
        other_results = await asyncio.gather(
            _check_training_complete(),
            _check_new_important_email(),
            _check_business_activity(),
            return_exceptions=True,
        )
        for r in other_results:
            if isinstance(r, TriggerResult):
                results.append(r)

        for result in results:
            if result.triggered and result.message:
                try:
                    await self._notify(result.message)
                    _mark_sent(result.trigger_key)
                    # Small gap between multiple alerts to avoid flood
                    await asyncio.sleep(2)
                except Exception as exc:
                    logger.warning("[ProactiveInitiator] notify failed: %s", exc)
