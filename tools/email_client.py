"""email_client.py — Async IMAP/SMTP email client for Legion.

Gmail setup:
  1. Enable 2FA on your Google account
  2. Go to myaccount.google.com → Security → App passwords
  3. Generate an App Password for "Mail"
  4. Add to .env:
     EMAIL_ADDRESS=you@gmail.com
     EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

Requirements:
    pip install aioimaplib aiosmtplib
"""

from __future__ import annotations

import asyncio
import email
import email.header
import logging
import os
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Defaults for Gmail (overridable via env)
_IMAP_HOST = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
_IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", "993"))
_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
_EMAIL = os.getenv("EMAIL_ADDRESS", "")
_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")


def _check_config() -> str | None:
    """Check if email is configured. Returns error message or None."""
    if not _EMAIL or not _PASSWORD:
        return (
            "Email not configured. Add to .env:\n"
            "  EMAIL_ADDRESS=you@gmail.com\n"
            "  EMAIL_APP_PASSWORD=your_app_password\n\n"
            "For Gmail: enable 2FA, then generate an App Password at\n"
            "myaccount.google.com → Security → App passwords"
        )
    return None


def _decode_header(header_value: str) -> str:
    """Decode email header (handles encoded-word syntax)."""
    if not header_value:
        return ""
    decoded_parts = email.header.decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def _extract_body(msg: email.message.Message) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
            elif ctype == "text/html":
                # Strip HTML tags as fallback
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
                    return re.sub(r"<[^>]+>", "", html).strip()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


