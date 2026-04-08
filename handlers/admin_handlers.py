"""handlers/admin_handlers.py — Admin commands for Legion: /budget, /soul.

P2-3: /budget — Cost tracking dashboard
P2-4: /soul — Show current SOUL.md contents
"""
from __future__ import annotations

import html
import logging
import os
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()

ALLOWED_USER_ID: int = int((os.getenv("ALLOWED_USER_ID") or os.getenv("BASHARA_TELEGRAM_ID") or "0").strip().split(",")[0])


async def _require_owner(message: Message) -> bool:
    """Return True if allowed; send rejection and return False otherwise."""
    try:
        from handlers.shared import ALLOWED_USER_ID as _uid  # type: ignore[attr-defined]
        allowed = _uid
    except Exception:
        allowed = ALLOWED_USER_ID
    if message.from_user and message.from_user.id == allowed:
        return True
    await message.answer("<b>Unauthorized.</b>", parse_mode="HTML")
    return False


async def _split_and_send(message: Message, text: str) -> None:
    """Send text chunked at 4000 chars."""
    try:
        from handlers.shared import split_and_send  # type: ignore[attr-defined]
        await split_and_send(message, text)
        return
    except Exception:
        pass
    chunk_size = 4000
    for i in range(0, len(text), chunk_size):
        await message.answer(text[i : i + chunk_size], parse_mode="HTML")


@router.message(Command("budget"))
async def cmd_budget(message: Message) -> None:
    """Show cost tracking dashboard — current API spend vs. MAX_PROACTIVE_PER_DAY."""
    if not await _require_owner(message):
        return

    try:
        # Try to get budget manager from swarms_bot
        try:
            from handlers.shared import _budget_manager  # type: ignore[attr-defined]
            budget = _budget_manager
        except Exception:
            from swarms_bot.routing.budget_manager import BudgetManager  # type: ignore[import]
            budget = BudgetManager()

        # Get budget stats
        stats = budget.get_stats()  # type: ignore[attr-defined]
        
        daily_limit = float(os.getenv("BUDGET_DAILY_LIMIT_USD", "2.00"))
        spent = stats.get("total_spent_today", 0.0)
        remaining = daily_limit - spent
        pct = (spent / daily_limit * 100) if daily_limit > 0 else 0

        # Format response
        lines = [
            "<b>💰 Budget Dashboard</b>\n",
            f"<b>Daily Limit:</b> ${daily_limit:.2f}",
            f"<b>Spent Today:</b> ${spent:.4f} ({pct:.1f}%)",
            f"<b>Remaining:</b> ${remaining:.4f}\n",
        ]

        # Task breakdown
        if "tasks" in stats:
            lines.append("<b>Breakdown by Task:</b>")
            for task, amount in stats["tasks"].items():
                lines.append(f"  • {task}: ${amount:.4f}")

        response = "\n".join(lines)
        await message.answer(response, parse_mode="HTML")

    except Exception as exc:
        logger.exception("Budget command error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        await message.answer(
            f"<b>Budget error:</b> <code>{safe_err}</code>\n\n"
            "<i>This command requires swarms_bot.routing.budget_manager to be initialized.</i>",
            parse_mode="HTML",
        )


@router.message(Command("soul"))
async def cmd_soul(message: Message) -> None:
    """Show the current contents of SOUL.md — Legion's living identity."""
    if not await _require_owner(message):
        return

    soul_path = Path("SOUL.md")
    if not soul_path.exists():
        await message.answer(
            "<b>SOUL.md not found.</b>\n"
            "<i>Legion's identity file should be at the repository root.</i>",
            parse_mode="HTML",
        )
        return

    try:
        content = soul_path.read_text(encoding="utf-8")
        
        # Add header
        response = (
            "<b>🧠 SOUL.md — Legion's Living Identity</b>\n"
            f"<i>Last modified: {soul_path.stat().st_mtime}</i>\n\n"
            f"<pre>{html.escape(content)}</pre>"
        )

        await _split_and_send(message, response)

    except Exception as exc:
        logger.exception("Soul command error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        await message.answer(
            f"<b>Soul read error:</b> <code>{safe_err}</code>",
            parse_mode="HTML",
        )
