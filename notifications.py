# /home/newadmin/swarm-bot/notifications.py
"""Proactive notification manager.

Sends alerts to the owner Telegram user for:
  - Rate limit approaching (from usage_tracker)
  - Recurring error patterns (from error_recovery)
  - Long task completion (from executor)

All methods are fire-and-forget coroutines — they should be awaited but
never raise to the caller.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)

_bot: Optional[Bot] = None
_user_id: int = 0


def init(bot: Bot, user_id: int) -> None:
    """Initialize module with bot and owner user_id (called at startup)."""
    global _bot, _user_id
    _bot = bot
    _user_id = user_id


async def _send(text: str) -> None:
    """Send a proactive message to the owner, silently ignoring errors."""
    if not _bot or not _user_id:
        return
    try:
        await _bot.send_message(_user_id, text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("Notification failed: %s", exc)


# ── Public notification senders ────────────────────────────────────────────────

async def rate_limit_alert(model: str, current: int, limit: int) -> None:
    """Warn when approaching a daily rate limit.

    Args:
        model: Model identifier string.
        current: Current request count.
        limit: Daily limit.
    """
    pct = int(current / limit * 100)
    remaining = limit - current
    await _send(
        f"⚠️ <b>Rate Limit Warning</b>\n\n"
        f"<b>Model:</b> <code>{model}</code>\n"
        f"<b>Usage:</b> {current:,}/{limit:,} requests ({pct}%)\n"
        f"<b>Remaining:</b> {remaining:,} requests today\n\n"
        f"<i>Consider switching to an alternative model.</i>"
    )


async def task_complete(description: str, duration_s: float, agent: str) -> None:
    """Notify when a long-running task finishes.

    Args:
        description: Task description (first 100 chars).
        duration_s: Total wall-clock time in seconds.
        agent: Agent that ran the task.
    """
    if duration_s < 15:   # Don't clutter for fast tasks
        return
    mins, secs = divmod(int(duration_s), 60)
    time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
    await _send(
        f"✅ <b>Task Complete</b>\n\n"
        f"<b>Agent:</b> {agent}\n"
        f"<b>Duration:</b> {time_str}\n\n"
        f"<i>{description[:100]}</i>"
    )


async def error_pattern_detected(error_type: str, count: int, agent: str) -> None:
    """Alert on a recurring error pattern.

    Args:
        error_type: Short error category (e.g. "TimeoutError").
        count: How many times seen today.
        agent: Agent that keeps failing.
    """
    await _send(
        f"🔴 <b>Recurring Error Detected</b>\n\n"
        f"<b>Error:</b> <code>{error_type}</code>\n"
        f"<b>Agent:</b> {agent}\n"
        f"<b>Occurrences today:</b> {count}\n\n"
        f"<i>Consider checking the circuit breaker status with /circuits</i>"
    )


async def circuit_opened(agent: str) -> None:
    """Alert when a circuit breaker trips open.

    Args:
        agent: Agent whose circuit just opened.
    """
    await _send(
        f"⚡ <b>Circuit Breaker Opened</b>\n\n"
        f"<b>Agent:</b> <code>{agent}</code>\n\n"
        f"Requests to this agent will fail-fast for 60 seconds.\n"
        f"Use /circuits to check status."
    )


async def gpu_memory_alert(used_gb: float, total_gb: float) -> None:
    """Alert on high GPU VRAM usage.

    Args:
        used_gb: Current VRAM used in GB.
        total_gb: Total VRAM in GB.
    """
    pct = int(used_gb / total_gb * 100)
    await _send(
        f"🎮 <b>GPU Memory Alert</b>\n\n"
        f"<b>VRAM:</b> {used_gb:.1f}/{total_gb:.1f} GB ({pct}%)\n\n"
        f"<i>Run <code>ollama stop &lt;model&gt;</code> to free memory.</i>"
    )


async def model_fallback_used(primary: str, fallback: str, reason: str) -> None:
    """Inform when a fallback model was used instead of primary.

    Args:
        primary: Model that failed.
        fallback: Model that was used instead.
        reason: Short reason for fallback.
    """
    await _send(
        f"🔄 <b>Model Fallback</b>\n\n"
        f"<b>Primary:</b> <code>{primary}</code> — failed\n"
        f"<b>Fallback:</b> <code>{fallback}</code> — used\n"
        f"<b>Reason:</b> {reason[:100]}"
    )
