#!/usr/bin/env python3
"""
Legion weekly repo scan (n8n-friendly).

Fetches curated awesome-ai-agents list + optional GitHub trending page, writes
``wiki/legion/update_proposals/YYYY-MM-DD.md``, and optionally notifies Telegram.

Does not auto-merge code. Set GITHUB_TOKEN for richer trending parsing later.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("legion_trending_watcher")

AWESOME_AGENTS_URL = (
    "https://raw.githubusercontent.com/caramaschiHG/awesome-ai-agents-2026/main/README.md"
)
TRENDING_PYTHON_WEEKLY = "https://github.com/trending/python?since=weekly"


async def _fetch_text(url: str) -> str:
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status != 200:
                return ""
            return await resp.text()


async def _fetch_trending_markdown() -> str:
    from tools.scraper_tool import scrape_url

    return await scrape_url(TRENDING_PYTHON_WEEKLY, max_chars=12000)


async def run(out_dir: Path | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    day = datetime.now().strftime("%Y-%m-%d")
    out_dir = out_dir or (root / "wiki" / "legion" / "update_proposals")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{day}.md"

    awesome, trending = await asyncio.gather(
        _fetch_text(AWESOME_AGENTS_URL),
        _fetch_trending_markdown(),
        return_exceptions=True,
    )
    if isinstance(awesome, BaseException):
        awesome = f"(fetch failed: {awesome})"
    if isinstance(trending, BaseException):
        trending = f"(fetch failed: {trending})"

    body = (
        f"# Legion repo scan — {day}\n\n"
        "## awesome-ai-agents-2026 (README excerpt)\n\n"
        f"```\n{str(awesome)[:8000]}\n```\n\n"
        "## GitHub trending python (weekly) — text extract\n\n"
        f"```\n{str(trending)[:8000]}\n```\n\n"
        "_Next: pipe through LLM evaluation + MCP GitHub issue when keys are set._\n"
    )
    out_path.write_text(body, encoding="utf-8")
    logger.info("Wrote %s", out_path)

    if os.getenv("LEGION_TRENDING_NOTIFY", "0").strip().lower() in ("1", "true", "yes", "on"):
        token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        uid = (os.getenv("ALLOWED_USER_ID") or os.getenv("BASHARA_TELEGRAM_ID") or "").strip()
        if token and uid:
            import urllib.parse
            import urllib.request

            msg = urllib.parse.quote_plus(f"Legion: weekly repo scan saved to {out_path.name}")
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={uid}&text={msg}"
            try:
                urllib.request.urlopen(url, timeout=15).read()
            except Exception as exc:
                logger.warning("telegram notify failed: %s", exc)

    return out_path


def main() -> int:
    asyncio.run(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
