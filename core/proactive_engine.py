"""Proactive Engine — Legion monitors and initiates messages autonomously.

These are NOT responses to user messages. Legion sends these unprompted
when it detects something worth mentioning.

All checks are non-fatal. Failure = silent, never crashes bot.
All messages respect do_not_disturb hours (1-7 AM JST).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))
DO_NOT_DISTURB_START = 1
DO_NOT_DISTURB_END = 7

_last_github_check: float = 0.0
_last_site_check: float = 0.0
_last_thesis_nudge: float = 0.0
_last_late_night_warning: float = 0.0
_known_git_shas: dict[str, str] = {}
_site_was_down: set[str] = set()
_send_message_fn: Callable[[str], Awaitable[None]] | None = None


def register_sender(fn: Callable[[str], Awaitable[None]]) -> None:
    global _send_message_fn
    _send_message_fn = fn


def _is_do_not_disturb() -> bool:
    now = datetime.now(JST)
    return DO_NOT_DISTURB_START <= now.hour < DO_NOT_DISTURB_END


from core.utils.datetime_utils import jst_now as _jst_now  # noqa: E402


async def _send(text: str) -> None:
    if _send_message_fn and not _is_do_not_disturb():
        try:
            await _send_message_fn(text)
        except Exception as e:
            logger.warning("Proactive send failed: %s", e)


async def check_late_night() -> None:
    global _last_late_night_warning
    now = _jst_now()
    if 1 <= now.hour < 3 and time.time() - _last_late_night_warning > 3600 * 20:
        _last_late_night_warning = time.time()
        await _send(
            f"⏰ yo it's {now.strftime('%H:%M')} JST. "
            f"you're still up. thesis won't write itself but "
            f"neither will a sleep-deprived brain. your call."
        )


async def check_site_health() -> None:
    global _last_site_check, _site_was_down
    if time.time() - _last_site_check < 300:
        return
    _last_site_check = time.time()

    sites = {
        "rumahlabuh.com": "https://rumahlabuh.com",
        # "cekwajar.id": "https://cekwajar.id",  # Not deployed yet
    }
    try:
        from tools.rumahlabuh_http import get_resilient_session

        async with get_resilient_session() as session:
            for name, url in sites.items():
                try:
                    async with session.get(url) as resp:
                        if resp.status >= 500:
                            if name not in _site_was_down:
                                _site_was_down.add(name)
                                await _send(
                                    f"🚨 **{name} is DOWN** — HTTP {resp.status}\n"
                                    f"URL: {url}\nTime: {_jst_now().strftime('%H:%M JST')}"
                                )
                        else:
                            if name in _site_was_down:
                                _site_was_down.discard(name)
                                await _send(f"✅ **{name} is back up** — {resp.status}")
                except Exception as e:
                    if name not in _site_was_down:
                        _site_was_down.add(name)
                        await _send(f"🚨 **{name} unreachable** — {e}")
    except ImportError:
        pass


async def check_github_releases() -> None:
    global _last_github_check, _known_git_shas
    if time.time() - _last_github_check < 3600 * 6:
        return
    _last_github_check = time.time()

    watched_repos = [
        "opencode-ai/opencode",
        "letta-ai/letta",
        "mem0ai/mem0",
        "e2b-dev/E2B",
        "browser-use/browser-use",
        "Significant-Gravitas/AutoGPT",
        "aitomatic/openssa",
    ]
    try:
        import aiohttp

        headers = {}
        gh_token = os.getenv("GITHUB_TOKEN", "")
        if gh_token:
            headers["Authorization"] = f"token {gh_token}"

        async with aiohttp.ClientSession(headers=headers) as session:
            for repo in watched_repos:
                try:
                    url = f"https://api.github.com/repos/{repo}/releases/latest"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        tag = data.get("tag_name", "")
                        name = data.get("name", tag)
                        published = data.get("published_at", "")[:10]
                        html_url = data.get("html_url", "")
                        body = (data.get("body", "") or "")[:300]

                        prev_tag = _known_git_shas.get(repo)
                        if prev_tag and prev_tag != tag:
                            await _send(f"📦 **{repo}** released **{name}** ({published})\n{body[:200]}...\n{html_url}")
                        _known_git_shas[repo] = tag
                except Exception:
                    pass
    except ImportError:
        pass


async def check_system_health() -> None:
    try:
        import psutil

        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        ram_pct = ram.percent
        disk_pct = disk.percent

        alerts = []
        if ram_pct > 85:
            alerts.append(f"🔴 RAM critical: {ram.used / 1e9:.1f}GB used ({ram_pct:.0f}%)")
        if disk_pct > 90:
            alerts.append(f"🔴 Disk critical: {disk_pct:.0f}% used")

        try:
            import subprocess

            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                if len(parts) >= 3:
                    temp, _vram_used, _vram_total = parts
                    if int(temp) > 83:
                        alerts.append(f"🔴 GPU temp: {temp}°C")
        except Exception:
            pass

        if alerts:
            await _send("⚠️ **System Alert**\n" + "\n".join(alerts))
    except ImportError:
        pass


async def check_thesis_deadline() -> None:
    global _last_thesis_nudge
    if time.time() - _last_thesis_nudge < 3600 * 24:
        return

    now = _jst_now()
    if not (now.weekday() < 5 and 9 <= now.hour < 10):
        return

    deadline = datetime(2026, 7, 1, tzinfo=JST)
    days_left = (deadline - now).days
    if days_left < 0:
        return

    try:
        import subprocess

        result = subprocess.run(
            ["git", "-C", os.path.expanduser("~/swarm-bot"), "log", "--oneline", "-1", "--format=%ar"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        last_push = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        last_push = "unknown"

    _last_thesis_nudge = time.time()
    if days_left < 30:
        urgency = "🚨 CRITICAL"
    elif days_left < 60:
        urgency = "⚠️ Urgent"
    else:
        urgency = "📅 FYI"

    await _send(
        f"{urgency} Thesis deadline: **{days_left} days** left (July 2026)\n"
        f"Last Legion commit: {last_push}\n"
        f"Morning check-in — what are you working on today?"
    )


async def run_proactive_loop() -> None:
    logger.info("🔮 Proactive engine started")
    while True:
        try:
            await asyncio.gather(
                check_late_night(),
                check_site_health(),
                check_system_health(),
                return_exceptions=True,
            )
            now_min = int(time.time() / 60)
            if now_min % 360 == 0:
                await check_github_releases()
            if now_min % 1440 == 0:
                await check_thesis_deadline()
        except Exception as e:
            logger.warning("Proactive loop error: %s", e)
        await asyncio.sleep(60)
