"""WhatsApp Telegram handler.

Commands:
  /wa              — Show unread WhatsApp messages
  /wa_reply <name_or_number> <message>  — Send a WhatsApp message
  /wa_qr           — Show QR code for first-time authentication
  /wa_status       — Check sidecar connection status
"""

from __future__ import annotations

import html
import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

router = Router()
logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))


def _is_allowed(msg: Message) -> bool:
    return msg.from_user is not None and msg.from_user.id == ALLOWED_USER_ID


def _get_bridge():
    from bridges.whatsapp_bridge import WhatsAppBridge
    return WhatsAppBridge()


@router.message(Command("wa"))
async def cmd_wa(msg: Message) -> None:
    """Show unread WhatsApp messages."""
    if not _is_allowed(msg):
        return

    bridge = _get_bridge()
    status = await bridge.get_status()
    wa_status = status.get("status", "offline")

    if wa_status == "qr_pending":
        await msg.answer(
            "WhatsApp not authenticated yet. Scan the QR code first: <code>/wa_qr</code>",
            parse_mode="HTML",
        )
        return
    if wa_status == "offline":
        await msg.answer(
            "WhatsApp sidecar is offline. Starting it now...",
            parse_mode="HTML",
        )
        await bridge.start_sidecar()
        await msg.answer("Sidecar started. Try <code>/wa_qr</code> if not authenticated.", parse_mode="HTML")
        return
    if wa_status not in ("ready",):
        await msg.answer(f"WhatsApp status: <code>{html.escape(wa_status)}</code>", parse_mode="HTML")
        return

    messages = await bridge.get_unread(limit=15)
    if not messages:
        await msg.answer("No unread WhatsApp messages.")
        return

    lines = ["<b>Unread WhatsApp Messages</b>\n"]
    for m in messages[:10]:
        name = html.escape(str(m.get("name") or m.get("from", "?")))
        body = html.escape(str(m.get("body", ""))[:200])
        ts = m.get("timestamp", "")
        group = " [group]" if m.get("isGroup") else ""
        lines.append(f"<b>{name}</b>{group}: {body}")

    lines.append(
        f"\n<i>Use: <code>/wa_reply &lt;name_or_number&gt; &lt;message&gt;</code></i>"
    )
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("wa_reply"))
async def cmd_wa_reply(msg: Message) -> None:
    """Send a WhatsApp reply. Usage: /wa_reply <chat_id_or_name> <message>"""
    if not _is_allowed(msg):
        return

    args = (msg.text or "").replace("/wa_reply", "", 1).strip()
    if not args or " " not in args:
        await msg.answer(
            "Usage: <code>/wa_reply 6281234567890 Hello there!</code>\n"
            "Use the phone number with country code (no + sign) followed by @c.us,\n"
            "e.g. <code>6281234567890@c.us</code>",
            parse_mode="HTML",
        )
        return

    parts = args.split(" ", 1)
    chat_id = parts[0].strip()
    body = parts[1].strip()

    # Auto-format phone number to WhatsApp chat_id format
    if "@" not in chat_id and chat_id.isdigit():
        chat_id = f"{chat_id}@c.us"

    bridge = _get_bridge()
    status = await bridge.get_status()
    if status.get("status") != "ready":
        await msg.answer("WhatsApp not ready. Use <code>/wa_status</code>.", parse_mode="HTML")
        return

    ok = await bridge.send_message(chat_id, body)
    if ok:
        await msg.answer(
            f"✅ Sent to <code>{html.escape(chat_id)}</code>: <i>{html.escape(body[:100])}</i>",
            parse_mode="HTML",
        )
    else:
        await msg.answer(
            "Failed to send. Check <code>/wa_status</code> or rate limit (1 msg/10s).",
            parse_mode="HTML",
        )


@router.message(Command("wa_qr"))
async def cmd_wa_qr(msg: Message) -> None:
    """Show the WhatsApp QR code for first-time authentication."""
    if not _is_allowed(msg):
        return

    await msg.answer("Fetching QR code...", parse_mode="HTML")
    bridge = _get_bridge()

    # Auto-start sidecar if not running
    healthy = await bridge._is_healthy()
    if not healthy:
        await msg.answer("Starting WhatsApp sidecar...", parse_mode="HTML")
        started = await bridge.start_sidecar()
        if not started:
            await msg.answer(
                "Failed to start sidecar. Check that Node.js is installed "
                "and run <code>npm install</code> in <code>bridges/wa_sidecar/</code>",
                parse_mode="HTML",
            )
            return

    qr_bytes = await bridge.get_qr_code()
    if qr_bytes is None:
        status = await bridge.get_status()
        if status.get("status") == "ready":
            await msg.answer("Already authenticated — WhatsApp is ready!", parse_mode="HTML")
        else:
            await msg.answer(
                f"QR not ready yet (status: {status.get('status', 'unknown')}). "
                "Wait 10 seconds and try again.",
                parse_mode="HTML",
            )
        return

    await msg.answer_photo(
        BufferedInputFile(qr_bytes, filename="whatsapp_qr.png"),
        caption="Scan this QR code with WhatsApp on your phone.\n"
                "Go to: <b>WhatsApp → Settings → Linked Devices → Link a Device</b>",
        parse_mode="HTML",
    )


@router.message(Command("wa_status"))
async def cmd_wa_status(msg: Message) -> None:
    """Check WhatsApp sidecar connection status."""
    if not _is_allowed(msg):
        return

    bridge = _get_bridge()
    status = await bridge.get_status()
    wa_status = status.get("status", "offline")
    msg_count = status.get("message_count", 0)

    status_icons = {
        "ready": "✅",
        "qr_pending": "📱",
        "initialising": "⏳",
        "disconnected": "❌",
        "offline": "⭕",
    }
    icon = status_icons.get(wa_status, "❓")

    lines = [
        f"<b>WhatsApp Status</b>",
        f"Status: {icon} <code>{html.escape(wa_status)}</code>",
        f"Buffered messages: {msg_count}",
    ]
    if wa_status == "qr_pending":
        lines.append("→ Scan QR: <code>/wa_qr</code>")
    elif wa_status == "offline":
        lines.append("→ Start sidecar: <code>/wa_qr</code>")
    elif wa_status == "ready":
        lines.append("→ Read messages: <code>/wa</code>")

    await msg.answer("\n".join(lines), parse_mode="HTML")
