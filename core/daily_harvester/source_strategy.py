"""Source strategy — trust scoring, fetching, search, and contradiction resolution."""

from __future__ import annotations

import asyncio
import logging
import warnings
from typing import Any

import httpx

from core.daily_harvester.types import SourceInfo, SourceType, TrustTier

logger = logging.getLogger(__name__)
warnings.filterwarnings(
    "ignore",
    message=r".*duckduckgo_search.*renamed to `ddgs`.*",
    category=RuntimeWarning,
)
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    module=r"duckduckgo_search.*",
)

FEATURE_WEB_SEARCH_ENABLED = True

# Trust scores by source type
_TRUST_SCORES: dict[SourceType, int] = {
    SourceType.GOV: 10,
    SourceType.ACADEMIC: 9,
    SourceType.INDUSTRY: 7,
    SourceType.COMMUNITY: 5,
    SourceType.SOCIAL: 3,
}

# Trust tier mapping
_TRUST_TIERS: dict[int, TrustTier] = {
    10: TrustTier.TIER_1_GOV,
    9: TrustTier.TIER_2_ACADEMIC,
    7: TrustTier.TIER_3_PROFESSIONAL,
    6: TrustTier.TIER_4_COMMUNITY,
    5: TrustTier.TIER_4_COMMUNITY,
    3: TrustTier.TIER_5_ANONYMOUS,
}


def get_trust_score(source_type: SourceType) -> int:
    """Return the trust score for a source type."""
    return _TRUST_SCORES.get(source_type, 3)


def get_trust_tier(trust_score: int) -> TrustTier:
    """Return the trust tier for a trust score."""
    return _TRUST_TIERS.get(trust_score, TrustTier.TIER_5_ANONYMOUS)


