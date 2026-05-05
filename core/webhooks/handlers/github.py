"""GitHub webhook handler — PR merged → send summary to Bashara."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_github_pr_merged(payload: dict[str, Any]) -> None:
    """Handle GitHub pull request merge events.

    Sends a Telegram notification when a PR is merged.
    """
    action = payload.get("action", "")
    if action != "closed" or not payload.get("pull_request", {}).get("merged"):
        return

    pr_title = payload["pull_request"]["title"]
    repo = payload.get("repository", {}).get("full_name", "unknown")
    merged_by = payload.get("pull_request", {}).get("merged_by", {}).get("login", "unknown")

    msg = f"🔀 PR Merged\n<b>{repo}</b>\n{pr_title}\nby @{merged_by}"

    try:
        import handlers.shared as _shared

        if _shared._bot and _shared.ALLOWED_USER_ID:
            await _shared._bot.send_message(_shared.ALLOWED_USER_ID, msg)  # type: ignore[reportGeneralTypeIssues]
    except Exception as e:
        logger.warning("Failed to send GitHub PR notification: %s", e)
