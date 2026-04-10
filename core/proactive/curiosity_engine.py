"""Proactive curiosity engine — Legion initiates conversation autonomously.

Checks three signal sources on a configurable interval:
1. Pending follow-up questions from data/beliefs.json
2. rumahlabuh.com site health (via tools/browser_agent.py)
3. Sleep pattern — if Bashara hasn't messaged in >8 hours, check in

Rate-limited to MAX_PROACTIVE_PER_DAY messages (default: 3).
Only fires if Legion hasn't heard from the user in at least QUIET_MINUTES minutes
(to avoid interrupting an active session).

Env vars:
  MAX_PROACTIVE_PER_DAY     — int, default 3
  CURIOSITY_INTERVAL_MIN    — int, minutes between checks, default 60
  CURIOSITY_QUIET_MIN       — int, min silence before interrupting, default 30
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable, Awaitable
from datetime import datetime

logger = logging.getLogger(__name__)

# Configurable via env
_MAX_PER_DAY = int(os.getenv("MAX_PROACTIVE_PER_DAY", "3"))
_INTERVAL_SEC = int(os.getenv("CURIOSITY_INTERVAL_MIN", "60")) * 60
_QUIET_SEC = int(os.getenv("CURIOSITY_QUIET_MIN", "30")) * 60

# Japan timezone offset (UTC+9) — no pytz needed
_JST_OFFSET_HOURS = 9


def _jst_hour() -> int:
    """Return current hour in JST (UTC+9)."""
    utc_hour = datetime.utcnow().hour
    return (utc_hour + _JST_OFFSET_HOURS) % 24


def _today_str() -> str:
    """Return current date in JST as YYYY-MM-DD."""
    utc_now = datetime.utcnow()
    # Approximate JST date
    jst_hour = (utc_now.hour + _JST_OFFSET_HOURS) % 24
    jst_day_bump = (utc_now.hour + _JST_OFFSET_HOURS) // 24
    from datetime import timedelta
    jst_date = (utc_now + timedelta(days=jst_day_bump)).date()
    return str(jst_date)


class _CuriosityState:
    """Tracks daily send count and last fire time."""
    sent_today: int = 0
    last_date: str = ""
    last_fire_ts: float = 0.0

    def reset_if_new_day(self) -> None:
        today = _today_str()
        if today != self.last_date:
            self.sent_today = 0
            self.last_date = today

    def can_send(self) -> bool:
        self.reset_if_new_day()
        return self.sent_today < _MAX_PER_DAY

    def record_send(self) -> None:
        self.sent_today += 1
        self.last_fire_ts = time.monotonic()


_state = _CuriosityState()


async def _check_pending_followups() -> str | None:
    """Return a follow-up message if there are pending items in beliefs.json."""
    try:
        from core.soul_engine import get_pending_followups
        followups = get_pending_followups()
        if followups:
            task_text = followups[0].get("task", str(followups[0])) if isinstance(followups[0], dict) else str(followups[0])
            return (
                f"Hey — I've been meaning to ask: {task_text}\n"
                f"(I'll keep bugging you about this until it's done or dismissed)"
            )
    except Exception as exc:
        logger.debug("[CuriosityEngine] followup check failed: %s", exc)
    return None


async def _check_site_health() -> str | None:
    """Check rumahlabuh.com and alert if degraded."""
    try:
        from tools.browser_agent import check_site_health, format_health_for_prompt
        health = await check_site_health()
        if health.get("status") in ("degraded", "unreachable"):
            return (
                f"Heads up — rumahlabuh.com looks unhealthy right now.\n"
                f"{format_health_for_prompt(health)}\n"
                f"Want me to dig into the Supabase logs or check the deployment?"
            )
    except Exception as exc:
        logger.debug("[CuriosityEngine] site health check failed: %s", exc)
    return None


async def _check_sleep_pattern(get_last_user_ts: Callable[[], float]) -> str | None:
    """If no message in >8h during typical waking hours, send a check-in."""
    silence_sec = time.time() - get_last_user_ts()
    jst_hour = _jst_hour()

    # Only check in during Tokyo daytime (9am–11pm JST), after 8h of silence
    if 9 <= jst_hour <= 23 and silence_sec > 8 * 3600:
        silence_h = int(silence_sec // 3600)
        return (
            f"You've been quiet for about {silence_h} hours. Everything good? "
            f"Anything you want me to prep or check while I'm idle?"
        )
    return None


async def run_curiosity_loop(
    notify: Callable[[str], Awaitable[None]],
    get_last_user_ts: Callable[[], float],
) -> None:
    """
    Main loop — runs forever as an asyncio background task.

    Args:
        notify: async callable that sends a Telegram message to Bashara
        get_last_user_ts: callable returning float timestamp of last user message
    """
    logger.info("[CuriosityEngine] started (interval=%ds, max_per_day=%d)", _INTERVAL_SEC, _MAX_PER_DAY)
    # Initial delay to let the bot fully start
    await asyncio.sleep(120)

    while True:
        try:
            await _tick(notify, get_last_user_ts)
        except Exception as exc:
            logger.warning("[CuriosityEngine] tick error: %s", exc)
        await asyncio.sleep(_INTERVAL_SEC)


async def _tick(
    notify: Callable[[str], Awaitable[None]],
    get_last_user_ts: Callable[[], float],
) -> None:
    """Single curiosity check cycle."""
    if not _state.can_send():
        logger.debug("[CuriosityEngine] daily limit reached (%d/%d)", _state.sent_today, _MAX_PER_DAY)
        return

    # Don't interrupt an active session
    silence_sec = time.time() - get_last_user_ts()
    if silence_sec < _QUIET_SEC:
        logger.debug(
            "[CuriosityEngine] user active %.0f min ago — skipping", silence_sec / 60
        )
        return

    # Don't fire too often even within daily budget
    since_last = time.monotonic() - _state.last_fire_ts
    if _state.last_fire_ts > 0 and since_last < _INTERVAL_SEC * 0.8:
        return

    # Check signals in priority order
    message = (
        await _check_pending_followups()
        or await _check_site_health()
        or await _check_sleep_pattern(get_last_user_ts)
    )

    if message:
        _state.record_send()
        logger.info("[CuriosityEngine] firing proactive message (%d/%d today)", _state.sent_today, _MAX_PER_DAY)
        await notify(message)
