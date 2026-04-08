"""
Weekly wiki lint (e.g. n8n cron Sunday 09:00 JST).
Writes wiki/LINT_REPORT.md and optionally notifies Telegram.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Repo root on path for `core` / `llm_client`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

logger = logging.getLogger(__name__)


async def run_lint() -> str:
    from core.wiki_manager import get_wiki_manager

    wm = get_wiki_manager()
    return await wm.lint()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    report = await run_lint()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    uid_raw = os.getenv("ALLOWED_USER_ID", "").strip()
    if not token or not uid_raw:
        logger.info("Skipping Telegram send (TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID missing).")
        print(report[:2000])
        return

    from aiogram import Bot

    chat_id = int(uid_raw)
    bot = Bot(token=token)
    try:
        summary = report[:3500]
        if len(report) > 3500:
            summary += "\n\n(Full report: wiki/LINT_REPORT.md)"
        await bot.send_message(
            chat_id,
            f"Weekly Wiki Lint\n\n{summary}",
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
