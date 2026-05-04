"""
lib/legiona/scheduler.py
APScheduler-powered autonomous maintenance.
Runs inside the aiogram bot process — no separate worker needed.

Schedule:
  Every Sunday  09:00 JST → self-evolution (evolve)
  Every Friday  18:00 JST → hallucination eval + notify Telegram
  1st of month  02:00 JST → rule deduplication
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from lib.legiona.observability.cost_log import today_total_jpy
from lib.legiona.self_evolve import evolve

# JST = UTC+9
JST_OFFSET = 9


def jst_to_utc(hour: int) -> int:
    return (hour - JST_OFFSET) % 24


TELEGRAM_NOTIFY_CHAT_ID_STR = os.getenv("LEGIONA_NOTIFY_CHAT_ID", "0")
TELEGRAM_NOTIFY_CHAT_ID = int(TELEGRAM_NOTIFY_CHAT_ID_STR) if TELEGRAM_NOTIFY_CHAT_ID_STR.isdigit() else 0


async def _weekly_evolve(bot=None):
    """Sunday 9AM JST: run self-evolution, notify owner."""
    new_rule = evolve(last_n=10)
    if bot and TELEGRAM_NOTIFY_CHAT_ID:
        msg = f"🔁 **Weekly Evolution Complete**\n\nNew rule:\n`{new_rule or 'No change'}`"
        await bot.send_message(TELEGRAM_NOTIFY_CHAT_ID, msg, parse_mode="Markdown")


async def _friday_eval(bot=None):
    """Friday 6PM JST: run hallucination eval, notify owner."""
    repo_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "lib/legiona/eval/hallucination_eval.py"],
        capture_output=True, text=True, timeout=120, cwd=repo_root,
    )
    cost = today_total_jpy()
    if bot and TELEGRAM_NOTIFY_CHAT_ID:
        summary = result.stdout[-800:] if result.stdout else "No output"
        await bot.send_message(
            TELEGRAM_NOTIFY_CHAT_ID,
            f"📊 **Friday Eval Complete**\n\nToday cost: ¥{cost:.2f}\n\n```\n{summary}\n```",
            parse_mode="Markdown",
        )


async def _monthly_dedup(bot=None):
    """1st of month 2AM JST: deduplicate evolved rules."""
    from lib.legiona.self_evolve import RULES_FILE
    if not RULES_FILE.exists():
        return
    rules = RULES_FILE.read_text()
    from lib.legiona.minimax_client import LegionaOutput, complete
    result = complete([
        {"role": "system", "content": "You are a rules editor. Deduplicate and clarify."},
        {"role": "user", "content": (
            "Clean these rules — remove duplicates, resolve contradictions, "
            f"keep the best version of each:\n\n{rules}"
        )},
    ], preset="research", response_model=LegionaOutput)
    RULES_FILE.write_text(result.answer)
    if bot and TELEGRAM_NOTIFY_CHAT_ID:
        await bot.send_message(
            TELEGRAM_NOTIFY_CHAT_ID,
            "🧹 **Monthly Dedup Complete** — rules cleaned",
            parse_mode="Markdown",
        )


# ── Market Intelligence ────────────────────────────────────────────────────────

async def _morning_market_brief(bot=None):
    """06:30 WIB — before IDX opens at 9:00 AM. Full overnight report."""
    from tools.market_intel import market_overnight_report
    try:
        report = await market_overnight_report()
    except Exception as exc:
        report = f"❌ Morning brief failed: {exc}"
    if bot and TELEGRAM_NOTIFY_CHAT_ID:
        if len(report) > 4096:
            report = report[:4090] + "\n...(truncated)"
        await bot.send_message(TELEGRAM_NOTIFY_CHAT_ID, report, parse_mode="Markdown")


async def _afternoon_market_brief(bot=None):
    """16:30 WIB — after IDX closes at 15:30. Quick IDX summary."""
    from tools.market_intel import DEFAULT_TICKERS, market_brief
    try:
        report = await market_brief(DEFAULT_TICKERS["IDX"], mode="standard")
    except Exception as exc:
        report = f"❌ Afternoon brief failed: {exc}"
    if bot and TELEGRAM_NOTIFY_CHAT_ID:
        if len(report) > 4096:
            report = report[:4090] + "\n...(truncated)"
        await bot.send_message(TELEGRAM_NOTIFY_CHAT_ID, report, parse_mode="Markdown")


def start_scheduler(bot=None) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        lambda: asyncio.create_task(_weekly_evolve(bot)),
        CronTrigger(day_of_week="sun", hour=jst_to_utc(9), minute=0),
        id="weekly_evolve",
    )
    scheduler.add_job(
        lambda: asyncio.create_task(_friday_eval(bot)),
        CronTrigger(day_of_week="fri", hour=jst_to_utc(18), minute=0),
        id="friday_eval",
    )
    scheduler.add_job(
        lambda: asyncio.create_task(_monthly_dedup(bot)),
        CronTrigger(day=1, hour=jst_to_utc(2), minute=0),
        id="monthly_dedup",
    )
    scheduler.add_job(
        lambda: asyncio.create_task(_morning_market_brief(bot)),
        CronTrigger(hour=6, minute=30, timezone="Asia/Jakarta"),
        id="morning_market_brief",
    )
    scheduler.add_job(
        lambda: asyncio.create_task(_afternoon_market_brief(bot)),
        CronTrigger(hour=16, minute=30, timezone="Asia/Jakarta"),
        id="afternoon_market_brief",
    )
    scheduler.start()
    return scheduler
