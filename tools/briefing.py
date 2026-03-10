"""briefing.py — Morning briefing assembler for Legion.

Aggregates: GitHub PRs, training status, tech news (RSS),
GPU/system stats, weather, calendar.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def _fetch_rss(url: str, max_items: int = 3) -> list[dict[str, str]]:
    """Fetch and parse an RSS feed. Returns list of {title, link, published}."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                text = await resp.text()

        root = ET.fromstring(text)
        items = []

        # Standard RSS 2.0
        for item in root.findall(".//item")[:max_items]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "")[:25].strip()
            items.append({"title": title, "link": link, "published": pub})

        # Atom feed fallback
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:max_items]:
                title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                pub = (entry.findtext("atom:published", namespaces=ns) or "")[:25]
                items.append({"title": title, "link": link, "published": pub})

        return items
    except Exception as e:
        logger.warning("RSS fetch failed for %s: %s", url, e)
        return []


async def _get_github_prs() -> str:
    """Get GitHub PRs via gh CLI."""
    try:
        proc = await asyncio.create_subprocess_shell(
            "gh pr list --author @me --json title,url,state --limit 5 2>/dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode().strip()
        if not output or output == "[]":
            return "No open PRs by you."

        import json
        prs = json.loads(output)
        lines = []
        for pr in prs:
            state = "🟢" if pr.get("state") == "OPEN" else "🟣"
            lines.append(f"  {state} {pr.get('title', '?')}")
        return "\n".join(lines) if lines else "No PRs found."
    except Exception as e:
        return f"(GitHub CLI not available: {e})"


async def _get_review_prs() -> str:
    """Get PRs requesting your review."""
    try:
        proc = await asyncio.create_subprocess_shell(
            "gh pr list --search 'review-requested:@me' --json title,url --limit 5 2>/dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode().strip()
        if not output or output == "[]":
            return "No reviews requested."

        import json
        prs = json.loads(output)
        lines = [f"  📝 {pr.get('title', '?')}" for pr in prs]
        return "\n".join(lines) if lines else "None."
    except Exception:
        return "(unavailable)"


async def _get_training_status() -> str:
    """Read latest training log metrics."""
    log_path = os.getenv("WORKERNET_LOG_PATH", "")
    if not log_path:
        # Try common locations
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
        return "No training log found. Set WORKERNET_LOG_PATH in .env"

    try:
        proc = await asyncio.create_subprocess_shell(
            f"tail -20 '{log_path}' 2>/dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        output = stdout.decode().strip()
        if output:
            # Get last few meaningful lines
            lines = [l for l in output.split("\n") if l.strip()]
            return "\n".join(lines[-5:])
        return "Log file empty or unreadable."
    except Exception as e:
        return f"Error reading log: {e}"


async def _get_system_stats() -> str:
    """Quick GPU/system snapshot."""
    try:
        proc = await asyncio.create_subprocess_shell(
            "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu "
            "--format=csv,noheader,nounits 2>/dev/null || echo 'No GPU'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        gpu = stdout.decode().strip()

        proc2 = await asyncio.create_subprocess_shell(
            "free -h | grep Mem | awk '{print $3\"/\"$2}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout2, _ = await asyncio.wait_for(proc2.communicate(), timeout=5)
        mem = stdout2.decode().strip()

        return f"  GPU: {gpu}\n  RAM: {mem}"
    except Exception:
        return "(stats unavailable)"


async def _get_weather() -> str:
    """Get weather from wttr.in."""
    city = os.getenv("CITY_FOR_WEATHER", "Jakarta")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://wttr.in/{city}?format=3",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                return (await resp.text()).strip()
    except Exception:
        return f"(weather unavailable for {city})"


async def generate_briefing() -> str:
    """Assemble the full morning briefing."""
    now = datetime.now()
    greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"

    # Fetch everything in parallel
    (
        github_prs,
        review_prs,
        training,
        system,
        weather,
        hn_news,
        arxiv_news,
    ) = await asyncio.gather(
        _get_github_prs(),
        _get_review_prs(),
        _get_training_status(),
        _get_system_stats(),
        _get_weather(),
        _fetch_rss("https://hnrss.org/frontpage", max_items=3),
        _fetch_rss("https://arxiv.org/rss/cs.CV", max_items=3),
    )

    # Format news
    hn_lines = []
    for item in hn_news:
        hn_lines.append(f"  - {item['title'][:80]}")
    hn_text = "\n".join(hn_lines) if hn_lines else "  (unavailable)"

    arxiv_lines = []
    for item in arxiv_news:
        arxiv_lines.append(f"  - {item['title'][:80]}")
    arxiv_text = "\n".join(arxiv_lines) if arxiv_lines else "  (unavailable)"

    briefing = (
        f"<b>{'☀️' if now.hour < 17 else '🌙'} {greeting}, Bas!</b>\n"
        f"📅 {now.strftime('%A, %B %d %Y')} — {now.strftime('%H:%M')}\n\n"

        f"<b>🌤 Weather</b>\n  {weather}\n\n"

        f"<b>💻 System</b>\n{system}\n\n"

        f"<b>📦 Your PRs</b>\n{github_prs}\n\n"
        f"<b>📝 Reviews Requested</b>\n{review_prs}\n\n"

        f"<b>🧠 Training Status</b>\n<pre>{training}</pre>\n\n"

        f"<b>📰 Hacker News</b>\n{hn_text}\n\n"

        f"<b>📚 arXiv CS.CV</b>\n{arxiv_text}\n\n"

        "<i>Use /paper to dive into any paper, /stats for full system info</i>"
    )

    return briefing


async def schedule_daily_briefing(bot, user_id: int, hour: int = 7, minute: int = 30) -> None:
    """Background task: send briefing at specified time daily."""
    while True:
        now = datetime.now()
        # Calculate seconds until next target time
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= target:
            # Already past today's time, schedule for tomorrow
            target = target.replace(day=target.day + 1)
        try:
            # Handle month rollover
            import calendar
            days_in_month = calendar.monthrange(target.year, target.month)[1]
            if target.day > days_in_month:
                if target.month == 12:
                    target = target.replace(year=target.year + 1, month=1, day=1)
                else:
                    target = target.replace(month=target.month + 1, day=1)
        except Exception:
            pass

        delay = (target - now).total_seconds()
        logger.info("Next briefing in %.0f seconds (at %s)", delay, target.strftime("%H:%M"))

        await asyncio.sleep(delay)

        try:
            briefing = await generate_briefing()
            # Chunk if needed
            from llm_client import chunk_output
            for chunk in chunk_output(briefing):
                try:
                    await bot.send_message(user_id, chunk, parse_mode="HTML")
                except Exception:
                    await bot.send_message(user_id, chunk)
            logger.info("Daily briefing sent")
        except Exception as e:
            logger.error("Briefing failed: %s", e)

        # Sleep until next day (with buffer)
        await asyncio.sleep(60)  # Prevent double-send
