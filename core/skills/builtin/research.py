"""Research skills using Brave Search, arxiv, and news sources."""

from __future__ import annotations

import logging
import os
import re

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _web_search_handler(text: str) -> str:
    """Search the web using Brave Search API."""
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
    if not api_key:
        return "❌ Brave Search API key not configured (BRAVE_SEARCH_API_KEY)"

    # Extract query - remove trigger keywords
    query = text
    for kw in ["search", "google", "web search", "search for", "look up", "cari"]:
        query = re.sub(rf"\b{kw}\b", "", query, flags=re.IGNORECASE).strip()
    if not query:
        return "Please provide a search query."

    try:
        import aiohttp

        headers = {"X-Subscription-Token": api_key}
        params = {"q": query, "count": "10"}
        async with aiohttp.ClientSession() as session, session.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                return f"❌ Brave Search API error: {resp.status}"
            data = await resp.json()

        results = data.get("web", {}).get("results", [])
        if not results:
            return f"No results found for: {query}"

        lines = [f"🔍 Search results for: {query}\n"]
        for i, r in enumerate(results[:8], 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            desc = r.get("description", "")[:150]
            lines.append(f"{i}. {title}\n   {desc}...\n   {url}\n")
        return "\n".join(lines)
    except Exception as exc:
        return f"❌ Search failed: {exc}"


async def _arxiv_search_handler(text: str) -> str:
    """Search arXiv for academic papers."""
    query = text
    for kw in ["arxiv", "paper", "paper search", "academic search"]:
        query = re.sub(rf"\b{kw}\b", "", query, flags=re.IGNORECASE).strip()
    if not query:
        return "Please provide an arXiv search query."

    try:
        import aiohttp

        url = "http://export.arxiv.org/api/query"
        params = {"search_query": f"all:{query}", "start": 0, "max_results": 5, "sortBy": "relevance"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return f"❌ arXiv API error: {resp.status}"
                text_content = await resp.text()

        # Parse basic XML response
        entries = re.findall(r"<entry>(.*?)</entry>", text_content, re.DOTALL)
        if not entries:
            return f"No papers found for: {query}"

        lines = [f"📚 arXiv papers for: {query}\n"]
        for entry in entries[:5]:
            title_match = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
            title = title_match.group(1).replace("\n", " ").strip() if title_match else "No title"
            id_match = re.search(r"<id>(.*?)</id>", entry)
            paper_id = id_match.group(1).split("/")[-1] if id_match else "N/A"
            summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
            summary = summary_match.group(1).replace("\n", " ").strip()[:200] if summary_match else ""
            lines.append(f"• {title}\n  ID: {paper_id}\n  {summary}...\n")
        return "\n".join(lines)
    except Exception as exc:
        return f"❌ arXiv search failed: {exc}"


async def _summarize_url_handler(text: str) -> str:
    """Summarize content from a URL using LLM."""
    url_match = re.search(r"https?://[^\s'\"]+", text)
    if not url_match:
        return "No URL found. Please provide a URL to summarize."
    url = url_match.group(0).rstrip(".,)")

    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            if not result or not result.get("markdown"):  # type: ignore[reportAttributeAccessIssue]
                return f"⚠️ Could not extract content from: {url}"
            content = result["markdown"][:4000]  # type: ignore[reportIndexIssue]
    except Exception as exc:
        return f"❌ Failed to fetch URL: {exc}"

    try:
        from llm_client import call_llm

        prompt = f"Summarize the following content concisely:\n\n{content}"
        summary = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="minimax/ai-01",
            max_tokens=300,
            temperature=0.3,
        )
        if isinstance(summary, dict):
            summary = ""
        return f"📄 Summary of {url}:\n\n{summary}"
    except Exception as exc:
        return f"❌ LLM summarization failed: {exc}"


async def _hacker_news_handler(text: str) -> str:
    """Fetch top Hacker News stories."""
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session, session.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return f"❌ Hacker News API error: {resp.status}"
            ids = await resp.json()

        top_ids = ids[:10]
        stories = []
        for story_id in top_ids:
            async with session.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    story = await resp.json()
                    if story:
                        title = story.get("title", "No title")
                        score = story.get("score", 0)
                        url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                        stories.append(f"• {title} (↑{score})\n  {url}")

        if not stories:
            return "No stories retrieved from Hacker News."
        return "🔥 Top Hacker News Stories:\n\n" + "\n".join(stories)
    except Exception as exc:
        return f"❌ Hacker News fetch failed: {exc}"


def _register_research_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="web_search",
            description="Search the web using Brave Search API",
            trigger_keywords=["search", "google", "web search", "search for", "look up", "cari", "cari tahu"],
            handler=_web_search_handler,
            required_env_keys=["BRAVE_SEARCH_API_KEY"],
            category="research",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="arxiv_search",
            description="Search arXiv for academic papers",
            trigger_keywords=["arxiv", "paper", "academic", "research paper", "scientific paper"],
            handler=_arxiv_search_handler,
            required_env_keys=[],
            category="research",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="summarize_url",
            description="Summarize content from a URL using LLM",
            trigger_keywords=["summarize", "summary", "tldr", "quick summary", "url summary"],
            handler=_summarize_url_handler,
            required_env_keys=[],
            category="research",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="hacker_news",
            description="Fetch top stories from Hacker News",
            trigger_keywords=["hacker news", "hn", "hackernews", "tech news", "news"],
            handler=_hacker_news_handler,
            required_env_keys=[],
            category="research",
        )
    )


_register_research_skills()
