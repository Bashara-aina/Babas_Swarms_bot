"""Proactive initiator — Legion talks first.

Runs as a background asyncio task. Periodically decides whether to send
an unsolicited message to Bashara based on time-of-day, emotion state,
recent activity, and cooldown. This is what makes Legion feel like Jarvis
instead of a passive chatbot.

Usage (already wired in main.py on_startup):
    from tools.proactive_initiator import start_proactive_initiator
    asyncio.create_task(start_proactive_initiator(bot, ALLOWED_USER_ID))
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
# Minimum gap between proactive messages (seconds). Default 90 min.
_MIN_INTERVAL = int(os.getenv("PROACTIVE_MIN_INTERVAL_SEC", "5400"))
# Max gap — ensures Legion checks in at least every N hours if nothing happened
_MAX_INTERVAL = int(os.getenv("PROACTIVE_MAX_INTERVAL_SEC", "21600"))  # 6h
# Probability of sending a message on each eligible check (0-1)
_SEND_PROBABILITY = float(os.getenv("PROACTIVE_SEND_PROB", "0.35"))

_last_sent: float = 0.0  # epoch seconds of last proactive message


def _is_quiet_hours() -> bool:
    """Return True if it's 01:00–07:00 JST (Bashara is likely asleep)."""
    jst_hour = (datetime.now(UTC).hour + 9) % 24
    return 1 <= jst_hour < 7


def _pick_trigger(user_id: int) -> str | None:
    """Return a proactive message topic, or None if Legion should stay quiet."""
    import time

    global _last_sent

    if _is_quiet_hours():
        return None

    elapsed = time.time() - _last_sent
    if elapsed < _MIN_INTERVAL:
        return None

    # Upcoming schedule in episodic memory → higher priority nudge
    try:
        from core.memory.episodic_store import get_episodic_store

        upcoming = get_episodic_store().get_upcoming_schedule(str(user_id), horizon_days=2)
        if upcoming and elapsed >= _MIN_INTERVAL:
            if elapsed >= _MAX_INTERVAL * 0.5 or random.random() < 0.4:
                return "schedule_nudge"
    except Exception:
        pass

    # Hard check-in after max interval
    if elapsed >= _MAX_INTERVAL:
        return random.choice(
            [
                "check_in",
                "resource_alert",
                "news_brief",
            ]
        )

    # Probabilistic trigger
    if random.random() > _SEND_PROBABILITY:
        return None

    return random.choice(
        [
            "check_in",
            "tip",
            "resource_alert",
            "news_brief",
            "memory_surface",
        ]
    )


async def _build_message(trigger: str, user_id: int | None = None) -> str:
    """Generate a context-appropriate proactive message."""
    jst_hour = (datetime.now(UTC).hour + 9) % 24

    if trigger == "check_in":
        greetings = [
            "Oi, masih hidup? Ada yang perlu gw bantu?",
            "Lo lagi ngerjain apa sekarang?",
            "Anything on your plate I should know about?",
            "Gw idle nih — ada task yang bisa gw handle?",
            "Status check: lo baik-baik aja? Ada yang stuck?",
        ]
        if 7 <= jst_hour < 12:
            greetings += ["Pagi! Ada agenda hari ini yang bisa gw bantu prep?"]
        elif jst_hour >= 20 or jst_hour < 1:
            greetings += ["Malam. Lo masih kerja? Kasih tau kalau butuh gw."]
        return random.choice(greetings)

    if trigger == "tip":
        tips = [
            "FYI: kalau lo pakai `asyncio.create_task()` jangan lupa handle exception-nya — silent failures are the worst.",
            "Reminder: commit message yang bagus itu `fix: <what> — <why>`, bukan cuma 'fix bug'.",
            "Quick tip: `git stash push -m 'wip'` instead of committing half-done work.",
            "Lo tau nggak ada shortcut `Ctrl+Shift+P` di VS Code buat command palette? Saves time.",
            "Kalau Supabase query lo lambat, check RLS policy dulu — sering bikin N+1 diam-diam.",
        ]
        return random.choice(tips)

    if trigger == "resource_alert":
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=0.2)
            mem = psutil.virtual_memory()
            ram_pct = mem.percent
            disk = psutil.disk_usage("/")
            alerts = []
            if cpu > 85:
                alerts.append(f"CPU {cpu:.0f}%")
            if ram_pct > 85:
                alerts.append(f"RAM {ram_pct:.0f}%")
            if disk.percent > 90:
                alerts.append(f"Disk {disk.percent:.0f}%")
            if alerts:
                return f"\u26a0\ufe0f Resource alert: {', '.join(alerts)} — lo mau gw cek apa yang makan resource?"
            # No alert — fallback to check-in
            return await _build_message("check_in", user_id)
        except Exception:
            return await _build_message("check_in", user_id)

    if trigger == "news_brief":
        try:
            from tools.briefing import get_quick_brief

            brief = await get_quick_brief()
            if brief:
                return f"\U0001f4f0 Quick brief:\n{brief[:800]}"
        except Exception:
            pass
        return await _build_message("check_in", user_id)

    if trigger == "memory_surface":
        try:
            from tools.mem0_client import mem0_search

            mems = await mem0_search("bashara", "recent important", limit=1)
            if mems:
                content = mems[0].get("memory") or mems[0].get("content", "")
                if content:
                    return f'Eh, gw inget lo pernah bilang: "{content[:200]}" — masih relevan nggak?'
        except Exception:
            pass
        return await _build_message("check_in", user_id)

    if trigger == "schedule_nudge":
        try:
            from core.memory.episodic_store import get_episodic_store

            uid = str(user_id) if user_id is not None else os.getenv("ALLOWED_USER_ID", "0")
            upcoming = get_episodic_store().get_upcoming_schedule(uid, horizon_days=2)
            if upcoming:
                lines = [
                    "\U0001f4c5 Heads-up — lo punya ini di kalender (dari memory gw):",
                ]
                for ep in upcoming[:4]:
                    lines.append(f"  • {ep.get('summary', '')[:120]}")
                lines.append("Perlu gw bantu prep atau reminder tambahan?")
                return "\n".join(lines)
        except Exception:
            pass
        return await _build_message("check_in", user_id)

    return "Gw masih di sini kalau lo butuh sesuatu."


async def start_proactive_initiator(bot: Bot, user_id: int) -> None:
    """Main loop — runs forever as a background task."""
    import time

    global _last_sent

    logger.info("Proactive initiator started (min_interval=%ds, prob=%.0f%%)", _MIN_INTERVAL, _SEND_PROBABILITY * 100)

    # Initial jitter: don't fire immediately on startup
    await asyncio.sleep(random.uniform(300, 900))

    while True:
        try:
            trigger = _pick_trigger(user_id)
            if trigger:
                message = await _build_message(trigger, user_id)
                await bot.send_message(user_id, message)
                _last_sent = time.time()
                logger.info("[Proactive] Sent (%s): %s", trigger, message[:80])
        except Exception as e:
            logger.warning("Proactive initiator error (non-fatal): %s", e)

        # Sleep until next check (every 15-30 min)
        await asyncio.sleep(random.uniform(900, 1800))
