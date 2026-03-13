"""WAJAR_WATCH — scraper: scrape regulation sources and detect changes."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

import httpx
from bs4 import BeautifulSoup

from tools.wajar_watch.constants import REGULATION_SOURCES
from tools.wajar_watch import supabase_writer

logger = logging.getLogger(__name__)

USER_AGENT = "WAJAR_WATCH/1.0 (cekwajar.id regulation monitor)"
REQUEST_TIMEOUT = 15.0
MIN_RECHECK_HOURS = 20  # don't re-scrape within 20 hours


@dataclass
class ScraperResult:
    source_id: str
    url: str
    changed: bool
    new_hash: str
    old_hash: str | None
    snippet: str  # first 800 chars of page text
    keywords_found: list[str] = field(default_factory=list)
    pdf_urls: list[str] = field(default_factory=list)
    error: str | None = None


def _hash_content(text: str) -> str:
    """SHA-256 hash of whitespace-stripped text."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def _extract_pdf_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract all PDF links from the page."""
    pdfs = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            if href.startswith("http"):
                pdfs.append(href)
            elif href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                pdfs.append(f"{parsed.scheme}://{parsed.netloc}{href}")
    return list(set(pdfs))


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    """Find which keywords appear in the text (case-insensitive)."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


async def _scrape_one(source: dict, client: httpx.AsyncClient) -> ScraperResult:
    """Scrape a single regulation source."""
    source_id = source["id"]
    url = source["url"]
    keywords = source.get("keywords", [])
    force = os.getenv("WAJAR_WATCH_FORCE_CHECK", "false").lower() == "true"

    # Check if recently scraped (rate limit)
    if not force:
        existing = await supabase_writer.get_page_hash(source_id, url)
        if existing and existing.get("last_checked"):
            last_checked_str = existing["last_checked"]
            try:
                if isinstance(last_checked_str, str):
                    last_checked = datetime.fromisoformat(
                        last_checked_str.replace("Z", "+00:00")
                    )
                else:
                    last_checked = last_checked_str
                cutoff = datetime.now(timezone.utc) - timedelta(hours=MIN_RECHECK_HOURS)
                if last_checked > cutoff:
                    logger.info("Skipping %s — checked %s ago", source_id, datetime.now(timezone.utc) - last_checked)
                    return ScraperResult(
                        source_id=source_id,
                        url=url,
                        changed=False,
                        new_hash=existing.get("content_hash", ""),
                        old_hash=existing.get("content_hash"),
                        snippet="",
                        keywords_found=[],
                        pdf_urls=[],
                    )
            except Exception as e:
                logger.warning("Date parse error for %s: %s — proceeding", source_id, e)

    # Fetch the page
    resp = await client.get(url, follow_redirects=True, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script/style tags before extracting text
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)

    new_hash = _hash_content(text)
    snippet = text[:800]
    pdf_urls = _extract_pdf_urls(soup, url)
    keywords_found = _find_keywords(text, keywords)

    # Check against stored hash
    existing = await supabase_writer.get_page_hash(source_id, url)
    old_hash = existing.get("content_hash") if existing else None

    if old_hash is None:
        # First run — store hash, do NOT report as changed (Safety Rule 7)
        await supabase_writer.update_page_hash(source_id, url, new_hash, snippet)
        logger.info("First run for %s — baseline stored, no change reported", source_id)
        return ScraperResult(
            source_id=source_id,
            url=url,
            changed=False,  # first run = no false positive
            new_hash=new_hash,
            old_hash=None,
            snippet=snippet,
            keywords_found=keywords_found,
            pdf_urls=pdf_urls,
        )

    changed = new_hash != old_hash
    if changed:
        await supabase_writer.update_page_hash(source_id, url, new_hash, snippet)
        logger.info("CHANGE detected for %s (hash %s→%s)", source_id, old_hash[:12], new_hash[:12])
    else:
        await supabase_writer.update_page_hash_checked_only(source_id, url)
        logger.debug("No change for %s", source_id)

    return ScraperResult(
        source_id=source_id,
        url=url,
        changed=changed,
        new_hash=new_hash,
        old_hash=old_hash,
        snippet=snippet,
        keywords_found=keywords_found,
        pdf_urls=pdf_urls,
    )


async def scrape_all_sources() -> list[ScraperResult]:
    """Scrape all REGULATION_SOURCES in parallel. Return one result per source."""
    results = []
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=REQUEST_TIMEOUT,
    ) as client:
        tasks = []
        for source in REGULATION_SOURCES:
            tasks.append(_scrape_one_safe(source, client))
        results = await asyncio.gather(*tasks)
    return list(results)


async def _scrape_one_safe(source: dict, client: httpx.AsyncClient) -> ScraperResult:
    """Wrap _scrape_one with error handling."""
    try:
        return await _scrape_one(source, client)
    except Exception as e:
        logger.error("Scraper error for %s: %s", source["id"], e)
        return ScraperResult(
            source_id=source["id"],
            url=source["url"],
            changed=False,
            new_hash="",
            old_hash=None,
            snippet="",
            keywords_found=[],
            pdf_urls=[],
            error=str(e),
        )
