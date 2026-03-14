"""Enterprise handlers: /budget /routing_stats /security_stats /audit_summary."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    is_allowed,
    send_chunked,
)
import handlers.shared as _shared

router = Router()


# ── /budget — Cost tracking dashboard ────────────────────────────────────────
@router.message(Command("budget"))
async def cmd_budget(msg: Message) -> None:
    """Show cost tracking and budget status."""
    if not is_allowed(msg):
        return
    if not _shared._budget_manager:
        await msg.answer("Budget manager not initialized.")
        return
    text = _shared._budget_manager.format_budget_html()
    await msg.answer(text, parse_mode="HTML")


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


# ── /audit_summary — Audit log summary ───────────────────────────────────────
@router.message(Command("audit_summary"))
async def cmd_audit_summary(msg: Message) -> None:
    """Show audit log summary for the last 24 hours."""
    if not is_allowed(msg):
        return
    if not _shared._audit_logger:
        await msg.answer("Audit logger not initialized.")
        return

    summary = await _shared._audit_logger.get_summary(hours=24)
    lines = [
        "<b>Audit Summary (24h)</b>\n",
        f"Events: {summary['total_events']}",
        f"Success: {summary['success_count']} | "
        f"Failures: {summary['failure_count']}",
        f"Cost: ${summary['total_cost_usd']:.4f}",
    ]

    if summary["by_agent"]:
        lines.append("\n<b>By agent:</b>")
        for agent, count in sorted(summary["by_agent"].items(),
                                     key=lambda x: x[1], reverse=True):
            lines.append(f"  <code>{agent}</code>: {count}")

    if summary["by_action"]:
        lines.append("\n<b>By action:</b>")
        for action, count in summary["by_action"].items():
            lines.append(f"  {action}: {count}")

    await msg.answer("\n".join(lines), parse_mode="HTML")
