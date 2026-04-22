"""Enterprise handlers: /budget /routing_stats /security_stats /audit_summary.

NOTE: /budget is canonical in admin_handlers.py (comprehensive cost breakdown).
This file only contains /routing_stats, /security_stats, /audit_summary.
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import handlers.shared as _shared

from .shared import (
    is_allowed,
    send_chunked,
)

router = Router()


# ── /budget — Canonical handler is in admin_handlers.py ────────────────────────
# This file does NOT define /budget to avoid duplicate handler registration.
# The canonical admin_handlers.cmd_budget handles all /budget commands.


# ── /routing_stats — Cost router analytics ───────────────────────────────────
@router.message(Command("routing_stats"))
async def cmd_routing_stats(msg: Message) -> None:
    """Show cost-aware routing statistics."""
    if not is_allowed(msg):
        return

    lines = []

    if _shared._chief_of_staff:
        lines.append(_shared._chief_of_staff.format_stats_html())
        lines.append("")

    if _shared._cost_router:
        lines.append(_shared._cost_router.format_stats_html())
        lines.append("")

    if _shared._evaluator:
        lines.append(_shared._evaluator.format_scores_html())

    if not lines:
        await msg.answer("No routing stats available yet.")
        return

    await send_chunked(msg, "\n".join(lines))


# ── /security_stats — Security guard stats ───────────────────────────────────
@router.message(Command("security_stats"))
async def cmd_security_stats(msg: Message) -> None:
    """Show security guard statistics."""
    if not is_allowed(msg):
        return
    if not _shared._security_guard:
        await msg.answer("Security guard not initialized.")
        return

    stats = _shared._security_guard.get_stats()
    text = (
        "<b>Security Guard Stats</b>\n\n"
        f"Scanned: {stats['total_scanned']}\n"
        f"Blocked: {stats['total_blocked']}\n"
        f"Block rate: {stats['block_rate']*100:.1f}%"
    )
    await msg.answer(text, parse_mode="HTML")



