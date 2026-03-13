"""WAJAR_WATCH — telegram_alerter: send Telegram alerts with inline buttons."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

if TYPE_CHECKING:
    from aiogram import Bot

    from tools.wajar_watch.confidence_scorer import ConfidenceResult
    from tools.wajar_watch.constants import WatchedConstant
    from tools.wajar_watch.github_pr_writer import PRResult

logger = logging.getLogger(__name__)


async def send_auto_applied_alert(
    bot: "Bot",
    chat_id: int,
    watched: "WatchedConstant",
    result: "ConfidenceResult",
    pr: "PRResult",
) -> None:
    """TYPE 1: Auto-applied — info only, no buttons needed."""
    text = (
        f"✅ <b>WAJAR_WATCH — Auto-Applied</b>\n\n"
        f"📋 <code>{watched.key}</code>\n"
        f"💰 {watched.current_value:,} → {result.proposed_value:,.0f} "
        f"(+{result.delta_pct:.1f}%)\n"
        f"📅 Effective: {watched.effective_date}\n"
        f"⚖️ Source: {result.legal_basis}\n"
        f'🔗 <a href="{pr.pr_url}">View PR #{pr.pr_number}</a>\n\n'
        f"Confidence: HIGH ({result.sources_agreeing}/{result.sources_total} sources)\n"
        f"CI tests running — will auto-merge if all pass ✓"
    )
    try:
        await bot.send_message(chat_id, text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logger.error("Failed to send auto-applied alert: %s", e)


async def send_needs_approval_alert(
    bot: "Bot",
    chat_id: int,
    log_id: str,
    watched: "WatchedConstant",
    result: "ConfidenceResult",
    pr: "PRResult",
) -> None:
    """TYPE 2: Needs human approval — with inline buttons."""
    reason = result.block_reason or "Needs second opinion."
    text = (
        f"⚠️ <b>WAJAR_WATCH — Needs Your Approval</b>\n\n"
        f"📋 <code>{watched.key}</code>\n"
        f"💰 {watched.current_value:,} → {result.proposed_value:,.0f} "
        f"(+{result.delta_pct:.1f}%)\n"
        f"📅 Effective: {watched.effective_date}\n"
        f"⚖️ Source: {result.legal_basis}\n"
        f'🔗 <a href="{pr.pr_url}">View PR #{pr.pr_number}</a>\n\n'
        f"Confidence: MEDIUM ({result.sources_agreeing}/{result.sources_total} sources)\n"
        f"⚠️ {reason}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve & Merge", callback_data=f"wajar_approve_{log_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"wajar_reject_{log_id}"),
            ],
            [
                InlineKeyboardButton(text="🔍 Open PR", url=pr.pr_url),
            ],
        ]
    )
    try:
        await bot.send_message(
            chat_id, text, parse_mode="HTML",
            reply_markup=keyboard, disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error("Failed to send needs-approval alert: %s", e)


async def send_low_confidence_alert(
    bot: "Bot",
    chat_id: int,
    log_id: str,
    watched: "WatchedConstant",
    result: "ConfidenceResult",
    source_url: str,
) -> None:
    """TYPE 3: Low confidence — alert only, no PR created."""
    text = (
        f"🔍 <b>WAJAR_WATCH — Change Detected (Low Confidence)</b>\n\n"
        f"📋 <code>{watched.key}</code>\n"
        f"💰 Possible new value: {result.proposed_value:,.0f}\n"
        f"🌐 Detected in: {source_url}\n\n"
        f"Confidence: LOW ({result.sources_agreeing}/{result.sources_total} sources)\n"
        f"⚠️ No PR created. Manual investigation needed."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 View Source", url=source_url),
                InlineKeyboardButton(text="🚫 Dismiss", callback_data=f"wajar_dismiss_{log_id}"),
            ],
        ]
    )
    try:
        await bot.send_message(
            chat_id, text, parse_mode="HTML",
            reply_markup=keyboard, disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error("Failed to send low-confidence alert: %s", e)


async def send_critical_block_alert(
    bot: "Bot",
    chat_id: int,
    log_id: str,
    watched: "WatchedConstant",
    result: "ConfidenceResult",
    source_url: str,
) -> None:
    """TYPE 4: CRITICAL — rate/bracket change detected, NEVER auto-apply."""
    text = (
        f"🚨 <b>WAJAR_WATCH — CRITICAL: Rate Change Detected</b>\n\n"
        f"A <b>rate or bracket change</b> may have occurred in Indonesian regulation.\n"
        f"This pipeline NEVER auto-applies rate changes. Manual legal review required.\n\n"
        f"📋 <code>{watched.key}</code>\n"
        f"⚖️ Current: {watched.current_value} | Possible new: {result.proposed_value}\n"
        f"🌐 Source: {source_url}\n"
        f"📝 Block reason: {result.block_reason}\n\n"
        f"Verify the document is genuine before making any code changes."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📄 View Document", url=source_url),
                InlineKeyboardButton(text="🚫 Dismiss", callback_data=f"wajar_dismiss_{log_id}"),
            ],
        ]
    )
    try:
        await bot.send_message(
            chat_id, text, parse_mode="HTML",
            reply_markup=keyboard, disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error("Failed to send critical-block alert: %s", e)


async def send_pipeline_summary(
    bot: "Bot",
    chat_id: int,
    run_id: str,
    sources_checked: int,
    changes_detected: int,
    errors: list[str],
) -> None:
    """Send a brief pipeline completion summary (even if nothing changed)."""
    if changes_detected == 0 and not errors:
        text = (
            f"📋 <b>WAJAR_WATCH Daily — No Changes</b>\n\n"
            f"Checked {sources_checked} sources. All regulation constants unchanged.\n"
            f"<code>{run_id}</code>"
        )
    elif errors:
        text = (
            f"⚠️ <b>WAJAR_WATCH Daily — Completed with Errors</b>\n\n"
            f"Sources: {sources_checked} | Changes: {changes_detected} | "
            f"Errors: {len(errors)}\n"
            f"<code>{run_id}</code>"
        )
    else:
        text = (
            f"✅ <b>WAJAR_WATCH Daily — {changes_detected} Change(s) Processed</b>\n\n"
            f"Sources: {sources_checked}\n"
            f"<code>{run_id}</code>"
        )
    try:
        await bot.send_message(chat_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error("Failed to send pipeline summary: %s", e)
