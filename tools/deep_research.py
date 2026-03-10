"""
tools/deep_research.py

Perplexity-grade 5-layer deep research pipeline.

LAYER 1: Query decomposition into 5-8 sub-questions
LAYER 2: Parallel search across DuckDuckGo, Semantic Scholar, ArXiv
LAYER 3: Source credibility scoring (keep top 15)
LAYER 4: Cross-reference synthesis (agreements, contradictions, gaps)
LAYER 5: Final structured report with citations
"""
from __future__ import annotations
import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# Credibility scoring table
_CREDIBILITY_RULES: list[tuple] = [
    (r'arxiv\.org', 10),
    (r'semanticscholar\.org', 10),
    (r'pubmed\.ncbi\.nlm\.nih\.gov', 10),
    (r'nature\.com', 9),
    (r'science\.org', 9),
    (r'ieee\.org', 9),
    (r'acm\.org', 9),
    (r'\.gov', 8),
    (r'\.edu', 8),
    (r'springer\.com|wiley\.com|elsevier\.com', 7),
    (r'techcrunch|wired|mit\.edu|stanford\.edu', 7),
    (r'\.org', 5),
    (r'reddit\.com|news\.ycombinator', 3),
]


def _score_source(url: str) -> int:
    url_lower = url.lower()
    for pattern, score in _CREDIBILITY_RULES:
        if re.search(pattern, url_lower):
            return score
    return 4  # default web


