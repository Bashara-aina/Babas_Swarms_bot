# /home/newadmin/swarm-bot/playwright_agent.py
"""Headless Chromium web automation via Playwright.

All browser work runs synchronously inside a thread-pool executor
so the aiogram event loop stays unblocked.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

# Shared browser launch args required on headless Linux (no display server)
_LAUNCH_ARGS: list[str] = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
]

DEFAULT_TIMEOUT_MS = 30_000


def _scrape_sync(url: str) -> str:
    """Scrape visible text from a URL (blocking).

    Args:
        url: Fully-qualified URL to load.

    Returns:
        Extracted page text, or an error string.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=_LAUNCH_ARGS)
        try:
            page = browser.new_page()
            page.goto(url, timeout=DEFAULT_TIMEOUT_MS, wait_until="domcontentloaded")
            text: str = page.inner_text("body")
            return text.strip() or "(page body was empty)"
        except PlaywrightTimeout:
            logger.warning("Scrape timed out for %s", url)
            return f"Timeout loading {url}"
        except Exception as exc:
            logger.exception("Scrape error for %s: %s", url, exc)
            return f"Error scraping {url}: {exc}"
        finally:
            browser.close()


def _screenshot_sync(url: str) -> Path:
    """Take a full-page screenshot and return the temp file path (blocking).

    Args:
        url: Fully-qualified URL to load.

    Returns:
        Path to the PNG screenshot file.

    Raises:
        RuntimeError: If the screenshot cannot be taken.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=_LAUNCH_ARGS)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(url, timeout=DEFAULT_TIMEOUT_MS, wait_until="networkidle")
            page.screenshot(path=str(tmp_path), full_page=True)
            logger.debug("Screenshot saved to %s", tmp_path)
            return tmp_path
        except PlaywrightTimeout:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"Timeout loading {url}")
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            logger.exception("Screenshot error for %s: %s", url, exc)
            raise RuntimeError(f"Error screenshotting {url}: {exc}") from exc
        finally:
            browser.close()


async def scrape(url: str) -> str:
    """Async wrapper — scrape page text from a URL.

    Args:
        url: Fully-qualified URL.

    Returns:
        Page text string.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _scrape_sync, url)


async def screenshot(url: str) -> Path:
    """Async wrapper — take a screenshot and return its temp path.

    Caller is responsible for unlinking the file after sending.

    Args:
        url: Fully-qualified URL.

    Returns:
        Path to the PNG file.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _screenshot_sync, url)
