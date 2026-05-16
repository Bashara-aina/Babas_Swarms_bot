"""Headless fetch + visible text extraction via Playwright."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def fetch_page_text(url: str, max_chars: int = 12000) -> str:
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        logger.warning("browser_tool: Playwright not available: %s", exc)
        return "Playwright not available."

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            text = await page.inner_text("body")
            await browser.close()
            return (text or "").strip()[:max_chars]
    except Exception as exc:
        logger.warning("browser_tool fetch failed: %s", exc)
        return f"Browser fetch error: {exc}"