async def _search_duckduckgo(session, query: str) -> list[dict]:
    """Search DuckDuckGo HTML and extract results."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        async with session.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            text = await resp.text()
        # Extract result links and snippets
        title_re = re.compile(r'class="result__a"[^>]*>([^<]+)<', re.DOTALL)
        url_re = re.compile(r'class="result__url"[^>]*>([^<]+)<', re.DOTALL)
        snippet_re = re.compile(r'class="result__snippet"[^>]*>([^<]+)<', re.DOTALL)
        titles = title_re.findall(text)[:10]
        urls = url_re.findall(text)[:10]
        snippets = snippet_re.findall(text)[:10]
        results = []
        for i in range(min(len(titles), len(urls))):
            snippet = snippets[i].strip() if i < len(snippets) else ""
            raw_url = urls[i].strip()
            if not raw_url.startswith('http'):
                raw_url = 'https://' + raw_url
            results.append({
                "title": titles[i].strip(),
                "url": raw_url,
                "snippet": snippet,
                "source_type": "web",
            })
        return results
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)
        return []


async def _search_semantic_scholar(session, query: str) -> list[dict]:
    """Search Semantic Scholar API."""
    try:
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search"
            f"?query={quote_plus(query)}&limit=5"
            f"&fields=title,authors,year,abstract,url,externalIds"
        )
        async with session.get(url, timeout=10) as resp:
            data = await resp.json()
        results = []
        for paper in data.get("data", []):
            paper_url = paper.get("url") or f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
            abstract = paper.get("abstract") or ""
            results.append({
                "title": paper.get("title", "Untitled"),
                "url": paper_url,
                "snippet": abstract[:300],
                "source_type": "academic",
                "year": paper.get("year"),
            })
        return results
    except Exception as e:
        logger.warning("Semantic Scholar search failed: %s", e)
        return []


async def _search_arxiv(session, query: str) -> list[dict]:
    """Search ArXiv API and parse XML."""
    try:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results=5"
        async with session.get(url, timeout=10) as resp:
            text = await resp.text()
        # Parse XML
        root = ET.fromstring(text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []
        for entry in root.findall('atom:entry', ns):
            title_el = entry.find('atom:title', ns)
            summary_el = entry.find('atom:summary', ns)
            link_el = entry.find('atom:id', ns)
            title = title_el.text.strip() if title_el is not None else "Untitled"
            summary = summary_el.text.strip()[:300] if summary_el is not None else ""
            link = link_el.text.strip() if link_el is not None else ""
            results.append({
                "title": title,
                "url": link,
                "snippet": summary,
                "source_type": "arxiv",
            })
        return results
    except Exception as e:
        logger.warning("ArXiv search failed: %s", e)
        return []


class DeepResearchPipeline:
    """5-layer Perplexity-grade research pipeline."""

    async def _call_llm(self, llm_client, prompt: str, agent: str = "analyst", temperature: float = 0.5) -> str:
        try:
            from agents import AGENT_MODELS
            model = AGENT_MODELS.get(agent, AGENT_MODELS["analyst"])
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm_client.complete(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=2048,
                )
            )
            return result.strip() if result else ""
        except Exception as e:
            logger.error("DeepResearch LLM error: %s", e)
            return ""

    async def _status(self, bot, chat_id, text: str):
        """Send a status update to Telegram."""
        if bot and chat_id:
            try:
                await bot.send_message(chat_id, text)
            except Exception as e:
                logger.warning("Status message failed: %s", e)

    async def run(self, query: str, llm_client, bot=None, chat_id: int = None) -> str:
        """
        Run the full 5-layer deep research pipeline.
        Returns a formatted research report string.
        """
        import aiohttp

        await self._status(bot, chat_id, "\ud83d\udd0d *Decomposing query into sub-questions...*")

        # LAYER 1: Query decomposition
        decomp_prompt = (
            f"Research topic: {query}\n\n"
            "Break this into 5-8 distinct, specific sub-questions that together "
            "would give a comprehensive understanding of the topic. "
            "Return ONLY a numbered list, one question per line."
        )
        decomp_raw = await self._call_llm(llm_client, decomp_prompt, "analyst", 0.4)
        sub_questions = _parse_numbered_questions(decomp_raw)
        if not sub_questions:
            sub_questions = [query]
        sub_questions = sub_questions[:6]  # cap at 6 for API sanity

        await self._status(bot, chat_id, f"\ud83d\udce1 *Searching academic papers, web, and ArXiv for {len(sub_questions)} sub-questions...*")

        # LAYER 2: Parallel web search for all sub-questions
        all_results: list[dict] = []
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for sq in sub_questions:
                    tasks.append(_search_duckduckgo(session, sq))
                    tasks.append(_search_semantic_scholar(session, sq))
                    tasks.append(_search_arxiv(session, sq))
                # Also search the main query on all sources
                tasks.append(_search_duckduckgo(session, query))
                tasks.append(_search_semantic_scholar(session, query))
                tasks.append(_search_arxiv(session, query))

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in batch_results:
                    if isinstance(res, list):
                        all_results.extend(res)
        except Exception as e:
            logger.error("Search layer failed: %s", e)
            all_results = []

        await self._status(bot, chat_id, f"\ud83c\udfc6 *Found {len(all_results)} sources, scoring credibility...*")

        # LAYER 3: Deduplicate and score
        seen_urls: set[str] = set()
        unique_results: list[dict] = []
        for r in all_results:
            url = r.get("url", "")
            if url and url not in seen_urls and r.get("title"):
                seen_urls.add(url)
                r["credibility"] = _score_source(url)
                unique_results.append(r)

        # Sort by credibility descending, keep top 15
        unique_results.sort(key=lambda x: x.get("credibility", 0), reverse=True)
        top_sources = unique_results[:15]

        await self._status(bot, chat_id, "\ud83e\uddec *Cross-referencing findings for contradictions and gaps...*")

        # LAYER 4: Cross-reference synthesis
        sources_text = "\n\n".join(
            f"[{i+1}] **{s['title']}** ({s.get('source_type', 'web')}, score={s.get('credibility', 0)})\n"
            f"URL: {s['url']}\n"
            f"Snippet: {s.get('snippet', '')[:200]}"
            for i, s in enumerate(top_sources)
        )
        synthesis_prompt = (
            f"Research topic: {query}\n\n"
            f"Here are the top {len(top_sources)} sources found:\n\n{sources_text}\n\n"
            "Analyze these sources and provide:\n"
            "1. KEY AGREEMENTS: What do multiple sources agree on?\n"
            "2. CONTRADICTIONS: Where do sources conflict and why might that be?\n"
            "3. RESEARCH GAPS: What important aspects are NOT covered by any source?\n\n"
            "Be analytical and specific. Reference source numbers [1], [2], etc."
        )
        synthesis = await self._call_llm(llm_client, synthesis_prompt, "architect", 0.5)

        await self._status(bot, chat_id, "\ud83d\udcdd *Writing final research report...*")

        # LAYER 5: Final report generation
        report_prompt = (
            f"Research topic: {query}\n\n"
            f"Source synthesis: {synthesis}\n\n"
            f"Available sources (with numbers for citation): {sources_text[:3000]}\n\n"
            "Write a comprehensive research report with these exact sections:\n"
            "**Executive Summary** (3-4 sentences)\n"
            "**Key Findings** (cite sources as [1], [2], etc.)\n"
            "**Contradictions Found** (where evidence conflicts)\n"
            "**Research Gaps** (what's missing)\n"
            "**Actionable Implications** (what should someone DO with this)\n\n"
            "Write like a brilliant analyst, not a textbook. Be direct and opinionated where warranted."
        )
        final_report = await self._call_llm(llm_client, report_prompt, "research", 0.6)

        # Append sources list
        sources_footer = "\n\n---\n**Sources**\n" + "\n".join(
            f"[{i+1}] [{s['title']}]({s['url']}) — {s.get('source_type', 'web').upper()}, credibility: {s.get('credibility', 0)}/10"
            for i, s in enumerate(top_sources)
        )

        return final_report + sources_footer


def _parse_numbered_questions(text: str) -> list[str]:
    pattern = re.compile(r'^\d+[.):]\s+(.+)', re.MULTILINE)
    return pattern.findall(text)