async def fetch_source(url: str) -> str:
    """
    Fetch the content of a URL using httpx (async).

    Returns the text content (up to 5000 chars), or an error string.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = response.text
            return text[:5000]
    except Exception as e:
        logger.warning("fetch_source failed for %s: %s", url, e)
        return f"[fetch error: {e}]"


async def search_sources(query: str, topic: str) -> list[SourceInfo]:
    """
    Search for sources matching a query and topic.

    Strategy: primary via DuckDuckGo (web search), fallback via arXiv API
    (academic papers). Results are de-duplicated by URL and limited to 10.

    Returns list of SourceInfo dicts with url, title, snippet,
    source_type (inferred from domain), and trust_score.
    """
    if not FEATURE_WEB_SEARCH_ENABLED:
        logger.info("Web search feature is disabled (FEATURE_WEB_SEARCH_ENABLED=False).")
        return []

    sources: list[SourceInfo] = []
    seen_urls: set[str] = set()

    # Primary: DuckDuckGo web search (run in thread to avoid blocking)
    def _ddg_search() -> list[SourceInfo]:
        try:
            try:
                from ddgs import DDGS  # type: ignore[import-not-found]
            except ImportError:
                from duckduckgo_search import DDGS

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with DDGS() as ddg:
                    results = list(ddg.text(query, max_results=10))
        except Exception as e:
            logger.warning("DuckDuckGo search failed: %s", e)
            return []
        found: list[SourceInfo] = []
        for r in results:
            url = r.get("href", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            src_type = _classify_domain(url)
            found.append(
                SourceInfo(
                    url=url,
                    source_type=src_type,
                    trust_score=get_trust_score(src_type),
                    title=r.get("title") or "Untitled",
                    snippet=r.get("body") or "",
                )
            )
        return found

    # Fallback: arXiv API for academic papers
    async def _arxiv_search() -> list[SourceInfo]:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    "http://export.arxiv.org/api/query",
                    params={"search_query": f"all:{query}", "start": 0, "max_results": 5, "sortBy": "relevance"},
                )
            if resp.status_code != 200:
                return []
            text = resp.text
            # Parse atom feed (simple regex approach for no-dep parsing)
            import re

            entries = re.findall(r"<entry>(.*?)</entry>", text, re.DOTALL)
            found: list[SourceInfo] = []
            for entry in entries:
                url_match = re.search(r"<id>(.*?)</id>", entry)
                title_match = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                if not url_match:
                    continue
                url = url_match.group(1).strip()
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                title = title_match.group(1).strip().replace("\n", " ") if title_match else "Untitled"
                snippet = summary_match.group(1).strip()[:300] if summary_match else ""
                found.append(
                    SourceInfo(
                        url=url,
                        source_type=SourceType.ACADEMIC,
                        trust_score=get_trust_score(SourceType.ACADEMIC),
                        title=title,
                        snippet=snippet,
                    )
                )
            return found
        except Exception as e:
            logger.warning("arXiv search failed: %s", e)
            return []

    # Run both in parallel, prefer DuckDuckGo results
    ddg_sources = await asyncio.to_thread(_ddg_search)
    sources.extend(ddg_sources)

    # Only fall back to arXiv if DuckDuckGo returned nothing
    if not sources:
        arxiv_sources = await _arxiv_search()
        sources.extend(arxiv_sources)

    logger.debug("search_sources('%s', '%s') -> %d results", query, topic, len(sources))
    return sources[:10]


def _classify_domain(url: str) -> SourceType:
    """Infer SourceType from URL domain."""
    lower = url.lower()
    if "arxiv.org" in lower:
        return SourceType.ACADEMIC
    if "github.com" in lower:
        return SourceType.INDUSTRY
    if "wikipedia.org" in lower:
        return SourceType.COMMUNITY
    if "twitter.com" in lower or "x.com" in lower:
        return SourceType.SOCIAL
    if any(tld in lower for tld in [".gov", ".go.jp", ".ac.jp"]):
        return SourceType.GOV
    return SourceType.COMMUNITY


class ContradictionResolver:
    """Resolve contradictions between new and existing wiki entries."""

    @staticmethod
    def _source_rank(entry: dict[str, Any]) -> int:
        """Higher = more authoritative."""
        return entry.get("veracity_score", 0.5) * get_trust_score(entry.get("source_type", SourceType.SOCIAL))

    def resolve(self, new: dict[str, Any], existing: dict[str, Any]) -> tuple[str, str]:
        """
        Resolve a contradiction between a new entry and an existing one.

        Returns (decision, reason) where decision is one of:
        - NEW_WINS: new entry is better
        - EXISTING_WINS: existing entry is better
        - SUPERSEDE: new entry should supersede existing
        - ADD_BOTH: both are valuable, keep both
        """
        new_rank = self._source_rank(new)
        existing_rank = self._source_rank(existing)

        new_date = new.get("created_at", "")
        existing_date = existing.get("created_at", "")

        # Rule 1: GOV source wins over any other
        new_type = new.get("source_type", SourceType.SOCIAL)
        existing_type = existing.get("source_type", SourceType.SOCIAL)

        if new_type == SourceType.GOV and existing_type != SourceType.GOV:
            return ("SUPERSEDE", "Government source overrules others")
        if existing_type == SourceType.GOV and new_type != SourceType.GOV:
            return ("EXISTING_WINS", "Government source already on record")

        # Rule 2: newer date wins for regulations/policies
        if new_date and existing_date and new_date > existing_date and new_type in (SourceType.GOV, SourceType.ACADEMIC):
                return ("SUPERSEDE", f"Newer regulation ({new_date}) supersedes older ({existing_date})")

        # Rule 3: higher veracity/citations wins for research
        new_citations = new.get("citations", 0)
        existing_citations = existing.get("citations", 0)

        if new_citations > existing_citations * 1.5:
            return ("SUPERSEDE", f"More citations ({new_citations} vs {existing_citations})")
        if existing_citations > new_citations * 1.5:
            return ("EXISTING_WINS", f"Higher citations ({existing_citations})")

        # Rule 4: trust score
        if new_rank > existing_rank + 2:
            return ("SUPERSEDE", f"Higher trust rank ({new_rank:.1f} vs {existing_rank:.1f})")
        if existing_rank > new_rank + 2:
            return ("EXISTING_WINS", f"Higher trust rank ({existing_rank:.1f} vs {new_rank:.1f})")

        # Rule 5: unclear — add both
        return ("ADD_BOTH", "Both entries have comparable authority; kept separate")
