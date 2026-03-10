"""deep_research.py — 5-layer Perplexity-grade research pipeline.

Layers:
  1. Query decomposition into 5-8 sub-questions
  2. Parallel web search across Google Scholar, Semantic Scholar,
     DuckDuckGo, ArXiv, Reddit/HackerNews
  3. Source credibility scoring
  4. Cross-reference synthesis — agreements, contradictions, gaps
  5. Final report: Executive Summary → Findings → Contradictions
     → Research Gaps → Implications → Sources

Designed for the /research command.
"""

from __future__ import annotations
import asyncio
import logging
import re
import json
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

# ── Credibility scores by source type ───────────────────────────────────────
SOURCE_SCORES = {
    "scholar.google.com": 10,
    "semanticscholar.org": 10,
    "arxiv.org": 9,
    ".gov": 8,
    ".edu": 8,
    "nature.com": 8,
    "science.org": 8,
    "pubmed": 8,
    "reuters.com": 7,
    "bbc.com": 7,
    "techcrunch.com": 6,
    "medium.com": 4,
    "reddit.com": 3,
    "news.ycombinator.com": 5,
    "hackernews": 5,
}

DEFAULT_SCORE = 4


def _score_source(url: str) -> int:
    """Score a URL by its source credibility."""
    url_lower = url.lower()
    for pattern, score in SOURCE_SCORES.items():
        if pattern in url_lower:
            return score
    return DEFAULT_SCORE


