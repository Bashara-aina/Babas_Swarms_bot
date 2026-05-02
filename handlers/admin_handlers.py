"""handlers/admin_handlers.py — Admin commands for Legion: /budget, /soul, /capabilities, /self_report.

P2-3: /budget — Cost tracking dashboard
P2-4: /soul — Show current SOUL.md contents
P9: /capabilities — Honest capability status (✅ ⚠️ ❌)
P9: /self_report — 24h activity report
"""

from __future__ import annotations

import html
import logging
import os
from datetime import datetime
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import handlers.shared as _shared
from handlers.shared import is_allowed

logger = logging.getLogger(__name__)
router = Router()


async def _split_and_send(message: Message, text: str) -> None:
    """Send text chunked at 4000 chars."""
    try:
        from handlers.shared import send_chunked

        await send_chunked(message, text)
        return
    except Exception:
        pass
    chunk_size = 4000
    for i in range(0, len(text), chunk_size):
        await message.answer(text[i : i + chunk_size], parse_mode="HTML")


@router.message(Command("budget"))
async def cmd_budget(message: Message) -> None:
    """Show cost tracking dashboard — current API spend vs. MAX_PROACTIVE_PER_DAY."""
    if not is_allowed(message):
        await message.answer("<b>Unauthorized.</b>", parse_mode="HTML")
        return

    if not _shared._budget_manager:
        await message.answer("<b>Budget manager not initialized.</b>", parse_mode="HTML")
        return

    try:
        budget_status = _shared._budget_manager.check_budget()
        day_breakdown = _shared._budget_manager.get_cost_breakdown("day")
        proactive_cap = int(os.getenv("MAX_PROACTIVE_PER_DAY", "3"))

        daily_spent = float(budget_status.get("daily_spent", 0.0))
        daily_limit = float(budget_status.get("daily_limit", 0.0))
        daily_pct = (daily_spent / daily_limit * 100.0) if daily_limit > 0 else 0.0

        lines = [
            "<b>💰 Budget Dashboard</b>",
            f"<b>Daily:</b> ${daily_spent:.4f} / ${daily_limit:.2f} ({daily_pct:.1f}%)",
            f"<b>Daily remaining:</b> ${float(budget_status.get('daily_remaining', 0.0)):.4f}",
            f"<b>Monthly:</b> ${float(budget_status.get('monthly_spent', 0.0)):.4f} / "
            f"${float(budget_status.get('monthly_limit', 0.0)):.2f}",
            f"<b>Proactive cap (MAX_PROACTIVE_PER_DAY):</b> {proactive_cap}",
            f"<b>Requests today:</b> {int(day_breakdown.get('total_requests', 0))}",
            f"<b>Tokens today:</b> {int(day_breakdown.get('total_tokens', 0)):,}",
        ]

        by_task = day_breakdown.get("by_task_type", {}) or {}
        if by_task:
            lines.append("\n<b>By task type:</b>")
            for task_type, amount in list(by_task.items())[:8]:
                safe_task = html.escape(str(task_type or "unspecified"))
                lines.append(f"• <code>{safe_task}</code>: ${float(amount):.4f}")

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Refresh", callback_data="budget:refresh"),
                    InlineKeyboardButton(text="📊 Details", callback_data="budget:details"),
                ],
                [
                    InlineKeyboardButton(text="💰 Full Report", callback_data="cmd:budget"),
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                ],
            ]
        )
        await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=kb)
    except Exception as exc:
        logger.exception("Budget command error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        await message.answer(
            f"<b>Budget error:</b> <code>{safe_err}</code>\n\n"
            "<i>Budget manager returned an unexpected state.</i>",
            parse_mode="HTML",
        )


