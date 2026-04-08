"""Firecrawl scrape (optional) or requests+BeautifulSoup fallback."""

from __future__ import annotations

import logging
import os

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def scrape_url(url: str, max_chars: int = 10000) -> str:
    api_key = (os.getenv("FIRECRAWL_API_KEY") or "").strip()
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"url": url, "formats": ["markdown"]},
                )
                if r.status_code == 200:
                    data = r.json()
                    md = (data.get("data") or {}).get("markdown") or data.get("markdown")
                    if isinstance(md, str) and md.strip():
                        return md.strip()[:max_chars]
        except Exception as exc:
            logger.debug("Firecrawl failed, falling back: %s", exc)

    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "LegionSwarmBot/1.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:max_chars]
    except Exception as exc:
        logger.warning("scraper_tool fallback failed: %s", exc)
        return f"Scrape error: {exc}"
