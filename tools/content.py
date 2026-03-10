"""content.py — Social media content & brand monitoring for Legion.

Draft posts (LinkedIn, X/Twitter), monitor brand mentions,
RSS-to-post pipeline.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def draft_linkedin_post(topic: str, tone: str = "professional") -> str:
    """Generate a LinkedIn post using marketer agent."""
    from llm_client import chat

    prompt = (
        f"Write a LinkedIn post about: {topic}\n\n"
        f"Tone: {tone}\n"
        "Requirements:\n"
        "- No markdown formatting (LinkedIn uses plain text)\n"
        "- Use paragraph breaks for readability\n"
        "- Include a hook in the first line\n"
        "- Add relevant hashtags at the end (3-5)\n"
        "- Keep it under 1300 characters\n"
        "- Be authentic and value-driven, not salesy\n"
    )
    result, _ = await chat(prompt, agent_key="general")
    return result


async def draft_tweet(topic: str, thread: bool = False) -> str:
    """Generate X/Twitter post(s)."""
    from llm_client import chat

    if thread:
        prompt = (
            f"Write a 5-tweet thread about: {topic}\n\n"
            "Requirements:\n"
            "- First tweet hooks the reader\n"
            "- Each tweet is under 280 characters\n"
            "- Number them 1/5, 2/5, etc.\n"
            "- Last tweet has a CTA or takeaway\n"
            "- No hashtags except in the last tweet\n"
        )
    else:
        prompt = (
            f"Write a single tweet about: {topic}\n\n"
            "Requirements:\n"
            "- Under 280 characters\n"
            "- Punchy, engaging\n"
            "- 1-2 relevant hashtags\n"
        )
    result, _ = await chat(prompt, agent_key="general")
    return result


async def monitor_brand(keywords: list[str], platforms: list[str] | None = None) -> str:
    """Search Reddit and HN for keyword mentions."""
    platforms = platforms or ["reddit", "hackernews"]
    results = []

    for keyword in keywords:
        # Reddit
        if "reddit" in platforms:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://www.reddit.com/search.json?q={keyword}&sort=new&limit=5"
                    headers = {"User-Agent": "LegionBot/1.0"}
                    async with session.get(
                        url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            posts = data.get("data", {}).get("children", [])
                            for post in posts[:3]:
                                pd = post.get("data", {})
                                title = pd.get("title", "")[:80]
                                sub = pd.get("subreddit", "")
                                score = pd.get("score", 0)
                                results.append(
                                    f"  Reddit r/{sub}: {title} (score: {score})"
                                )
            except Exception as e:
                results.append(f"  Reddit: error ({e})")

        # Hacker News
        if "hackernews" in platforms:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://hn.algolia.com/api/v1/search_by_date?query={keyword}&tags=story"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            hits = data.get("hits", [])
                            for hit in hits[:3]:
                                title = hit.get("title", "")[:80]
                                points = hit.get("points", 0)
                                results.append(
                                    f"  HN: {title} ({points} points)"
                                )
            except Exception as e:
                results.append(f"  HN: error ({e})")

    if not results:
        return f"No mentions found for: {', '.join(keywords)}"

    header = f"Brand monitor: {', '.join(keywords)}\n"
    return header + "\n".join(results)


async def rss_to_post(rss_url: str, platform: str = "linkedin") -> str:
    """Fetch latest RSS item, draft a platform-appropriate post."""
    from tools.briefing import _fetch_rss
    from llm_client import chat

    items = await _fetch_rss(rss_url, max_items=1)
    if not items:
        return "No RSS items found."

    item = items[0]
    title = item.get("title", "Unknown")

    prompt = (
        f"Create a {platform} post sharing this article:\n"
        f"Title: {title}\n\n"
        f"Add your professional take and commentary. "
        f"Keep it authentic and value-driven."
    )
    result, _ = await chat(prompt, agent_key="general")
    return f"Source: {title}\n\n{result}"