@router.message(Command("soul"))
async def cmd_soul(message: Message) -> None:
    """Show the current contents of SOUL.md — Legion's living identity."""
    if not is_allowed(message):
        await message.answer("<b>Unauthorized.</b>", parse_mode="HTML")
        return

    soul_path = Path("SOUL.md")
    if not soul_path.exists():
        await message.answer(
            "<b>SOUL.md not found.</b>\n<i>Legion's identity file should be at the repository root.</i>",
            parse_mode="HTML",
        )
        return

    try:
        content = soul_path.read_text(encoding="utf-8")
        modified_iso = datetime.fromtimestamp(soul_path.stat().st_mtime).isoformat(timespec="seconds")
        await message.answer(
            "<b>🧠 SOUL.md — Legion's Living Identity</b>\n"
            f"<i>Last modified: {html.escape(modified_iso)}</i>",
            parse_mode="HTML",
        )
        chunk_size = 3500
        for i in range(0, len(content), chunk_size):
            await message.answer(f"<pre>{html.escape(content[i:i + chunk_size])}</pre>", parse_mode="HTML")

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🧠 Edit SOUL", callback_data="soul:edit"),
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                ],
            ]
        )
        await message.answer("Use /soul to reload or tap Home to return.", parse_mode="HTML", reply_markup=kb)

    except Exception as exc:
        logger.exception("Soul read error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        await message.answer(
            f"<b>Soul read error:</b> <code>{safe_err}</code>",
            parse_mode="HTML",
        )


@router.message(Command("capabilities"))
async def cmd_capabilities(message: Message) -> None:
    """Returns honest list of what works vs what's partial vs what's stub."""
    if not is_allowed(message):
        await message.answer("<b>Unauthorized.</b>", parse_mode="HTML")
        return

    try:
        from core.capability_audit import CapabilityAudit

        audit = CapabilityAudit()
        result = await audit.run_audit()
        present = result.get("present", [])
        missing = result.get("missing", [])

        lines = ["<b>Legion Capabilities — Honest Status</b>"]

        if present:
            lines.append("\n✅ <b>Working</b>")
            for cap, _path in present:
                lines.append(f"• ✅ {html.escape(str(cap))}")

        if missing:
            lines.append("\n⚠️ <b>Missing / Not Ready</b>")
            for cap, _path in missing:
                lines.append(f"• ❌ {html.escape(str(cap))} (not ready)")

        coverage = result.get("coverage_pct", 0)
        lines.append(f"\n📊 Coverage: {coverage}% ({len(present)}/{len(present) + len(missing)})")

        await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as exc:
        logger.exception("Capabilities command error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        await message.answer(
            f"<b>Capabilities error:</b> <code>{safe_err}</code>",
            parse_mode="HTML",
        )


@router.message(Command("self_report"))
async def cmd_self_report(message: Message) -> None:
    """24h activity report — what Legion did, failed at, learned."""
    if not is_allowed(message):
        await message.answer("<b>Unauthorized.</b>", parse_mode="HTML")
        return

    try:
        from data.message_count import load_message_count
        from data.self_improvement_buffer import get_recent_learnings

        count = load_message_count()
        learnings = await get_recent_learnings(n=10)

        # Format learnings
        if learnings:
            learn_lines = []
            for idx, learn in enumerate(learnings, 1):
                learn_lines.append(f"  {idx}. {learn}")
            learn_text = "\n".join(learn_lines)
        else:
            learn_text = "  (none yet)"

        report = (
            "<b>Legion — 24h Self Report</b>\n\n"
            f"📨 Messages processed: {count}\n\n"
            "🧠 Recent learnings:\n"
            f"{html.escape(learn_text)}\n\n"
            "<i>Run /capabilities for full capability status.</i>"
        )

        await message.answer(report, parse_mode="HTML")

    except Exception as exc:
        logger.exception("Self report command error: %s", exc)
        safe_err = html.escape(str(exc)[:200])
        await message.answer(
            f"<b>Self report error:</b> <code>{safe_err}</code>",
            parse_mode="HTML",
        )