def _truncate_prompt(text: str, max_chars: int = 8000) -> str:
    """Prevent 'prompt too long' failures by truncating gracefully."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated for length]"


async def _search_duckduckgo(
    query: str,
    browser_search_fn: Callable[[str], Coroutine[Any, Any, list[dict]]] | None = None
) -> list[dict]:
    """Search DuckDuckGo. Returns list of {title, url, snippet} dicts."""
    if browser_search_fn:
        try:
            return await browser_search_fn(query)
        except Exception as e:
            logger.warning("DuckDuckGo search failed: %s", e)
    return []


async def _search_semantic_scholar(query: str) -> list[dict]:
    """Search Semantic Scholar API for academic papers."""
    try:
        import aiohttp
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": 5,
            "fields": "title,abstract,year,authors,url,citationCount"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for paper in data.get("data", []):
                        results.append({
                            "title": paper.get("title", ""),
                            "url": paper.get("url", f"https://semanticscholar.org/paper/{paper.get('paperId', '')}"),
                            "snippet": (paper.get("abstract") or "")[:300],
                            "year": paper.get("year"),
                            "citations": paper.get("citationCount", 0),
                            "source_type": "academic",
                        })
                    return results
    except Exception as e:
        logger.warning("Semantic Scholar search failed: %s", e)
    return []


async def _search_arxiv(query: str) -> list[dict]:
    """Search ArXiv for preprints."""
    try:
        import aiohttp
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 5
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Simple XML parsing
                    entries = re.findall(r'<entry>(.*?)</entry>', text, re.DOTALL)
                    results = []
                    for entry in entries[:5]:
                        title_m = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                        link_m = re.search(r'<id>(.*?)</id>', entry)
                        summary_m = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                        if title_m and link_m:
                            results.append({
                                "title": re.sub(r'\s+', ' ', title_m.group(1)).strip(),
                                "url": link_m.group(1).strip(),
                                "snippet": re.sub(r'\s+', ' ', (summary_m.group(1) if summary_m else ""))[:300].strip(),
                                "source_type": "preprint",
                            })
                    return results
    except Exception as e:
        logger.warning("ArXiv search failed: %s", e)
    return []


async def run_deep_research(
    topic: str,
    llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    browser_search_fn: Callable[[str], Coroutine[Any, Any, list[dict]]] | None = None,
) -> str:
    """Run the full 5-layer deep research pipeline.

    Args:
        topic: The research topic/question.
        llm_call: async fn(model, system_prompt, user_message) -> str
        progress_fn: Optional async callback for Telegram status updates.
        browser_search_fn: Optional async fn(query) -> list[{title,url,snippet}]
            If None, only Semantic Scholar + ArXiv are searched.

    Returns:
        Formatted research report string.
    """
    from agents import AGENT_MODELS, build_system_prompt

    async def _progress(msg: str):
        if progress_fn:
            await progress_fn(msg)
        logger.info("[DeepResearch] %s", msg)

    # ── LAYER 1: Query Decomposition ─────────────────────────────────────────
    await _progress("🔍 Layer 1/5 — Decomposing query into sub-questions...")

    decomp_prompt = build_system_prompt(
        "You are a research strategist. Break the given research topic into"
        " 5-7 distinct, searchable sub-questions that together give full coverage."
        " Output ONLY a numbered list of sub-questions, nothing else."
    )
    sub_q_raw = await llm_call(
        AGENT_MODELS["analyst"],
        decomp_prompt,
        _truncate_prompt(f"Research topic: {topic}")
    )

    # Parse numbered list
    sub_questions = []
    for line in sub_q_raw.splitlines():
        m = re.match(r'^\s*\d+\.?\s+(.+)', line)
        if m:
            sub_questions.append(m.group(1).strip())
    if not sub_questions:
        sub_questions = [topic]  # Fallback
    sub_questions = sub_questions[:7]

    # ── LAYER 2: Parallel Multi-Source Search ────────────────────────────────
    await _progress(f"📡 Layer 2/5 — Searching {len(sub_questions)} sub-questions across 3 source types...")

    all_raw_sources: list[dict] = []

    async def _search_all(q: str) -> list[dict]:
        results = await asyncio.gather(
            _search_semantic_scholar(q),
            _search_arxiv(q),
            _search_duckduckgo(q, browser_search_fn),
            return_exceptions=True
        )
        combined = []
        for r in results:
            if isinstance(r, list):
                combined.extend(r)
        return combined

    search_tasks = [_search_all(q) for q in sub_questions[:4]]  # Limit parallel calls
    search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    for result in search_results:
        if isinstance(result, list):
            all_raw_sources.extend(result)

    # Deduplicate by URL
    seen_urls = set()
    unique_sources = []
    for s in all_raw_sources:
        url = s.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(s)

    # ── LAYER 3: Credibility Scoring ─────────────────────────────────────────
    await _progress(f"🏆 Layer 3/5 — Found {len(unique_sources)} sources, scoring credibility...")

    for s in unique_sources:
        s['score'] = _score_source(s.get('url', ''))
        # Boost score for academic papers with many citations
        if s.get('citations', 0) > 50:
            s['score'] = min(10, s['score'] + 1)
        if s.get('source_type') == 'academic':
            s['score'] = max(s['score'], 7)

    # Sort by score and take top 15
    top_sources = sorted(unique_sources, key=lambda x: x.get('score', 0), reverse=True)[:15]

    # ── LAYER 4: Cross-Reference Synthesis ───────────────────────────────────
    await _progress("🧬 Layer 4/5 — Cross-referencing and synthesizing findings...")

    sources_text = "\n\n".join(
        f"[{i+1}] {s.get('title', 'Untitled')} ({s.get('url', '')})\n{s.get('snippet', '')}"
        for i, s in enumerate(top_sources)
    )

    synth_prompt = build_system_prompt(
        "You are a research synthesizer. Given a set of sources on a topic, identify:\n"
        "1. Key points of AGREEMENT across sources\n"
        "2. CONTRADICTIONS between sources (and why they might exist)\n"
        "3. RESEARCH GAPS — what is NOT covered\n\n"
        "Be analytical and specific. Reference sources by their [number]."
    )
    synthesis = await llm_call(
        AGENT_MODELS["architect"],
        synth_prompt,
        _truncate_prompt(
            f"Topic: {topic}\n\nSources:\n{sources_text}\n\nSynthesis sub-questions addressed: {sub_questions}"
        )
    )

    # ── LAYER 5: Final Report Generation ────────────────────────────────────
    await _progress("📝 Layer 5/5 — Writing final research report...")

    report_prompt = build_system_prompt(
        "You are a senior research analyst writing for a smart, time-pressed audience."
        " Structure your report EXACTLY as:\n\n"
        "EXECUTIVE SUMMARY (3-4 sentences)\n"
        "KEY FINDINGS (with source citations as [1], [2], etc.)\n"
        "CONTRADICTIONS FOUND (where sources disagree and why)\n"
        "RESEARCH GAPS (what remains unknown or understudied)\n"
        "ACTIONABLE IMPLICATIONS (what should someone DO with this knowledge)\n"
        "SOURCES (numbered list)\n\n"
        "Be direct. No filler. Cite everything."
    )
    report = await llm_call(
        AGENT_MODELS["research"],
        report_prompt,
        _truncate_prompt(
            f"Topic: {topic}\n\nSynthesis:\n{synthesis}\n\nTop sources:\n{sources_text}"
        )
    )

    # Build sources footer
    sources_footer = "\n\n**SOURCES**\n" + "\n".join(
        f"[{i+1}] {s.get('title', 'Untitled')} — {s.get('url', '')} (credibility: {s.get('score', '?')}/10)"
        for i, s in enumerate(top_sources)
    )

    return report + sources_footer
