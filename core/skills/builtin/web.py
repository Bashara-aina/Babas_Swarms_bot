"""Web skills using Crawl4AI and Playwright."""

from __future__ import annotations

import logging
import re

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _web_audit_handler(text: str) -> str:
    """Audit a website for performance and health."""
    url_match = re.search(r"https?://[^\s'\"]+", text)
    if not url_match:
        return "No URL found in message. Please provide a URL to audit."
    url = url_match.group(0).rstrip(".,)")

    try:
        from tools.browser_agent import check_site_health

        result = await check_site_health(url)
        if "error" in result:
            return f"❌ Audit failed: {result.get('error', 'unknown error')}"
        status = result.get("status", "unknown")
        load = result.get("load_time_ms", "?")
        http = result.get("http_status", "?")
        title = result.get("title", "N/A")
        icon = {"ok": "✅", "degraded": "⚠️", "unreachable": "❌"}.get(status, "❓")
        return f"{icon} Site Audit\nURL: {url}\nStatus: {status.upper()}\nHTTP: {http}\nLoad: {load}ms\nTitle: {title}"
    except Exception as exc:
        return f"❌ Audit error: {exc}"


async def _url_check_handler(text: str) -> str:
    """Check if a URL is reachable and returns valid content."""
    url_match = re.search(r"https?://[^\s'\"]+", text)
    if not url_match:
        return "No URL found. Please provide a URL to check."
    url = url_match.group(0).rstrip(".,)")

    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            if result and result.get("markdown"):
                content_preview = result["markdown"][:300]
                return f"✅ URL reachable: {url}\n\nPreview:\n{content_preview}..."
            return f"⚠️ URL returned no content: {url}"
    except Exception as exc:
        return f"❌ URL check failed: {exc}"


async def _web_scrape_handler(text: str) -> str:
    """Scrape a webpage and extract its content."""
    url_match = re.search(r"https?://[^\s'\"]+", text)
    if not url_match:
        return "No URL found. Please provide a URL to scrape."
    url = url_match.group(0).rstrip(".,)")

    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            if result and result.get("markdown"):
                content = result["markdown"][:4000]
                return f"🌐 Scraped: {url}\n\n{content}"
            return f"⚠️ No content extracted from: {url}"
    except Exception as exc:
        return f"❌ Scrape failed: {exc}"


def _register_web_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="web_audit",
            description="Audit a website for health, load time, and performance",
            trigger_keywords=["audit", "site health", "website check", "check site", "site analysis"],
            handler=_web_audit_handler,
            required_env_keys=[],
            category="web",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="url_check",
            description="Check if a URL is reachable and returns valid content",
            trigger_keywords=["url check", "check url", "is site up", "website up", "ping url"],
            handler=_url_check_handler,
            required_env_keys=[],
            category="web",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="web_scrape",
            description="Scrape and extract content from a webpage",
            trigger_keywords=["scrape", "extract from url", "get page content", "fetch url", "parse webpage"],
            handler=_web_scrape_handler,
            required_env_keys=[],
            category="web",
        )
    )


_register_web_skills()
