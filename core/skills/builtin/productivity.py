"""Productivity skills: weather, translation, timer."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _weather_handler(text: str) -> str:
    """Get weather for a location using OpenWeatherMap."""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        return "❌ OpenWeatherMap API key not configured (OPENWEATHERMAP_API_KEY)"

    # Extract location
    location = "Tokyo"
    # Remove weather-related keywords to get location
    loc_text = text
    for kw in ["weather", "cuaca", "forecast", "temperature", "how is", "what is the"]:
        loc_text = re.sub(rf"\b{kw}\b", "", loc_text, flags=re.IGNORECASE).strip()
    loc_text = re.sub(r"\b(in|at|for|location|city)\b", "", loc_text, flags=re.IGNORECASE).strip()
    if loc_text:
        location = loc_text.strip()

    try:
        import aiohttp

        # Get coordinates first
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": location, "limit": 1, "appid": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(geo_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return f"❌ Geocoding failed: {resp.status}"
                geo_data = await resp.json()

            if not geo_data:
                return f"❌ Location not found: {location}"

            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
            city_name = geo_data[0].get("name", location)

            # Get weather
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
            async with session.get(weather_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return f"❌ Weather API error: {resp.status}"
                weather_data = await resp.json()

        temp = weather_data.get("main", {}).get("temp", "?")
        feels_like = weather_data.get("main", {}).get("feels_like", "?")
        humidity = weather_data.get("main", {}).get("humidity", "?")
        description = weather_data.get("weather", [{}])[0].get("description", "unknown")
        wind_speed = weather_data.get("wind", {}).get("speed", "?")

        return (
            f"🌤️ Weather for {city_name}:\n"
            f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"Condition: {description.capitalize()}\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind_speed} m/s"
        )
    except Exception as exc:
        return f"❌ Weather lookup failed: {exc}"


async def _translate_handler(text: str) -> str:
    """Translate text between languages."""
    # Extract target language and text
    target_lang_match = re.search(r"(?:to|in|in Bahasa|into)\s+(\w+)", text, re.IGNORECASE)
    if not target_lang_match:
        return "Please specify a target language (e.g., 'translate to Japanese')."

    target_lang = target_lang_match.group(1).lower()
    lang_map = {
        "english": "English",
        "japanese": "Japanese",
        "indonesian": "Indonesian",
        "bahasa": "Indonesian",
        "spanish": "Spanish",
        "french": "French",
        "german": "German",
        "chinese": "Chinese",
        "korean": "Korean",
        "russian": "Russian",
    }
    lang_code_map = {
        "english": "en",
        "japanese": "ja",
        "indonesian": "id",
        "bahasa": "id",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "chinese": "zh",
        "korean": "ko",
        "russian": "ru",
    }
    target_lang_full = lang_map.get(target_lang, target_lang.capitalize())
    lang_code = lang_code_map.get(target_lang, "en")

    # Extract the text to translate
    content = text
    for kw in ["translate", "terjemahkan", "translation"]:
        content = re.sub(rf"\b{kw}\b", "", content, flags=re.IGNORECASE).strip()
    content = re.sub(r"(?:to|in|in Bahasa|into)\s+\w+", "", content, flags=re.IGNORECASE).strip()

    if not content:
        return "Please provide text to translate."
    if len(content) > 1000:
        content = content[:1000] + "..."

    try:
        from llm_client import call_llm

        prompt = f"Translate the following text to {target_lang_full}. Return ONLY the translation, nothing else.\n\nText: {content}"
        translation = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="minimax/ai-01",
            max_tokens=500,
            temperature=0.3,
        )
        if isinstance(translation, dict):
            translation = ""
        return f"🌐 Translation ({lang_code.upper()}):\n{translation}"
    except Exception as exc:
        return f"❌ Translation failed: {exc}"


async def _timer_handler(text: str) -> str:
    """Set a timer with notification using the real timer skill."""
    try:
        from core.skills.timer import handle_timer_message, set_bot
        import handlers.shared as _shared

        # Ensure bot is set for timer notifications
        if _shared._bot is not None:
            set_bot(_shared._bot)

        # Default user_id for non-interactive contexts
        user_id = _shared.ALLOWED_USER_ID if hasattr(_shared, "ALLOWED_USER_ID") else 0

        return await handle_timer_message(text, user_id)
    except Exception as e:
        return f"❌ Timer error: {e}"


def _register_productivity_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="weather",
            description="Get current weather and forecast for a location",
            trigger_keywords=["weather", "cuaca", "forecast", "temperature", "rain"],
            handler=_weather_handler,
            required_env_keys=["OPENWEATHERMAP_API_KEY"],
            category="productivity",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="translate",
            description="Translate text between languages",
            trigger_keywords=["translate", "terjemahkan", "translation", "to english", "to japanese", "ke bahasa"],
            handler=_translate_handler,
            required_env_keys=[],
            category="productivity",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="timer",
            description="Set a countdown timer with notification",
            trigger_keywords=["timer", "set timer", "countdown", "alarm", "reminder", "ingatkan", "bunyi"],
            handler=_timer_handler,
            required_env_keys=[],
            category="productivity",
        )
    )


_register_productivity_skills()