async def check_inbox(
    folder: str = "INBOX",
    limit: int = 10,
    unread_only: bool = True,
) -> str:
    """List recent emails. Returns formatted text."""
    err = _check_config()
    if err:
        return err

    import aioimaplib

    try:
        client = aioimaplib.IMAP4_SSL(host=_IMAP_HOST, port=_IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(_EMAIL, _PASSWORD)
        await client.select(folder)

        # Search for messages
        if unread_only:
            _, data = await client.search("UNSEEN")
        else:
            _, data = await client.search("ALL")

        uids = data[0].split() if data and data[0] else []
        if not uids:
            await client.logout()
            return "No unread emails." if unread_only else "No emails found."

        # Get the most recent N
        recent_uids = uids[-limit:]
        recent_uids.reverse()

        lines = [f"📧 {'Unread' if unread_only else 'Recent'} emails ({len(uids)} total):\n"]

        for uid in recent_uids:
            _, msg_data = await client.fetch(uid.decode(), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if msg_data and len(msg_data) >= 2:
                header_bytes = msg_data[1]
                if isinstance(header_bytes, bytes):
                    msg = email.message_from_bytes(header_bytes)
                    from_addr = _decode_header(msg.get("From", ""))
                    subject = _decode_header(msg.get("Subject", "(no subject)"))
                    date = msg.get("Date", "")
                    lines.append(f"  [{uid.decode()}] {subject[:60]}")
                    lines.append(f"    From: {from_addr[:40]} | {date[:20]}")
                    lines.append("")

        await client.logout()
        return "\n".join(lines)
    except Exception as e:
        return f"Email check failed: {e}"


async def read_email(uid: str) -> str:
    """Read full email by UID."""
    err = _check_config()
    if err:
        return err

    import aioimaplib

    try:
        client = aioimaplib.IMAP4_SSL(host=_IMAP_HOST, port=_IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(_EMAIL, _PASSWORD)
        await client.select("INBOX")

        _, msg_data = await client.fetch(uid, "(RFC822)")
        if not msg_data or len(msg_data) < 2:
            await client.logout()
            return f"Email {uid} not found."

        raw = msg_data[1]
        if isinstance(raw, bytes):
            msg = email.message_from_bytes(raw)
        else:
            await client.logout()
            return f"Could not parse email {uid}"

        from_addr = _decode_header(msg.get("From", ""))
        to_addr = _decode_header(msg.get("To", ""))
        subject = _decode_header(msg.get("Subject", "(no subject)"))
        date = msg.get("Date", "")
        body = _extract_body(msg)

        # List attachments
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                filename = part.get_filename()
                if filename:
                    attachments.append(_decode_header(filename))

        result = (
            f"From: {from_addr}\n"
            f"To: {to_addr}\n"
            f"Subject: {subject}\n"
            f"Date: {date}\n"
        )
        if attachments:
            result += f"Attachments: {', '.join(attachments)}\n"
        result += f"\n{body[:4000]}"

        await client.logout()
        return result
    except Exception as e:
        return f"Read email failed: {e}"


async def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[list[str]] = None,
) -> str:
    """Send an email via SMTP."""
    err = _check_config()
    if err:
        return err

    import aiosmtplib

    try:
        msg = MIMEMultipart()
        msg["From"] = _EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Handle attachments
        if attachments:
            for filepath in attachments:
                p = Path(filepath).expanduser()
                if p.exists():
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(p.read_bytes())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={p.name}",
                    )
                    msg.attach(part)

        await aiosmtplib.send(
            msg,
            hostname=_SMTP_HOST,
            port=_SMTP_PORT,
            start_tls=True,
            username=_EMAIL,
            password=_PASSWORD,
        )
        return f"Email sent to {to}: '{subject}'"
    except Exception as e:
        return f"Send email failed: {e}"


async def reply_email(uid: str, body: str) -> str:
    """Reply to an email by UID."""
    err = _check_config()
    if err:
        return err

    import aioimaplib

    try:
        # First, read the original email to get From/Subject
        client = aioimaplib.IMAP4_SSL(host=_IMAP_HOST, port=_IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(_EMAIL, _PASSWORD)
        await client.select("INBOX")

        _, msg_data = await client.fetch(uid, "(RFC822)")
        await client.logout()

        if not msg_data or len(msg_data) < 2:
            return f"Original email {uid} not found."

        raw = msg_data[1]
        if isinstance(raw, bytes):
            original = email.message_from_bytes(raw)
        else:
            return f"Could not parse email {uid}"

        reply_to = _decode_header(original.get("Reply-To") or original.get("From", ""))
        orig_subject = _decode_header(original.get("Subject", ""))
        subject = f"Re: {orig_subject}" if not orig_subject.startswith("Re:") else orig_subject

        # Extract email address from "Name <email>" format
        match = re.search(r"<([^>]+)>", reply_to)
        to_addr = match.group(1) if match else reply_to

        return await send_email(to_addr, subject, body)
    except Exception as e:
        return f"Reply failed: {e}"


async def search_emails(
    query: str,
    folder: str = "INBOX",
    limit: int = 20,
) -> str:
    """Search emails by subject text."""
    err = _check_config()
    if err:
        return err

    import aioimaplib

    try:
        client = aioimaplib.IMAP4_SSL(host=_IMAP_HOST, port=_IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(_EMAIL, _PASSWORD)
        await client.select(folder)

        _, data = await client.search(f'SUBJECT "{query}"')
        uids = data[0].split() if data and data[0] else []

        if not uids:
            await client.logout()
            return f"No emails matching: {query}"

        recent = uids[-limit:]
        recent.reverse()

        lines = [f"🔍 Search results for '{query}' ({len(uids)} found):\n"]
        for uid in recent:
            _, msg_data = await client.fetch(uid.decode(), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if msg_data and len(msg_data) >= 2:
                header_bytes = msg_data[1]
                if isinstance(header_bytes, bytes):
                    msg = email.message_from_bytes(header_bytes)
                    subject = _decode_header(msg.get("Subject", "(no subject)"))
                    from_addr = _decode_header(msg.get("From", ""))
                    lines.append(f"  [{uid.decode()}] {subject[:60]}")
                    lines.append(f"    From: {from_addr[:40]}")
                    lines.append("")

        await client.logout()
        return "\n".join(lines)
    except Exception as e:
        return f"Email search failed: {e}"


async def summarize_inbox(limit: int = 20) -> str:
    """Get inbox summary for LLM to process."""
    return await check_inbox(limit=limit, unread_only=False)
