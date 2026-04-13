---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/decisions/ADR-091-weather-handler-session-bug.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.733687"
}
---

# ADR-091: Weather Handler Session Lifecycle Bug

**Date:** 2026-04-12  
**Status:** ACCEPTED - FIXED  
**Type:** Bugfix

---

## Context

The bot became unresponsive after issuing a weather command. Investigation revealed a critical session lifecycle bug in the `_weather_handler` function.

## Root Cause

At lines 37-53, the `aiohttp.ClientSession` is created and used for the geocoding request, but the `async with` block closes the session immediately after the first request completes:

```python
async with aiohttp.ClientSession() as session:
    async with session.get(geo_url, ...) as resp:  # Session closes here at line 41
        geo_data = await resp.json()

# Session is now CLOSED

async with session.get(weather_url, ...) as resp:  # LINE 53 - Tries to use closed session
    weather_data = await resp.json()               # HANGS INDEFINITELY
```

The second `session.get()` call on the closed session never completes, causing the bot to hang indefinitely.

## Fix Applied

Both API calls are now inside the same `async with session:` block:

```python
async with aiohttp.ClientSession() as session:
    # Geocoding
    async with session.get(geo_url, ...) as resp:
        geo_data = await resp.json()
    
    # Weather - inside same session block
    async with session.get(weather_url, ...) as resp:
        weather_data = await resp.json()
```

## Location Extraction

The location extraction logic (Tokyo vs Jakarta default) is working correctly:
- Default: `"Tokyo"` (line 22)
- Keywords removed: weather, cuaca, forecast, temperature, how is, what is the, in, at, for, location, city
- Remaining text used as location

## Related Files

- `core/skills/builtin/productivity.py` - Lines 37-53

## Review Status

Documented in: `.wiki/issues/review-2026-04-12-weather-handler-unresponsiveness.md`
