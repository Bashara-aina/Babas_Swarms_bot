"""web_browser.py — Playwright-based web browsing for Legion.

Provides JS-rendered browsing, multi-page research, cookie bypass,
form filling, and link extraction. Runs headless Chromium.

Requirements:
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Lazy-load playwright to avoid import errors if not installed
_browser = None
_playwright = None


async def _get_browser():
    """Lazy-initialize a persistent browser instance."""
    global _browser, _playwright
    if _browser and _browser.is_connected():
        return _browser

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright not installed. Run:\n"
            "  pip install playwright && playwright install chromium"
        )

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )
    logger.info("Playwright browser launched (headless Chromium)")
    return _browser


async def _new_page(timeout: int = 30000):
    """Create a new browser page with sensible defaults."""
    browser = await _get_browser()
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        java_script_enabled=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()
    page.set_default_timeout(timeout)
    return page, context


# Common cookie/consent button selectors (ordered by specificity)
COOKIE_SELECTORS = [
    "button[id*='accept' i]",
    "button[id*='agree' i]",
    "button[id*='consent' i]",
    "button[class*='accept' i]",
    "button[class*='consent' i]",
    "a[id*='accept' i]",
    "[aria-label*='Accept' i]",
    "[aria-label*='accept all' i]",
    "button:has-text('Accept All')",
    "button:has-text('Accept all')",
    "button:has-text('I agree')",
    "button:has-text('Accept')",
    "button:has-text('OK')",
    "button:has-text('Got it')",
    "button:has-text('Agree')",
    "button:has-text('Allow all')",
    "button:has-text('Terima')",  # Indonesian
    "button:has-text('Setuju')",  # Indonesian
]


async def _dismiss_cookies(page) -> bool:
    """Try to dismiss cookie/consent popups. Returns True if clicked."""
    for selector in COOKIE_SELECTORS:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=500):
                await btn.click(timeout=2000)
                await asyncio.sleep(0.5)
                logger.info("Dismissed cookie popup via: %s", selector)
                return True
        except Exception:
            continue
    return False


async def browse_url(
    url: str,
    extract_selector: str = "body",
    wait_for: str = "domcontentloaded",
    max_text_chars: int = 8000,
) -> dict[str, Any]:
    """Browse a URL with full JS rendering.

    Returns dict with: title, url, text, links (first 20), screenshot_path.
    Automatically dismisses cookie popups.
    """
    if not re.match(r"^https?://", url):
        url = f"https://{url}"

    page, context = await _new_page()
    try:
        await page.goto(url, wait_until=wait_for, timeout=20000)
        await asyncio.sleep(1)  # Let JS settle

        # Try to dismiss cookies
        await _dismiss_cookies(page)

        title = await page.title()
        current_url = page.url

        # Extract text from selector
        try:
            element = page.locator(extract_selector).first
            text = await element.inner_text(timeout=5000)
        except Exception:
            text = await page.inner_text("body")

        # Truncate
        if len(text) > max_text_chars:
            text = text[:max_text_chars] + f"\n\n[...truncated, {len(text)} total chars]"

        # Take screenshot
        ts = int(time.time())
        screenshot_path = f"/tmp/legion_web_{ts}.png"
        await page.screenshot(path=screenshot_path, full_page=False)

        # Get links
        links = await page.eval_on_selector_all(
            "a[href]",
            """els => els.slice(0, 30).map(a => ({
                text: a.innerText.trim().substring(0, 80),
                href: a.href
            })).filter(l => l.href && !l.href.startsWith('javascript:'))"""
        )

        return {
            "title": title,
            "url": current_url,
            "text": text.strip(),
            "links": links[:20],
            "screenshot_path": screenshot_path,
        }
    except Exception as e:
        return {
            "title": "",
            "url": url,
            "text": f"Failed to load page: {e}",
            "links": [],
            "screenshot_path": "",
        }
    finally:
        await context.close()


async def web_search(query: str, num_results: int = 10) -> list[dict[str, str]]:
    """Search the web via DuckDuckGo (no API key needed).

    Returns list of {title, url, snippet}.
    """
    search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

    page, context = await _new_page(timeout=15000)
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)

        # Extract results from DuckDuckGo HTML layout
        results = await page.eval_on_selector_all(
            ".result",
            f"""els => els.slice(0, {num_results}).map(el => {{
                const a = el.querySelector('.result__a');
                const snippet = el.querySelector('.result__snippet');
                return {{
                    title: a ? a.innerText.trim() : '',
                    url: a ? a.href : '',
                    snippet: snippet ? snippet.innerText.trim() : ''
                }};
            }}).filter(r => r.url)"""
        )
        return results
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return [{"title": "Search failed", "url": "", "snippet": str(e)}]
    finally:
        await context.close()


async def deep_research(
    topic: str,
    max_pages: int = 10,
    max_text_per_page: int = 4000,
) -> str:
    """Deep multi-page research on a topic.

    1. Searches for the topic
    2. Visits top results
    3. Extracts and compiles relevant content
    4. Returns a synthesized research summary

    Returns compiled text from all visited pages.
    """
    # Step 1: Search
    results = await web_search(topic, num_results=min(max_pages, 15))
    if not results or (len(results) == 1 and not results[0]["url"]):
        return f"Search returned no results for: {topic}"

    # Step 2: Visit pages and extract content
    findings: list[dict[str, str]] = []
    visited = 0

    for result in results[:max_pages]:
        url = result.get("url", "")
        if not url or url.startswith("javascript:"):
            continue

        try:
            page_data = await browse_url(url, max_text_chars=max_text_per_page)
            text = page_data.get("text", "").strip()
            if text and len(text) > 100:  # Skip empty/tiny pages
                findings.append({
                    "title": page_data.get("title", result.get("title", "")),
                    "url": url,
                    "content": text[:max_text_per_page],
                })
                visited += 1
        except Exception as e:
            logger.warning("Failed to visit %s: %s", url, e)
            continue

    if not findings:
        return f"Searched for '{topic}' but couldn't extract content from any pages."

    # Step 3: Compile into a research document
    lines = [
        f"Research: {topic}",
        f"Sources visited: {visited}",
        "=" * 60,
        "",
    ]
    for i, f in enumerate(findings, 1):
        lines.append(f"[{i}] {f['title']}")
        lines.append(f"    URL: {f['url']}")
        lines.append(f"    {f['content'][:2000]}")
        lines.append("")

    compiled = "\n".join(lines)

    # Truncate if too long for LLM context
    if len(compiled) > 30000:
        compiled = compiled[:30000] + "\n\n[...truncated for context limits]"

    return compiled


async def fill_form(
    url: str,
    fields: dict[str, str],
    submit: bool = False,
) -> str:
    """Navigate to URL and fill form fields.

    fields: mapping of label/name/placeholder text → value to fill.
    """
    if not re.match(r"^https?://", url):
        url = f"https://{url}"

    page, context = await _new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)
        await _dismiss_cookies(page)

        filled = []
        for label, value in fields.items():
            # Try multiple strategies to find the input
            selectors = [
                f"input[name='{label}']",
                f"input[id='{label}']",
                f"input[placeholder*='{label}' i]",
                f"textarea[name='{label}']",
                f"select[name='{label}']",
            ]
            found = False
            for sel in selectors:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=1000):
                        tag = await el.evaluate("el => el.tagName.toLowerCase()")
                        if tag == "select":
                            await el.select_option(label=value)
                        else:
                            await el.fill(value)
                        filled.append(f"{label}={value}")
                        found = True
                        break
                except Exception:
                    continue

            if not found:
                # Try finding by associated label text
                try:
                    label_el = page.locator(f"label:has-text('{label}')").first
                    for_attr = await label_el.get_attribute("for")
                    if for_attr:
                        input_el = page.locator(f"#{for_attr}")
                        await input_el.fill(value)
                        filled.append(f"{label}={value}")
                except Exception:
                    filled.append(f"{label}=FAILED (field not found)")

        if submit:
            try:
                submit_btn = page.locator(
                    "button[type='submit'], input[type='submit'], "
                    "button:has-text('Submit'), button:has-text('Send')"
                ).first
                await submit_btn.click()
                await asyncio.sleep(2)
                filled.append("SUBMITTED")
            except Exception as e:
                filled.append(f"submit failed: {e}")

        return f"Form fill results:\n" + "\n".join(f"  {f}" for f in filled)
    except Exception as e:
        return f"Form fill error: {e}"
    finally:
        await context.close()


async def get_page_links(
    url: str,
    filter_pattern: str = "",
    max_links: int = 50,
) -> list[dict[str, str]]:
    """Get all links from a webpage, optionally filtered by regex pattern.

    Returns list of {text, href}.
    """
    if not re.match(r"^https?://", url):
        url = f"https://{url}"

    page, context = await _new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)
        await _dismiss_cookies(page)

        links = await page.eval_on_selector_all(
            "a[href]",
            f"""els => els.slice(0, {max_links * 2}).map(a => ({{
                text: a.innerText.trim().substring(0, 100),
                href: a.href
            }})).filter(l => l.href && !l.href.startsWith('javascript:'))"""
        )

        if filter_pattern:
            pattern = re.compile(filter_pattern, re.IGNORECASE)
            links = [l for l in links if pattern.search(l.get("href", "")) or pattern.search(l.get("text", ""))]

        return links[:max_links]
    except Exception as e:
        logger.error("get_page_links failed: %s", e)
        return []
    finally:
        await context.close()


async def browse_and_click(
    url: str,
    click_text: str,
    wait_after: float = 2.0,
) -> dict[str, Any]:
    """Navigate to URL, find and click an element by its text, return new page state."""
    if not re.match(r"^https?://", url):
        url = f"https://{url}"

    page, context = await _new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)
        await _dismiss_cookies(page)

        # Try to find and click the element
        clicked = False
        for sel in [
            f"a:has-text('{click_text}')",
            f"button:has-text('{click_text}')",
            f"[role='button']:has-text('{click_text}')",
            f"text='{click_text}'",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            return {
                "title": await page.title(),
                "url": page.url,
                "text": f"Could not find clickable element with text: '{click_text}'",
                "screenshot_path": "",
            }

        await asyncio.sleep(wait_after)

        title = await page.title()
        text = await page.inner_text("body")
        ts = int(time.time())
        screenshot_path = f"/tmp/legion_web_{ts}.png"
        await page.screenshot(path=screenshot_path, full_page=False)

        if len(text) > 8000:
            text = text[:8000] + "\n\n[...truncated]"

        return {
            "title": title,
            "url": page.url,
            "text": text.strip(),
            "screenshot_path": screenshot_path,
        }
    except Exception as e:
        return {
            "title": "",
            "url": url,
            "text": f"browse_and_click error: {e}",
            "screenshot_path": "",
        }
    finally:
        await context.close()


async def shutdown_browser() -> None:
    """Clean up browser resources. Call on bot shutdown."""
    global _browser, _playwright
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None
