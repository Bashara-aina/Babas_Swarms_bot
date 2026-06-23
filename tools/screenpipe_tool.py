"""
Screenpipe integration — optional local screen + audio recall (http://localhost:3030).

API reference: https://docs.screenpi.pe/api-reference/context-retrieval/search-screen-and-audio-content-with-various-filters
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

_screenpipe_singleton: ScreenpipeTool | None = None


def _truthy(val: str | None) -> bool:
    if not val:
        return False
    return val.strip().lower() in ("1", "true", "yes", "on")


class ScreenpipeTool:
    """Query Screenpipe HTTP API. Fails silent when service is down."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("SCREENPIPE_URL", "http://127.0.0.1:3030")).rstrip("/")

    def is_configured(self) -> bool:
        return _truthy(os.getenv("SCREENPIPE_ENABLED", "0"))

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        hours_back: int = 168,
        content_type: str = "all",
        timeout_sec: float = 5.0,
    ) -> str:
        if not self.is_configured():
            return ""
        start_time = (datetime.now(UTC) - timedelta(hours=hours_back)).isoformat().replace("+00:00", "Z")
        params: dict[str, Any] = {
            "q": query,
            "limit": limit,
            "start_time": start_time,
            "content_type": content_type,
        }
        url = f"{self.base_url}/search"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout_sec),
                ) as resp:
                    if resp.status != 200:
                        logger.debug("Screenpipe search HTTP %s", resp.status)
                        return ""
                    data = await resp.json()
        except Exception as exc:
            logger.warning("Screenpipe unavailable (%s): %s", url, exc)
            return ""

        rows = data.get("data") or data.get("results") or data.get("items") or []
        if not isinstance(rows, list) or not rows:
            return ""

        lines: list[str] = []
        for item in rows[:limit]:
            if not isinstance(item, dict):
                continue
            ts = str(item.get("timestamp") or item.get("created_at") or "")[:19]
            typ = str(item.get("type") or item.get("content_type") or "entry").upper()
            content = item.get("content") or item.get("data") or {}
            if isinstance(content, str):
                text = content[:220]
                app = "unknown"
            elif isinstance(content, dict):
                text = (content.get("text") or content.get("transcription") or content.get("body") or "")[:220]
                app = str(content.get("app_name") or content.get("app") or "unknown")
            else:
                text = str(content)[:220]
                app = "unknown"

            if "AUDIO" in typ or typ == "TRANSCRIPTION":
                lines.append(f"[{ts}] Audio: {text}")
            else:
                lines.append(f"[{ts}] Screen ({app}): {text}")

        if not lines:
            return ""
        return "## SCREENPIPE CONTEXT (recent screen/audio)\n" + "\n".join(lines)

    async def get_recent_activity(self, hours: int = 2) -> str:
        return await self.search(
            "error traceback exception terminal code",
            limit=10,
            hours_back=hours,
        )

    async def get_app_context(self, app_name: str) -> str:
        return await self.search(app_name, limit=5, hours_back=24)


def get_screenpipe_tool() -> ScreenpipeTool:
    global _screenpipe_singleton
    if _screenpipe_singleton is None:
        _screenpipe_singleton = ScreenpipeTool()
    return _screenpipe_singleton
