"""Composio Hub — generic gateway to 850+ tool connectors.

Wraps tools/composio_client.py (Gmail/Calendar/GitHub specific) and adds:
- A generic composio_action() function for any Composio action by name
- WhatsApp Business convenience wrappers
- Graceful fallback when Composio isn't configured

Usage from anywhere:
    from tools.composio_hub import composio_action, get_unread_emails
    result = await composio_action("GMAIL_FETCH_EMAILS", {"max_results": 10})
    emails = await get_unread_emails()
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

_composio_toolset = None
_composio_init_attempted = False
_composio_lock = threading.Lock()


def _get_composio_toolset():
    """Lazy-init Composio toolset. Thread-safe singleton."""
    global _composio_toolset, _composio_init_attempted
    if _composio_init_attempted:
        return _composio_toolset
    with _composio_lock:
        if _composio_init_attempted:  # Double-check after acquiring lock
            return _composio_toolset
        _composio_init_attempted = True
        api_key = os.getenv("COMPOSIO_API_KEY", "")
        if not api_key:
            logger.info("[ComposioHub] COMPOSIO_API_KEY not set — Composio features disabled")
            return None
        try:
            from composio_langchain import ComposioToolSet

            _composio_toolset = ComposioToolSet(api_key=api_key)
            logger.info("[ComposioHub] Composio toolset initialized")
        except ImportError:
            logger.warning("[ComposioHub] composio-langchain not installed — pip install composio-langchain")
        except Exception as exc:
            logger.warning("[ComposioHub] Composio init failed: %s", exc)
        return _composio_toolset


# ── Generic action executor ───────────────────────────────────────────────────


async def composio_action(action_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Execute any Composio action by its action ID string.

    Args:
        action_name: Composio action ID, e.g. "GMAIL_FETCH_EMAILS"
        params: Optional dict of parameters for the action

    Returns:
        Dict with result or {"error": "..."} on failure
    """

    def _execute() -> dict[str, Any]:
        client = _get_composio_toolset()
        if client is None:
            return {"error": "Composio not configured — set COMPOSIO_API_KEY in .env"}
        try:
            tools = client.get_tools(actions=[action_name])
            if not tools:
                return {"error": f"Action '{action_name}' not found in Composio"}
            # tools is a list of LangChain tools; call the first one
            tool = tools[0]
            raw = tool.run(params or {})
            if isinstance(raw, dict):
                return raw
            return {"result": str(raw)}
        except Exception as exc:
            return {"error": str(exc)}

    return await asyncio.to_thread(_execute)


# ── Gmail wrappers ────────────────────────────────────────────────────────────


async def get_unread_emails(max_results: int = 10) -> list[dict[str, Any]]:
    """Fetch unread emails. Tries composio_client first (more reliable), falls back to generic."""
    try:
        from tools.composio_client import gmail_list_unread

        emails = await gmail_list_unread(max_results=max_results)
        if emails and not (len(emails) == 1 and "error" in emails[0]):
            return emails
    except Exception:
        pass
    # Generic Composio fallback
    result = await composio_action(
        "GMAIL_FETCH_EMAILS",
        {
            "max_results": max_results,
            "query": "is:unread",
        },
    )
    return result.get("emails", result.get("messages", [result] if "error" not in result else []))


async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email via Gmail."""
    try:
        from tools.composio_client import gmail_send

        return await gmail_send(to=to, subject=subject, body=body)
    except Exception:
        pass
    return await composio_action(
        "GMAIL_SEND_EMAIL",
        {
            "recipient_email": to,
            "subject": subject,
            "body": body,
        },
    )


# ── Calendar wrappers ─────────────────────────────────────────────────────────


async def get_calendar_events(days_ahead: int = 7) -> list[dict[str, Any]]:
    """Get upcoming calendar events."""
    try:
        from tools.composio_client import calendar_list_upcoming

        events = await calendar_list_upcoming(days_ahead=days_ahead)
        if events and not (len(events) == 1 and "error" in events[0]):
            return events
    except Exception:
        pass
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    future = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat().replace("+00:00", "Z")
    result = await composio_action(
        "GOOGLECALENDAR_LIST_EVENTS",
        {
            "time_min": now,
            "time_max": future,
            "max_results": 20,
        },
    )
    return result.get("events", [])


async def create_calendar_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
) -> dict[str, Any]:
    """Create a Google Calendar event."""
    try:
        from tools.composio_client import calendar_create_event

        return await calendar_create_event(title=title, start=start, end=end, description=description)
    except Exception:
        pass
    return await composio_action(
        "GOOGLECALENDAR_CREATE_EVENT",
        {
            "summary": title,
            "start": {"dateTime": start, "timeZone": "Asia/Tokyo"},
            "end": {"dateTime": end, "timeZone": "Asia/Tokyo"},
            "description": description,
        },
    )


# ── WhatsApp wrappers ─────────────────────────────────────────────────────────


async def get_whatsapp_messages(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent WhatsApp messages (requires WhatsApp Business API via Composio)."""
    result = await composio_action("WHATSAPP_GET_MESSAGES", {"limit": limit})
    return result.get("messages", [result] if "error" not in result else [])


async def send_whatsapp_message(to: str, message: str) -> dict[str, Any]:
    """Send a WhatsApp message."""
    return await composio_action(
        "WHATSAPP_SEND_MESSAGE",
        {
            "to": to,
            "message": message,
        },
    )


# ── Status helper ─────────────────────────────────────────────────────────────


def composio_hub_status() -> str:
    """Return a one-line status string for /keys or health checks."""
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    if not api_key:
        return "❌ Composio: not configured (COMPOSIO_API_KEY missing)"
    toolset = _get_composio_toolset()
    if toolset is None:
        return "❌ Composio: init failed (check logs)"
    return "✅ Composio: ready (850+ tool connectors)"
