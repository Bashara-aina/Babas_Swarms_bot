"""
Composio integration client — 850+ tool connectors for Legion.

Provides:
- Gmail: read, search, send, reply, label
- Google Calendar: list events, create events, check availability
- GitHub: issues, PRs, code search (augments existing github_intel.py)
- Slack: send messages, read channels
- WhatsApp Business: send messages, read recent (requires WhatsApp Business API)
- Notion: read/write pages and databases
- Supabase: query via Composio managed auth (optional, Legion has native client)
- Web search: Google Search, Perplexity-style search

Composio handles OAuth, token refresh, and rate limiting automatically.
Legion calls these as natural tool invocations — no slash commands needed.

Setup:
  pip install composio-core composio-langchain
  composio login  (run once on server)
  composio add gmail google-calendar github  (connect each app)

Docs: https://docs.composio.dev
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── Optional Composio import (graceful if not installed) ─────────────────────
try:
    from composio_langchain import Action, App, ComposioToolSet
    _COMPOSIO_AVAILABLE = True
except ImportError:
    try:
        from composio import Action, App, ComposioToolSet  # type: ignore
        _COMPOSIO_AVAILABLE = True
    except ImportError:
        _COMPOSIO_AVAILABLE = False
        logger.warning(
            "Composio not installed. Run: pip install composio-core composio-langchain"
        )

_toolset: Any | None = None


def get_toolset() -> Any | None:
    """Get or initialize the Composio toolset (lazy, singleton)."""
    global _toolset
    if not _COMPOSIO_AVAILABLE:
        return None
    if _toolset is not None:
        return _toolset
    try:
        api_key = os.getenv("COMPOSIO_API_KEY", "")
        if not api_key:
            logger.warning(
                "COMPOSIO_API_KEY not set. Get it from https://app.composio.dev"
            )
        _toolset = ComposioToolSet(api_key=api_key if api_key else None)
        logger.info("✅ Composio toolset initialized")
        return _toolset
    except Exception as e:
        logger.warning("Composio toolset init failed: %s", e)
        return None


def is_available() -> bool:
    """Check if Composio is installed and API key is configured."""
    return _COMPOSIO_AVAILABLE and bool(os.getenv("COMPOSIO_API_KEY", ""))


# ── Gmail ─────────────────────────────────────────────────────────────────────

async def gmail_list_unread(max_results: int = 10) -> list[dict[str, Any]]:
    """unread Gmail messages. Returns list of {id, subject, from, snippet, date}."""
    if not is_available():
        return [{"error": "Composio not configured. Set COMPOSIO_API_KEY and run: composio add gmail"}]

    def _fetch() -> list[dict]:
        ts = get_toolset()
        if not ts:
            return []
        ts.get_tools(actions=[Action.GMAIL_LIST_THREADS])
        # Execute via the tool directly
        result = ts.execute_action(
            action=Action.GMAIL_LIST_THREADS,
            params={"max_results": max_results, "query": "is:unread"},
        )
        return result.get("data", {}).get("threads", []) if isinstance(result, dict) else []

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("gmail_list_unread failed: %s", e)
        return [{"error": str(e)}]


async def gmail_send(
    to: str,
    subject: str,
    body: str,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    """Send an email via Gmail."""
    if not is_available():
        return {"error": "Composio not configured"}

    def _send() -> dict:
        ts = get_toolset()
        if not ts:
            return {"error": "toolset unavailable"}
        params: dict[str, Any] = {"to": to, "subject": subject, "body": body}
        if reply_to_message_id:
            params["reply_to_message_id"] = reply_to_message_id
        return ts.execute_action(action=Action.GMAIL_SEND_EMAIL, params=params)

    try:
        return await asyncio.to_thread(_send)
    except Exception as e:
        logger.warning("gmail_send failed: %s", e)
        return {"error": str(e)}


async def gmail_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search Gmail with a query string."""
    if not is_available():
        return [{"error": "Composio not configured"}]

    def _search() -> list[dict]:
        ts = get_toolset()
        if not ts:
            return []
        result = ts.execute_action(
            action=Action.GMAIL_LIST_THREADS,
            params={"query": query, "max_results": max_results},
        )
        return result.get("data", {}).get("threads", []) if isinstance(result, dict) else []

    try:
        return await asyncio.to_thread(_search)
    except Exception as e:
        logger.warning("gmail_search failed: %s", e)
        return [{"error": str(e)}]


# ── Google Calendar ───────────────────────────────────────────────────────────

