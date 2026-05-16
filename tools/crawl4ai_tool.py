"""
Crawl4AI tool — async web crawling, returns clean markdown.
Free, local, no API key required.

Usage:
  result = await crawl4ai.crawl("https://example.com", mode="balanced")
  results = await crawl4ai.crawl_multiple(["url1", "url2"], concurrency=3)
"""

from __future__ import annotations

import asyncio
from typing import Literal

# Lazy import — crawl4ai is optional
_crawl4ai_installed: bool | None = None


def _check_crawl4ai() -> bool:
    global _crawl4ai_installed
    if _crawl4ai_installed is None:
        try:
            import crawl4ai

            _crawl4ai_installed = True
        except ImportError:
            _crawl4ai_installed = False
    return _crawl4ai_installed


class Crawl4AITool:
    """Async wrapper for Crawl4AI web crawler."""

    def __init__(self):
        self._crawler = None

    async def _get_crawler(self):
        if self._crawler is None:
            if not _check_crawl4ai():
                raise ImportError(
                    "crawl4ai not installed. Run: pip install crawl4ai && python -m crawl4ai --install"
                )
            from crawl4ai import AsyncWebCrawler

            self._crawler = AsyncWebCrawler()
            await self._crawler.start()
        return self._crawler

    async def crawl(
        self,
        url: str,
        mode: Literal["fast", "balanced", "deep"] = "balanced",
        max_length: int = 10000,
    ) -> dict:
        """
        Crawl a single URL and return structured markdown.
        Returns: {url, title, markdown, links, images}
        """
        crawler = await self._get_crawler()
        result = await crawler.crawl(url, mode=mode)
        return {
            "url": url,
            "title": getattr(result, "metadata", {}).get("title", ""),
            "markdown": result.markdown[:max_length] if result.markdown else "",
            "links": getattr(result, "links", [])[:20] or [],
            "images": getattr(result, "images", [])[:10] or [],
        }

    async def crawl_multiple(
        self, urls: list[str], concurrency: int = 3
    ) -> list[dict]:
        """Crawl multiple URLs concurrently, up to `concurrency` at a time."""
        semaphore = asyncio.Semaphore(concurrency)

        async def crawl_one(url: str) -> dict:
            async with semaphore:
                try:
                    return await self.crawl(url)
                except Exception as e:
                    logger.warning("crawl_multiple: crawl failed for %s: %s", url, e)
                    return {"url": url, "error": str(e)}

        return await asyncio.gather(*[crawl_one(u) for u in urls])

    async def close(self) -> None:
        """Stop the crawler and free resources."""
        if self._crawler:
            await self._crawler.stop()
            self._crawler = None


# Module-level singleton
_crawl4ai: Crawl4AITool | None = None


def get_crawl4ai() -> Crawl4AITool:
    global _crawl4ai
    if _crawl4ai is None:
        _crawl4ai = Crawl4AITool()
    return _crawl4ai
