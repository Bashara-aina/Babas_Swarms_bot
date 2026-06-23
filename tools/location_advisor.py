"""Location-aware recommendations using UserProfile.location + live web search.

When the user asks "recommend a restaurant near home" or "where should I eat
in Koto City?", this module:
1. Pulls their location from UserProfile (no need to repeat it every time)
2. Builds a location-aware search query
3. Uses web_browser.deep_research() to gather live results
4. Returns a formatted Telegram HTML response

No external APIs required — uses Playwright web scraping.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Category → search modifiers
_CATEGORY_HINTS: dict[str, str] = {
    "restaurant": "best restaurants highly rated",
    "hotel": "best hotels to stay",
    "cafe": "cozy cafes specialty coffee",
    "event": "events happening things to do",
    "sightseeing": "tourist attractions must visit",
    "bar": "bars nightlife",
    "ramen": "best ramen shops",
    "sushi": "best sushi restaurants",
    "transport": "how to get around transport",
    "shopping": "shopping malls markets",
    "park": "parks nature outdoor",
    "hospital": "hospital clinic medical",
}


def _detect_category(query: str) -> str:
    """Infer category from the query text."""
    q = query.lower()
    for cat, _ in _CATEGORY_HINTS.items():
        if cat in q:
            return cat
    # Japanese food types
    if any(kw in q for kw in ["makan", "makanan", "eat", "food", "kuliner", "tempat makan"]):
        return "restaurant"
    if any(kw in q for kw in ["wisata", "jalan-jalan", "liburan", "vacation", "trip"]):
        return "sightseeing"
    if any(kw in q for kw in ["hotel", "menginap", "stay", "penginapan"]):
        return "hotel"
    return "restaurant"  # sensible default


def _build_search_query(user_query: str, location: str, category: str) -> str:
    """Build a precise location-aware search string."""
    hint = _CATEGORY_HINTS.get(category, "")
    # Strip the raw location to the core city name for cleaner searches
    city_match = re.match(r"([^,(]+)", location)
    city = city_match.group(1).strip() if city_match else location.split(",")[0].strip()
    return f"{hint} {category} near {city} {location} 2025"


class LocationAdvisor:
    """Provides location-aware recommendations using the user's stored location."""

    async def recommend_places(self, query: str, location: str) -> str:
        """Main entry point — returns a Telegram HTML formatted recommendation."""
        category = _detect_category(query)
        search_query = _build_search_query(query, location, category)

        logger.info("[LocationAdvisor] category=%s location=%s query=%s", category, location, search_query)

        # Gather live results via Playwright + LLM synthesis
        raw = await self._web_gather(search_query)
        if not raw:
            return (
                f"Couldn't find live results for <b>{category}</b> near <b>{location}</b>. "
                "Try asking me to search directly: <code>/research best ramen in Koto City</code>"
            )

        # Format via LLM for a clean, conversational response
        return await self._format_response(query, location, category, raw)

    async def get_local_info(self, query: str, location: str) -> str:
        """General local info — events, weather, transport, etc."""
        search_query = f"{query} {location} 2025"
        raw = await self._web_gather(search_query)
        if not raw:
            return f"Couldn't find local info for <b>{location}</b>. Try <code>/research {query}</code>"
        return await self._format_response(query, location, "general", raw)

    async def travel_advisor(self, destination: str, from_location: str) -> str:
        """Hotel/transport/itinerary recommendations for a trip."""
        search_query = f"travel guide {destination} from {from_location} hotels transport itinerary 2025"
        raw = await self._web_gather(search_query)
        if not raw:
            return f"Couldn't find travel info for <b>{destination}</b>."
        return await self._format_response(f"travel from {from_location} to {destination}", destination, "travel", raw)

    async def _web_gather(self, search_query: str, max_chars: int = 6000) -> str:
        """Scrape the web for results. Returns raw text for LLM processing."""
        try:
            from tools.web_browser import deep_research

            result = await deep_research(search_query, max_pages=5)
            return result[:max_chars] if result else ""
        except Exception as exc:
            logger.warning("[LocationAdvisor] web gather failed: %s", exc)
            # Fallback: try simple DuckDuckGo search
            try:
                from tools.web_browser import web_search

                results = await web_search(search_query)
                if results:
                    return "\n".join(str(r)[:500] for r in results[:5])
            except Exception as exc2:
                logger.warning("[LocationAdvisor] fallback search failed: %s", exc2)
            return ""

    async def _format_response(
        self,
        query: str,
        location: str,
        category: str,
        raw_data: str,
    ) -> str:
        """Use LLM to format raw web results into a clean Telegram recommendation."""
        from llm_client import call_llm

        prompt = (
            f"You are Legion, Bashara's AI companion. He asked: '{query}'\n"
            f"His location: {location}\n"
            f"Category: {category}\n\n"
            f"Here's what the web says:\n{raw_data[:4000]}\n\n"
            "Write a helpful, friendly recommendation in Telegram HTML format. "
            "Include: specific place names, rough addresses or areas, why each is good. "
            "Keep it under 350 words. Use <b> for place names. "
            "If you can't find specific recommendations in the data, say so honestly "
            "and suggest how to find them."
        )
        try:
            return await call_llm(
                messages=[{"role": "user", "content": prompt}],
                model="minimax-coding-plan/MiniMax-M3",
                temperature=0.5,
                max_tokens=500,
            )
        except Exception as exc:
            logger.warning("[LocationAdvisor] LLM format failed: %s", exc)
            # Return raw truncated data as fallback
            return f"<b>Results for {category} near {location}:</b>\n\n{raw_data[:1500]}"
