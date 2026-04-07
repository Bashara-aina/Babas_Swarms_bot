"""GitHub Trending Intelligence handler.

Commands:
  /github_intel           — Scan GitHub trending (Python) and show top picks
  /eval_repo <url>        — Evaluate a specific repo for Legion relevance
  /upgrade_from <url>     — Generate + apply code from a repo README via SelfUpgradeEngine
"""

from __future__ import annotations

import html
import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))


def _is_allowed(msg: Message) -> bool:
    return msg.from_user is not None and msg.from_user.id == ALLOWED_USER_ID


@router.message(Command("github_intel"))
async def cmd_github_intel(msg: Message) -> None:
    """Scan GitHub trending Python repos and show relevant ones."""
    if not _is_allowed(msg):
        return

    await msg.answer("Scanning GitHub trending... (~30s)", parse_mode="HTML")
    try:
        from tools.github_intel import GitHubIntelEngine
        engine = GitHubIntelEngine()
        repos = await engine.fetch_trending(language="python")
        if not repos:
            await msg.answer("Couldn't scrape GitHub trending. Try again later.")
            return
        evals = await engine.evaluate_all(repos)
        report = await engine.generate_intel_report(evals)

        # Send report
        for chunk in _chunk(report, 4000):
            await msg.answer(chunk, parse_mode="HTML")

        # Auto-discover skills for high scorers (non-blocking)
        import asyncio
        high_value = [e for e in evals if e.relevance_score >= 8]
        if high_value:
            await msg.answer(
                f"Found {len(high_value)} high-value repo(s) (score ≥ 8). "
                "Running skill discovery in background...",
                parse_mode="HTML",
            )

            async def _notify(text: str) -> None:
                try:
                    await msg.answer(text[:4000], parse_mode="HTML")
                except Exception:
                    pass

            for ev in high_value[:2]:
                asyncio.create_task(engine._discover_skill(ev, _notify))

    except Exception as exc:
        await msg.answer(
            f"GitHub intel failed: <code>{html.escape(str(exc)[:300])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("eval_repo"))
async def cmd_eval_repo(msg: Message) -> None:
    """Evaluate a specific GitHub repo for Legion relevance."""
    if not _is_allowed(msg):
        return

    url = (msg.text or "").replace("/eval_repo", "", 1).strip()
    if not url or "github.com" not in url:
        await msg.answer(
            "Usage: <code>/eval_repo https://github.com/owner/repo</code>",
            parse_mode="HTML",
        )
        return

    # Extract owner/repo from URL
    import re
    match = re.search(r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)", url)
    if not match:
        await msg.answer("Invalid GitHub URL.", parse_mode="HTML")
        return

    name = match.group(1)
    await msg.answer(f"Evaluating <b>{html.escape(name)}</b>...", parse_mode="HTML")

    try:
        from tools.github_intel import GitHubIntelEngine, TrendingRepo
        engine = GitHubIntelEngine()

        # Fetch README for richer evaluation
        readme = await engine.fetch_readme(url)
        repo = TrendingRepo(
            name=name,
            url=url,
            description=readme[:300] if readme else "No description fetched",
            stars="?",
            language="",
        )
        ev = await engine.evaluate_relevance(repo)

        lines = [
            f"<b>{html.escape(name)}</b> — Score: <b>{ev.relevance_score}/10</b>",
            f"<b>Use case:</b> {html.escape(ev.use_case)}",
            f"<b>Pros:</b> {html.escape(', '.join(ev.pros))}",
            f"<b>Cons:</b> {html.escape(', '.join(ev.cons))}",
            f"<b>Risk:</b> {html.escape(ev.risk)}",
        ]
        if ev.relevance_score >= 6:
            lines.append(f"\n<code>/upgrade_from {url}</code>")
        await msg.answer("\n".join(lines), parse_mode="HTML")

    except Exception as exc:
        await msg.answer(
            f"Evaluation failed: <code>{html.escape(str(exc)[:300])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("upgrade_from"))
async def cmd_upgrade_from(msg: Message) -> None:
    """Apply a GitHub repo as a Legion upgrade (README → SelfUpgradeEngine)."""
    if not _is_allowed(msg):
        return

    url = (msg.text or "").replace("/upgrade_from", "", 1).strip()
    if not url or "github.com" not in url:
        await msg.answer(
            "Usage: <code>/upgrade_from https://github.com/owner/repo</code>",
            parse_mode="HTML",
        )
        return

    await msg.answer(f"Fetching README and planning upgrade from <code>{html.escape(url)}</code>...", parse_mode="HTML")

    try:
        from tools.github_intel import GitHubIntelEngine
        from core.self_upgrade import SelfUpgradeEngine

        engine = GitHubIntelEngine()
        readme = await engine.fetch_readme(url)
        if not readme:
            await msg.answer("Could not fetch README for this repo.", parse_mode="HTML")
            return

        async def _notify(text: str) -> None:
            try:
                await msg.answer(text[:4000], parse_mode="HTML")
            except Exception:
                pass

        upgrade_engine = SelfUpgradeEngine(notify_cb=_notify)
        request = (
            f"Integrate useful patterns from this GitHub repo into Legion:\n\n"
            f"Repo: {url}\n\n"
            f"README:\n{readme[:3000]}"
        )
        result = await upgrade_engine.upgrade(request)
        if result.success:
            await msg.answer(
                f"✅ Upgrade from <b>{html.escape(url.split('/')[-1])}</b> complete!",
                parse_mode="HTML",
            )
        else:
            await msg.answer(
                f"Upgrade failed: <code>{html.escape(result.error[:300])}</code>",
                parse_mode="HTML",
            )
    except Exception as exc:
        await msg.answer(
            f"Upgrade failed: <code>{html.escape(str(exc)[:300])}</code>",
            parse_mode="HTML",
        )


def _chunk(text: str, size: int) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]
