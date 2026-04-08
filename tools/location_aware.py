"""Location intelligence — restaurant/hotel recommendations, weather.

Uses Google Places API and OpenWeatherMap for real-time local data.
Bashara's home base is Koto City, Tokyo, Japan (Asia/Tokyo timezone).

Falls back to tools/location_advisor.py (web-search + LLM based) when
API keys are not configured — so this always returns something useful.

Required env vars (optional — falls back gracefully without them):
  GOOGLE_PLACES_API_KEY    — Google Cloud Console, enable Places API
  OPENWEATHER_API_KEY      — openweathermap.org free tier
"""
from __future__ import annotations

import logging
import os
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

BASHARA_HOME: dict[str, Any] = {
    "lat": 35.6762,
    "lng": 139.7166,
    "name": "Koto City, Tokyo",
}


async def search_nearby_places(
    query: str,
    location: dict[str, Any] | None = None,
    radius_meters: int = 2000,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Search nearby places using Google Places API.

    Falls back to tools/location_advisor.py if Google API key is not set.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        return await _fallback_location_search(query, location)

    loc = location or BASHARA_HOME
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{loc['lat']},{loc['lng']}",
        "radius": radius_meters,
        "keyword": query,
        "key": api_key,
        "language": "en",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                places = data.get("results", [])[:limit]
                return [
                    {
                        "name": p.get("name", ""),
                        "rating": p.get("rating"),
                        "address": p.get("vicinity", ""),
                        "open_now": p.get("opening_hours", {}).get("open_now"),
                        "price_level": p.get("price_level"),
                        "types": p.get("types", [])[:3],
                        "source": "google_places",
                    }
                    for p in places
                ]
    except Exception as exc:
        logger.warning("[LocationAware] Google Places failed: %s — using fallback", exc)
        return await _fallback_location_search(query, location)


async def get_weather(city: str = "Tokyo") -> dict[str, Any]:
    """
    Get current weather using OpenWeatherMap free tier.
    Returns dict with city, temp_c, description, humidity, wind_kph.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return {"error": "OPENWEATHER_API_KEY not set — add to .env"}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "en"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                data = await resp.json()
                weather_list = data.get("weather", [{}])
                description = weather_list[0].get("description", "unknown") if weather_list else "unknown"
                return {
                    "city": data.get("name", city),
                    "temp_c": data.get("main", {}).get("temp"),
                    "feels_like_c": data.get("main", {}).get("feels_like"),
                    "description": description,
                    "humidity": data.get("main", {}).get("humidity"),
                    "wind_kph": round((data.get("wind", {}).get("speed", 0)) * 3.6, 1),
                    "source": "openweathermap",
                }
    except Exception as exc:
        logger.warning("[LocationAware] OpenWeather failed: %s", exc)
        return {"error": str(exc), "city": city}


def format_places_for_prompt(places: list[dict[str, Any]]) -> str:
    """
    Format a places list into a system-prompt-friendly block.
    Injected into the prompt before asking the LLM for a recommendation.
    """
    if not places:
        return ""
    # Handle error-only results
    if len(places) == 1 and "error" in places[0]:
        return ""

    lines = ["[Nearby Places from Google Maps — use these in your recommendation:]"]
    for p in places:
        rating = p.get("rating")
        price_raw = p.get("price_level")
        price = "¥" * price_raw if price_raw else "price unknown"
        open_status = (
            "open now" if p.get("open_now") is True
            else "closed" if p.get("open_now") is False
            else "hours unknown"
        )
        rating_str = f"⭐{rating}" if rating else "no rating"
        lines.append(
            f"- {p.get('name', 'Unknown')} {rating_str} | "
            f"{p.get('address', '')} | {price} | {open_status}"
        )
    return "\n".join(lines)


def format_weather_for_prompt(weather: dict[str, Any]) -> str:
    """Format weather data into a system-prompt-friendly block."""
    if "error" in weather:
        return ""
    return (
        f"[Current Weather in {weather.get('city', 'Tokyo')}]: "
        f"{weather.get('temp_c', '?')}°C, feels like {weather.get('feels_like_c', '?')}°C, "
        f"{weather.get('description', '')}, "
        f"humidity {weather.get('humidity', '?')}%, "
        f"wind {weather.get('wind_kph', '?')} km/h"
    )


# ── Fallback: web-search based (no API key needed) ────────────────────────────

async def _fallback_location_search(
    query: str,
    location: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fallback to the existing tools/location_advisor.py which uses
    web search + LLM synthesis when Google Places API key isn't set.
    Returns a single entry with the text result.
    """
    try:
        from tools.location_advisor import LocationAdvisor
        loc_name = (location or BASHARA_HOME).get("name", "Koto City, Tokyo")
        advisor = LocationAdvisor()
        result = await advisor.recommend_places(query, loc_name)
        return [{"name": "Web Search Result", "address": loc_name, "detail": result, "source": "web_search"}]
    except Exception as exc:
        logger.warning("[LocationAware] Fallback location search failed: %s", exc)
        return [{"error": str(exc)}]
