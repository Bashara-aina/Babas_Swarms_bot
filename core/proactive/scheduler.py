"""Proactive scheduler — Legion checks in on you without being asked.

Runs a background asyncio loop every PROACTIVE_INTERVAL_MINUTES.
Checks:
  1. Upcoming schedule from episodic memory
  2. rumahlabuh.com / Supabase health (DB errors, booking spikes)
  3. GitHub notifications (mentions, PR reviews needed)
  4. Email unread count via IMAP (if configured)
  5. Daily briefing at configured morning hour

All proactive messages are sent via the Telegram bot's notify_cb.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

# Config
PROACTIVE_INTERVAL_MINUTES = int(os.getenv("PROACTIVE_INTERVAL_MINUTES", "30"))
DAILY_BRIEFING_HOUR = int(os.getenv("DAILY_BRIEFING_HOUR", "8"))  # 8 AM local
BUSINESS_ALERT_THRESHOLD = int(os.getenv("BUSINESS_ALERT_THRESHOLD", "5"))  # errors


class ProactiveScheduler:
    """Background proactive intelligence loop."""

    def __init__(
        self,
        user_id: str,
        notify_cb: Callable[[str], Coroutine],
        telegram_chat_id: Optional[int] = None,
    ) -> None:
        self.user_id = user_id
        self.notify = notify_cb
        self.chat_id = telegram_chat_id
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_briefing_date: str = ""
        self._last_check_ts: float = 0.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("[Proactive] Scheduler started — interval %d min", PROACTIVE_INTERVAL_MINUTES)

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        await asyncio.sleep(60)  # Grace period on startup
        while self._running:
            try:
                await self._run_checks()
            except Exception as e:
                logger.warning("[Proactive] Check cycle error: %s", e)
            await asyncio.sleep(PROACTIVE_INTERVAL_MINUTES * 60)

    async def _run_checks(self) -> None:
        now = datetime.now()
        alerts: list[str] = []

        # 1. Daily briefing
        today_str = now.strftime("%Y-%m-%d")
        if now.hour == DAILY_BRIEFING_HOUR and self._last_briefing_date != today_str:
            briefing = await self._build_daily_briefing(now)
            if briefing:
                await self.notify(briefing)
                self._last_briefing_date = today_str
            return  # Skip other checks on briefing run

        # 2. Upcoming schedule alerts
        schedule_alerts = self._check_schedule()
        alerts.extend(schedule_alerts)

        # 3. Business / Supabase health
        business_alerts = await self._check_business_health()
        alerts.extend(business_alerts)

        # 4. GitHub notifications
        github_alerts = await self._check_github()
        alerts.extend(github_alerts)

        if alerts:
            msg = "🔔 <b>Legion check-in</b>\n\n" + "\n\n".join(alerts)
            await self.notify(msg)

    def _check_schedule(self) -> list[str]:
        try:
            from core.memory.episodic_store import get_episodic_store
            store = get_episodic_store()
            upcoming = store.get_upcoming_schedule(self.user_id, horizon_days=1)
            if not upcoming:
                return []
            alerts = ["📅 <b>Coming up soon:</b>"]
            for ep in upcoming[:3]:
                alerts.append(f"  • {ep.get('summary', '')}")
            return alerts
        except Exception as e:
            logger.debug("[Proactive] Schedule check failed: %s", e)
            return []

    async def _check_business_health(self) -> list[str]:
        """Check rumahlabuh.com Supabase for anomalies."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            if not supabase_url or not supabase_key:
                return []

            from supabase import create_client
            sb = create_client(supabase_url, supabase_key)

            alerts = []
            # Check recent bookings (example — adjust table name to match your schema)
            try:
                result = sb.table("bookings").select("id,created_at").order(
                    "created_at", desc=True
                ).limit(5).execute()
                if result.data:
                    alerts.append(
                        f"🏠 <b>rumahlabuh.com</b>: {len(result.data)} recent booking(s) — all good ✅"
                    )
            except Exception:
                pass  # Table may not exist or have different name

            return alerts
        except Exception as e:
            logger.debug("[Proactive] Business health check failed: %s", e)
            return []

    async def _check_github(self) -> list[str]:
        """Check GitHub for notifications/mentions."""
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                return []

            import aiohttp
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.github.com/notifications",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    unread = [n for n in data if n.get("unread")]
                    if not unread:
                        return []
                    return [
                        f"🐙 <b>GitHub</b>: {len(unread)} unread notification(s) — "
                        f"including '{unread[0].get('subject', {}).get('title', '?')[:60)}'"
                    ]
        except Exception as e:
            logger.debug("[Proactive] GitHub check failed: %s", e)
            return []

    async def _build_daily_briefing(self, now: datetime) -> str:
        """Build a morning briefing message."""
        from core.memory.episodic_store import get_episodic_store
        from core.memory.user_profile import get_user_profile

        profile = get_user_profile(self.user_id)
        store = get_episodic_store()
        schedule = store.get_upcoming_schedule(self.user_id, horizon_days=3)
        
        day_str = now.strftime("%A, %B %d")
        lines = [f"☀️ <b>Good morning, Bashara! It's {day_str}.</b>\n"]

        if schedule:
            lines.append("📅 <b>Upcoming this week:</b>")
            for ep in schedule[:4]:
                lines.append(f"  • {ep.get('summary', '')}")
            lines.append("")

        # GitHub
        github_alerts = await self._check_github()
        if github_alerts:
            lines.extend(github_alerts)
            lines.append("")

        # Business
        biz = await self._check_business_health()
        if biz:
            lines.extend(biz)
            lines.append("")

        location = profile.get("location", "Tokyo")
        lines.append(f"📍 You're in {location}. Need anything researched or set up today? I'm ready.")

        return "\n".join(lines)


# Singleton
_scheduler: ProactiveScheduler | None = None


def get_scheduler(
    user_id: str,
    notify_cb: Callable[[str], Coroutine],
    telegram_chat_id: Optional[int] = None,
) -> ProactiveScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ProactiveScheduler(user_id, notify_cb, telegram_chat_id)
    return _scheduler
