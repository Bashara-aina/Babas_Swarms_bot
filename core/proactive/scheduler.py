"""Proactive scheduler — Legion checks in on you without being asked.

Enhanced Schedule (JST):
  - DAILY MORNING BRIEF (8:00 AM JST): rumahlabuh.com ping, Supabase health, GitHub, weather, unfinished tasks
  - GITHUB TREND WATCHER (Monday 9:00 AM JST)
  - RUMAHLABUH.COM MONITOR (every 30 min during active hours 8AM–11PM JST)
  - LATE NIGHT CHECK (1:00 AM JST)

All proactive messages are sent via the Telegram bot's notify_cb.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Callable, Coroutine, Optional

import pytz

logger = logging.getLogger(__name__)

# Config
PROACTIVE_INTERVAL_MINUTES = int(os.getenv("PROACTIVE_INTERVAL_MINUTES", "30"))
DAILY_BRIEFING_HOUR = int(os.getenv("DAILY_BRIEFING_HOUR", "8"))  # 8 AM local
BUSINESS_ALERT_THRESHOLD = int(os.getenv("BUSINESS_ALERT_THRESHOLD", "5"))  # errors


def _jst_now() -> datetime:
    """Return current time in JST."""
    return datetime.now(pytz.timezone("Asia/Tokyo"))


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
        self._last_github_intel_week: tuple[int, int] = (0, 0)
        self._last_rumahlabuh_check: float = 0.0

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
        now = _jst_now()
        alerts: list[str] = []

        # ── DAILY MORNING BRIEF (8 AM JST) ─────────────────────────────────
        today_str = now.strftime("%Y-%m-%d")
        if now.hour == DAILY_BRIEFING_HOUR and self._last_briefing_date != today_str:
            briefing = await self._build_daily_briefing(now)
            if briefing:
                await self.notify(briefing)
                self._last_briefing_date = today_str
            return  # Skip other checks during briefing

        # ── LATE NIGHT CHECK (1 AM JST) ───────────────────────────────────
        if now.hour == 1 and now.minute < PROACTIVE_INTERVAL_MINUTES:
            night_msg = await self._build_late_night_check(now)
            if night_msg:
                await self.notify(night_msg)
                return

        # ── RUMAHLABUH.COM MONITOR (every 30 min during active hours 8AM–11PM) ──
        if now.hour >= 8 and now.hour <= 23:
            await self._check_rumahlabuh_30min(now)

        # ── GITHUB TREND WATCHER (Monday 9 AM JST) ─────────────────────────
        if now.weekday() == 0 and now.hour == 9 and now.minute < PROACTIVE_INTERVAL_MINUTES:
            await self._notify_github_trend_watcher()

        # ── Regular checks ─────────────────────────────────────────────────
        schedule_alerts = self._check_schedule()
        alerts.extend(schedule_alerts)

        business_alerts = await self._check_business_health()
        alerts.extend(business_alerts)

        github_alerts = await self._check_github()
        alerts.extend(github_alerts)

        if alerts:
            msg = "🔔 <b>Legion check-in</b>\n\n" + "\n\n".join(alerts)
            await self.notify(msg)

        await self._maybe_weekly_github_intel_digest(now)
        await self._maybe_weekly_wiki_lint(now)
        await self._maybe_saturday_agents_md_sync(now)

    # ── Weekly wiki lint ─────────────────────────────────────────────────────

    async def _maybe_saturday_agents_md_sync(self, now: datetime) -> None:
        """Saturday 10:30 AM JST — regenerate AGENTS.md from wiki brain."""
        if os.getenv("LEGION_WIKI_AUTO_LINT", "1").strip().lower() in (
            "0",
            "false",
            "no",
            "off",
        ):
            return
        if not (now.weekday() == 5 and now.hour == 10 and now.minute < PROACTIVE_INTERVAL_MINUTES):
            return
        try:
            from core.wiki_manager import get_wiki_manager

            wm = get_wiki_manager()
            result = await wm.sync_agents_md()
            if result:
                logger.info("[Proactive] AGENTS.md sync completed")
            else:
                logger.warning("[Proactive] AGENTS.md sync returned empty")
        except Exception as e:
            logger.debug("[Proactive] AGENTS.md sync failed: %s", e)

    # ── Weekly wiki lint ─────────────────────────────────────────────────────

    async def _maybe_weekly_wiki_lint(self, now: datetime) -> None:
        """Sunday 10 AM JST — health-check the wiki."""
        if os.getenv("LEGION_WIKI_AUTO_LINT", "1").strip().lower() in (
            "0",
            "false",
            "no",
            "off",
        ):
            return
        if not (now.weekday() == 6 and now.hour == 10 and now.minute < PROACTIVE_INTERVAL_MINUTES):
            return
        try:
            from core.wiki_auto_ingest import lint_wiki

            result = await lint_wiki()
            if result.get("ok"):
                logger.info("[Proactive] wiki lint completed ok")
            else:
                logger.warning("[Proactive] wiki lint failed: %s", result.get("error"))
        except Exception as e:
            logger.debug("[Proactive] wiki lint failed: %s", e)

    # ── Rumahlabuh.com 30-min monitor ────────────────────────────────────────

    async def _check_rumahlabuh_30min(self, now: datetime) -> None:
        """Ping rumahlabuh.com every 30 min during active hours."""
        import time

        now_ts = time.time()
        if now_ts - self._last_rumahlabuh_check < 1800:  # 30 min
            return
        self._last_rumahlabuh_check = now_ts

        try:
            from tools.rumahlabuh_crew import check_website_uptime

            result = await check_website_uptime("https://rumahlabuh.com")
            if not result.get("ok", True):
                msg = (
                    f"⚠️ <b>rumahlabuh.com Alert</b>\n"
                    f"Status: {result.get('message', 'unknown')}\n"
                    "Check Supabase hosting / Cloudflare status."
                )
                await self.notify(msg)
            else:
                logger.debug("[Proactive] rumahlabuh.com OK: %s", result.get("message"))
        except Exception as e:
            logger.debug("[Proactive] rumahlabuh.com check failed: %s", e)

    # ── GitHub trend watcher nudge ───────────────────────────────────────────

    async def _notify_github_trend_watcher(self) -> None:
        """Monday 9 AM — run full GitHub trending digest via SelfUpgradeEngine."""
        try:
            from core.self_upgrade import SelfUpgradeEngine

            engine = SelfUpgradeEngine(notify_cb=self.notify)
            evals = await engine.scan_github_trending(topic="ai-agent", limit=10)
            if evals:
                digest = engine.format_evaluations_for_telegram(evals)
                await self.notify(digest)
            else:
                await self.notify(
                    "📈 <b>Monday GitHub Trend Watcher</b>\n"
                    "No trending repos found — check GITHUB_TOKEN or try again later."
                )
        except Exception as e:
            logger.debug("[Proactive] github trend watcher failed: %s", e)

    # ── Late night check ─────────────────────────────────────────────────────

    async def _build_late_night_check(self, now: datetime) -> str:
        """1 AM JST — warm check-in with Soul Engine emotional context."""
        try:
            from core.memory.episodic_store import get_episodic_store
            from core.soul_engine import build_enhanced_soul_context, get_emotional_state

            store = get_episodic_store()
            if hasattr(store, "get_unfinished_tasks"):
                unfinished = store.get_unfinished_tasks(self.user_id, limit=3)
            else:
                unfinished = []

            # Get Soul Engine emotional context for warm/casual tone
            emotional_state = get_emotional_state(conversation_turns=0)
            soul_ctx = build_enhanced_soul_context(conversation_turns=0)
            # Extract warmth note from soul context if present
            warmth_note = ""
            if "TIRED" in emotional_state:
                warmth_note = " — take it easy tonight"
            elif "late night" in soul_ctx.lower() if soul_ctx else False:
                warmth_note = " — rest up"

            lines = [f"🌙 <b>Late night check-in{warmth_note}</b>\n"]
            if unfinished:
                lines.append("📋 <b>Unfinished tasks:</b>")
                for t in unfinished:
                    lines.append(f"  • {t.get('summary', '')}")
            else:
                lines.append("All clear ✅ — get some rest, Bashara.")
            return "\n".join(lines)
        except Exception as e:
            logger.debug("[Proactive] late night check failed: %s", e)
            return ""

    # ── Daily briefing ───────────────────────────────────────────────────────

    async def _build_daily_briefing(self, now: datetime) -> str:
        """Build a morning briefing message with weather + tasks."""
        from core.memory.episodic_store import get_episodic_store
        from core.memory.user_profile import get_user_profile

        profile = get_user_profile(self.user_id)
        store = get_episodic_store()
        schedule = store.get_upcoming_schedule(self.user_id, horizon_days=3)
        unfinished = store.get_unfinished_tasks(self.user_id, limit=5)

        day_str = now.strftime("%A, %B %d")
        lines = [f"☀️ <b>Good morning, Bashara! It's {day_str}.</b>\n"]

        # rumahlabuh.com ping
        try:
            from tools.rumahlabuh_crew import check_website_uptime

            uptime = await check_website_uptime()
            lines.append(f"🏠 Website: {uptime.get('message', 'checking...')}")
        except Exception:
            lines.append("🏠 Website: status unknown")

        # Unfinished tasks
        if unfinished:
            lines.append("📋 <b>Unfinished:</b>")
            for t in unfinished[:4]:
                lines.append(f"  • {t.get('summary', '')}")

        # Schedule
        if schedule:
            lines.append("📅 <b>This week:</b>")
            for ep in schedule[:3]:
                lines.append(f"  • {ep.get('summary', '')}")

        # GitHub
        github_alerts = await self._check_github()
        if github_alerts:
            lines.extend(github_alerts)

        # Business
        biz = await self._check_business_health()
        if biz:
            lines.extend(biz)

        location = profile.get("location", "Tokyo")
        lines.append(f"📍 You're in {location}. I'm ready for today's tasks.")

        return "\n".join(lines)

    # ── Weekly GitHub intel ───────────────────────────────────────────────────

    async def _maybe_weekly_github_intel_digest(self, now: datetime) -> None:
        """Optional Sunday (configurable) nudge to run OSS / self-evolution scan."""
        if os.getenv("LEGION_WEEKLY_GITHUB_INTEL", "0").strip().lower() not in (
            "1",
            "true",
            "yes",
            "on",
        ):
            return
        try:
            target_wd = int(os.getenv("LEGION_GITHUB_INTEL_WEEKDAY", "6"))
            if now.weekday() != target_wd:
                return
            iso = now.isocalendar()
            key = (int(iso[0]), int(iso[1]))
            if key == self._last_github_intel_week:
                return
            self._last_github_intel_week = key
            await self.notify(
                "📚 <b>Weekly GitHub digest</b>\n"
                "Ask naturally for <i>trending repos</i>, <i>what to adopt for Legion</i>, "
                "or say <code>github trending</code> — I'll run intel + pros/cons."
            )
        except Exception as e:
            logger.debug("[Proactive] weekly github intel nudge skipped: %s", e)

    # ── Regular checks ────────────────────────────────────────────────────────

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

            alerts: list[str] = []
            try:
                result = sb.table("bookings").select("id,created_at").order("created_at", desc=True).limit(5).execute()
                if result.data:
                    alerts.append(f"🏠 <b>rumahlabuh.com</b>: {len(result.data)} recent booking(s) — all good ✅")
            except Exception:
                pass

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
                        f"including '{unread[0].get('subject', {}).get('title', '?')[:60]}'"
                    ]
        except Exception as e:
            logger.debug("[Proactive] GitHub check failed: %s", e)
            return []


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