async def calendar_list_upcoming(max_results: int = 10) -> list[dict[str, Any]]:
    """upcoming Google Calendar events. Returns events sorted by start time."""
    if not is_available():
        return [{"error": "Composio not configured. Run: composio add google-calendar"}]

    def _fetch() -> list[dict]:
        ts = get_toolset()
        if not ts:
            return []
        result = ts.execute_action(
            action=Action.GOOGLECALENDAR_LIST_EVENTS,
            params={"max_results": max_results, "order_by": "startTime"},
        )
        return result.get("data", {}).get("items", []) if isinstance(result, dict) else []

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("calendar_list_upcoming failed: %s", e)
        return [{"error": str(e)}]


async def calendar_create_event(
    title: str,
    start_datetime: str,  # ISO 8601 e.g. "2026-04-10T10:00:00+09:00"
    end_datetime: str,
    description: str = "",
    location: str = "",
) -> dict[str, Any]:
    """Create a Google Calendar event."""
    if not is_available():
        return {"error": "Composio not configured"}

    def _create() -> dict:
        ts = get_toolset()
        if not ts:
            return {"error": "toolset unavailable"}
        return ts.execute_action(
            action=Action.GOOGLECALENDAR_CREATE_EVENT,
            params={
                "summary": title,
                "start": {"dateTime": start_datetime},
                "end": {"dateTime": end_datetime},
                "description": description,
                "location": location,
            },
        )

    try:
        return await asyncio.to_thread(_create)
    except Exception as e:
        logger.warning("calendar_create_event failed: %s", e)
        return {"error": str(e)}


async def calendar_get_today_schedule() -> str:
    """Get today's schedule formatted as a string for system prompt injection."""
    try:
        events = await calendar_list_upcoming(max_results=8)
        if not events or (len(events) == 1 and "error" in events[0]):
            return ""
        import datetime
        today = datetime.date.today().isoformat()
        today_events = [
            e for e in events
            if isinstance(e, dict) and today in str(e.get("start", ""))
        ]
        if not today_events:
            return ""
        lines = ["[Today's calendar (JST):"]
        for ev in today_events:
            start = ev.get("start", {}).get("dateTime", "?")[:16]
            title = ev.get("summary", "(no title)")
            lines.append(f"  {start} — {title}")
        lines.append("]")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("calendar_get_today_schedule failed: %s", e)
        return ""


# ── GitHub (augments existing github_intel.py) ────────────────────────────────

async def github_create_issue(
    repo: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a GitHub issue via Composio."""
    if not is_available():
        return {"error": "Composio not configured. Run: composio add github"}

    def _create() -> dict:
        ts = get_toolset()
        if not ts:
            return {"error": "toolset unavailable"}
        params: dict[str, Any] = {"owner": repo.split("/")[0], "repo": repo.split("/")[-1],
                                   "title": title, "body": body}
        if labels:
            params["labels"] = labels
        return ts.execute_action(action=Action.GITHUB_CREATE_AN_ISSUE, params=params)

    try:
        return await asyncio.to_thread(_create)
    except Exception as e:
        logger.warning("github_create_issue failed: %s", e)
        return {"error": str(e)}


# ── Composio status / health ──────────────────────────────────────────────────

async def composio_status() -> dict[str, Any]:
    """Return Composio integration status for /keys or /status command."""
    if not _COMPOSIO_AVAILABLE:
        return {
            "installed": False,
            "message": "pip install composio-core composio-langchain",
        }
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    return {
        "installed": True,
        "api_key_set": bool(api_key),
        "toolset_ready": get_toolset() is not None,
        "setup_cmd": "composio login && composio add gmail google-calendar github"
        if not api_key else "configured",
    }


async def get_langchain_tools(apps: list[str] | None = None) -> list[Any]:
    """
    Get Composio tools as LangChain-compatible tool objects.
    Use these to wire into LangChain agents / autonomous router.

    apps: list of app names e.g. ["gmail", "github", "google-calendar"]
          If None, returns all connected apps' tools.
    """
    if not is_available():
        return []
    try:
        ts = get_toolset()
        if not ts:
            return []
        if apps:
            app_enums = [getattr(App, a.upper().replace("-", "_"), None) for a in apps]
            app_enums = [a for a in app_enums if a]
            return await asyncio.to_thread(ts.get_tools, apps=app_enums)
        return await asyncio.to_thread(ts.get_tools)
    except Exception as e:
        logger.warning("get_langchain_tools failed: %s", e)
        return []
