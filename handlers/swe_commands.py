"""SWE-agent command handlers: /fix /fix_dry.

SWE-agent: GitHub issue URL → clone repo → write fix → open PR.
Usage:
  /fix https://github.com/owner/repo/issues/123
  /fix_dry https://github.com/owner/repo/issues/123
"""

from __future__ import annotations

import asyncio
import html as html_mod

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tools.swe_agent_bridge import SWEBridge
from handlers.shared import is_allowed

router = Router()
_swe = SWEBridge()


def _require_owner(message: Message) -> bool:
    """Return True if the message is from the allowed user, False otherwise."""
    return is_allowed(message)


@router.message(Command("fix"))
async def cmd_fix(message: Message) -> None:
    """
    /fix <github_issue_url>
    Run SWE-agent on a GitHub issue — clones repo, writes fix, opens PR.
    """
    if not _require_owner(message):
        return
    url = message.text.removeprefix("/fix").strip()
    if not url.startswith("https://github.com/"):
        await message.answer(
            "usage: <code>/fix &lt;github_issue_url&gt;</code>\n\n"
            "Example: <code>/fix https://github.com/owner/repo/issues/123</code>",
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"Running SWE-agent on issue…\n<code>{html_mod.escape(url[:80])}</code>",
        parse_mode="HTML",
    )

    try:
        result = await asyncio.wait_for(_swe.fix_issue(url), timeout=600)
    except asyncio.TimeoutError:
        result = "Timed out after 10 minutes. Check logs."

    if "PR opened" in result or "github.com" in result:
        await message.answer(f"✅ {html_mod.escape(result)}")
    else:
        await message.answer(
            f"SWE-agent finished:\n<code>{html_mod.escape(result[:4000])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("fix_dry"))
async def cmd_fix_dry(message: Message) -> None:
    """
    /fix_dry <github_issue_url>
    Dry-run SWE-agent — shows what it would do without opening a PR.
    """
    if not _require_owner(message):
        return
    url = message.text.removeprefix("/fix_dry").strip()
    if not url.startswith("https://github.com/"):
        await message.answer(
            "usage: <code>/fix_dry &lt;github_issue_url&gt;</code>",
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"SWE-agent dry-run on issue…\n<code>{html_mod.escape(url[:80])}</code>",
        parse_mode="HTML",
    )

    try:
        result = await asyncio.wait_for(_swe.dry_run(url), timeout=300)
    except asyncio.TimeoutError:
        result = "Timed out after 5 minutes."

    await message.answer(
        f"Dry-run result:\n<code>{html_mod.escape(result[:4000])}</code>",
        parse_mode="HTML",
    )
