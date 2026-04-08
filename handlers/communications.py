"""Communication handlers — email, calendar via Composio Hub.

All commands are triggered by slash commands OR via intent routing
when Legion detects EMAIL_READ / EMAIL_WRITE / SCHEDULE_TASK intents.
"""
from __future__ import annotations

import html
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed, send_chunked

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("emails", "inbox"))
async def cmd_emails(message: Message) -> None:
    """Show unread emails — /emails or /inbox."""
    if not is_allowed(message):
        return
    status = await message.answer("📧 Checking inbox...")
    try:
        from tools.composio_hub import get_unread_emails
        emails = await get_unread_emails(max_results=5)

        if not emails:
            await status.edit_text("📭 Inbox clean — no unread emails.")
            return

        lines = ["<b>📧 Unread Emails</b>\n"]
        for e in emails[:5]:
            sender = html.escape(str(e.get("from", e.get("sender", "Unknown")))[:60])
            subject = html.escape(str(e.get("subject", "No subject"))[:80])
            snippet = html.escape(str(e.get("snippet", e.get("body", "")))[:120])
            lines.append(f"<b>From:</b> {sender}\n<b>Subject:</b> {subject}\n<i>{snippet}</i>\n")

        await status.edit_text("\n".join(lines), parse_mode="HTML")

    except Exception as exc:
        logger.warning("[communications] emails failed: %s", exc)
        await status.edit_text(
            f"❌ Email check failed: <code>{html.escape(str(exc)[:200])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("calendar"))
async def cmd_calendar(message: Message) -> None:
    """Show upcoming calendar events — /calendar."""
    if not is_allowed(message):
        return
    status = await message.answer("📅 Checking calendar...")
    try:
        from tools.composio_hub import get_calendar_events
        events = await get_calendar_events(days_ahead=7)

        if not events:
            await status.edit_text("📅 Nothing scheduled in the next 7 days.")
            return

        lines = ["<b>📅 Upcoming Events (next 7 days)</b>\n"]
        for e in events[:8]:
            title = html.escape(str(e.get("summary", "Untitled"))[:80])
            start_data = e.get("start", {})
            start = str(
                start_data.get("dateTime", start_data.get("date", "TBD"))
                if isinstance(start_data, dict)
                else start_data
            )[:20]
            lines.append(f"• <b>{title}</b> — {start}")

        await status.edit_text("\n".join(lines), parse_mode="HTML")

    except Exception as exc:
        logger.warning("[communications] calendar failed: %s", exc)
        await status.edit_text(
            f"❌ Calendar check failed: <code>{html.escape(str(exc)[:200])}</code>",
            parse_mode="HTML",
        )
