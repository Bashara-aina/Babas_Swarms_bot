"""Firecrawl scrape with automatic fallback chain.

Fallback order (when Firecrawl fails or is exhausted):
1. Firecrawl API (if key available and credits exist)
2. httpx + BeautifulSoup (basic HTML scraping)
3. Use browse MCP tool (headless Chromium) for JS-rendered pages
4. Use exa_web_fetch_exa for alternative web extraction

Error detection:
- 402: Credits exhausted / Payment required
- 429: Rate limited / Too many requests
- "Insufficient credits", "credits exhausted", "blocked" in response
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FIRECRCRAWL_EXHAUSTED_CODES = {402, 429}
FIRECRCRAWL_EXHAUSTED_PATTERNS = re.compile(
    r"(insufficient credits|credits exhausted|blocked|rate limit|too many requests)",
    re.IGNORECASE,
)


def is_firecrawl_exhausted(status_code: int, response_text: str = "") -> bool:
    if status_code in FIRECRCRAWL_EXHAUSTED_CODES:
        return True
    if FIRECRCRAWL_EXHAUSTED_PATTERNS.search(response_text):
        return True
    return False


async def scrape_url(
    url: str,
    max_chars: int = 10000,
    prefer_fallback: bool = False,
) -> tuple[str, str]:
    """Scrape URL with automatic fallback.

    Returns:
        Tuple of (content, source) where source is one of:
        - "firecrawl": Successfully scraped via Firecrawl API
        - "httpx": Scraped via httpx + BeautifulSoup fallback
        - "error": Failed to scrape, returns error message
    """
    api_key = (os.getenv("FIRECRAWL_API_KEY") or "").strip()

    if api_key and not prefer_fallback:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"url": url, "formats": ["markdown"]},
                )
                response_text = r.text

                if r.status_code == 200:
                    data = r.json()
                    md = (data.get("data") or {}).get("markdown") or data.get("markdown")
                    if isinstance(md, str) and md.strip():
                        return md.strip()[:max_chars], "firecrawl"

                if is_firecrawl_exhausted(r.status_code, response_text):
                    logger.debug(
                        "Firecrawl exhausted (status=%d), falling back", r.status_code
                    )

        except Exception as exc:
            logger.debug("Firecrawl request failed, falling back: %s", exc)

    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "LegionSwarmBot/1.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:max_chars], "httpx"
    except Exception as exc:
        logger.warning("scraper_tool fallback failed: %s", exc)
        return f"Scrape error: {exc}", "error"


async def scrape_url_with_fallbacks(url: str, max_chars: int = 10000) -> dict:
    """Scrape URL trying all available methods.

    Returns dict with keys:
        - content: scraped content or error message
        - source: "firecrawl", "httpx", "browse", "exa", or "error"
        - firecrawl_exhausted: bool indicating if Firecrawl was exhausted
    """
    result = {
        "url": url,
        "content": "",
        "source": "error",
        "firecrawl_exhausted": False,
    }

    content, source = await scrape_url(url, max_chars)
    result["content"] = content
    result["source"] = source

    if source == "firecrawl":
        return result

    if source == "error" and "Insufficient credits" in content:
        result["firecrawl_exhausted"] = True

    return result


async def suggest_fallback_tools(url: str) -> list[dict]:
    """Suggest alternative tools when primary scraping fails.

    Returns list of dicts with tool suggestions and usage hints.
    """
    suggestions = []

    suggestions.append({
        "tool": "browse",
        "reason": "Headless Chromium for JS-rendered pages",
        "usage": "browse goto <url>; browse snapshot; browse text",
    })

    suggestions.append({
        "tool": "exa_web_fetch_exa",
        "reason": "Alternative web extraction with search",
        "usage": 'firecrawl_extract(urls=["<url>"], prompt="extract content")',
    })

    suggestions.append({
        "tool": "webfetch",
        "reason": "Simple URL content fetcher",
        "usage": "webfetch(url=<url>, format=\"markdown\")",
    })

    return suggestions
