"""Geo-intelligence skill — location-aware restaurant/hotel/nearby recommendations.

Uses web search to find places near a location, formatted for Telegram HTML.
Designed for travelers or finding amenities in a given city.

Usage:
    gi = GeoIntelligence()
    msg = await gi.recommend_restaurants("Shinjuku, Tokyo", cuisine="ramen")
    msg = await gi.nearby_places("Ueno, Tokyo", category="coffee shop")
"""

from __future__ import annotations

import logging
from typing import Any

from skills.web_search import WebSearch

logger = logging.getLogger(__name__)


class GeoIntelligence:
    """Location-aware place recommendations via web search."""

    def __init__(self) -> None:
        self._ws = WebSearch()

    async def recommend_restaurants(
        self,
        location: str,
        cuisine: str = "",
        num_results: int = 5,
    ) -> str:
        """
        Recommend restaurants in `location`.

        Args:
            location: City/neighborhood (e.g. "Shinjuku, Tokyo")
            cuisine: Optional cuisine type (e.g. "ramen", "italian")
            num_results: Max number of results (default 5)

        Returns:
            Telegram HTML formatted message.
        """
        query = f"best {cuisine} restaurants {location}" if cuisine else f"best restaurants {location}"
        results = await self._ws.search(query, num_results)
        return self._format_places("🍽️ <b>Restaurant Recommendations</b>", results, location)

    async def recommend_hotels(
        self,
        location: str,
        budget: str = "",
        num_results: int = 5,
    ) -> str:
        """
        Recommend hotels in `location`.

        Args:
            location: City/neighborhood
            budget: Budget level (e.g. "budget", "luxury", "mid-range")
            num_results: Max number of results

        Returns:
            Telegram HTML formatted message.
        """
        query = f"best {budget} hotels {location}" if budget else f"best hotels {location}"
        results = await self._ws.search(query, num_results)
        return self._format_places("🏨 <b>Hotel Recommendations</b>", results, location)

    async def nearby_places(
        self,
        location: str,
        category: str = "",
        num_results: int = 5,
    ) -> str:
        """
        Find nearby places of interest in `location`.

        Args:
            location: City/neighborhood
            category: Type of place (e.g. "coffee shop", "park", "coworking space")
            num_results: Max number of results

        Returns:
            Telegram HTML formatted message.
        """
        query = f"best {category} near {location}" if category else f"things to do in {location}"
        results = await self._ws.search(query, num_results)
        return self._format_places(f"📍 <b>Nearby: {category or 'Places of Interest'}</b>", results, location)

    def _format_places(
        self,
        header: str,
        results: list[dict[str, Any]],
        location: str,
    ) -> str:
        """Format place results as Telegram HTML."""
        if not results:
            return f"{header}\nNo results found for {location}."

        lines = [f"{header} in <b>{location}</b>\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "Unknown")[:80]
            url = r.get("url", "")
            snippet = r.get("snippet", "")[:140]
            if url:
                lines.append(f"{i}. <a href='{url}'>{title}</a>")
            else:
                lines.append(f"{i}. {title}")
            if snippet:
                lines.append(f"   {snippet}")
            lines.append("")
        lines.append(f"<i>Results via web search · {location}</i>")
        return "\n".join(lines)
