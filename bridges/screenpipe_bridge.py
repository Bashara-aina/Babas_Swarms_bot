"""
Proactive Screenpipe monitor — offers help when repeated errors appear on screen.

Uses wiki_raw_completion (no recursive chat). Telegram user from startup chat_id.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from aiogram import Bot

logger = logging.getLogger(__name__)


class ScreenpipeBridge:
    def __init__(self, bot: Bot, chat_id: int) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self._last_proactive_ts = 0.0
        self._interval_sec = int(os.getenv("SCREENPIPE_MONITOR_INTERVAL_SEC", "300"))
        self._cooldown_sec = int(os.getenv("SCREENPIPE_PROACTIVE_COOLDOWN_SEC", "1800"))

    async def monitor_loop(self) -> None:
        while True:
            await asyncio.sleep(max(60, self._interval_sec))
            try:
                await self._check_stuck_on_error()
            except Exception as exc:
                logger.error("Screenpipe monitor error: %s", exc)

    async def _check_stuck_on_error(self) -> None:
        if time.time() - self._last_proactive_ts < self._cooldown_sec:
            return

        from tools.screenpipe_tool import get_screenpipe_tool

        sp = get_screenpipe_tool()
        if not sp.is_configured():
            return

        recent = await sp.search(
            "error traceback exception failed",
            limit=5,
            hours_back=1,
        )
        if not recent or len(recent) < 80:
            return

        from llm_client import wiki_raw_completion

        assessment = await wiki_raw_completion(
            f"""Bashara's recent screen/audio context from Screenpipe:

{recent[:3500]}

Is Bashara likely stuck on the same error or repeating failures?
Reply with exactly YES or NO.""",
            model=os.getenv("SCREENPIPE_ASSESS_MODEL", "opencode-go/minimax-m3"),
            max_tokens=8,
        )
        if "YES" not in (assessment or "").upper():
            return

        message = await wiki_raw_completion(
            f"""Bashara may be stuck on an error. Context:
{recent[:1200]}

Write ONE short Telegram message as Legion — casual Indonesian-English mix, friendly, not preachy.
Max 2 sentences. Offer specific help. No markdown.""",
            model=os.getenv("SCREENPIPE_MESSAGE_MODEL", "opencode-go/minimax-m3"),
            max_tokens=120,
        )
        if not (message or "").strip():
            return

        try:
            await self.bot.send_message(
                self.chat_id,
                f"👁 {message.strip()}"[:4000],
            )
            self._last_proactive_ts = time.time()
            logger.info("Screenpipe proactive message sent")
        except Exception as exc:
            logger.warning("Screenpipe proactive send failed: %s", exc)
