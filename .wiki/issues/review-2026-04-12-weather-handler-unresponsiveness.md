---
title: Review 2026 04 12 Weather Handler Unresponsiveness
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: 'The `_weather_handler` in `core/skills/builtin/productivity.py` contains
  a **critical session lifecycle bug** at lines 37-53:'
wikilinks: []
confidence: medium
source: research
---
The `_weather_handler` in `core/skills/builtin/productivity.py` contains a **critical session lifecycle bug** at lines 37-53:

```python
async with aiohttp.ClientSession() as session:          # Line 37 - session created
    async with session.get(geo_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status != 200:
            return f"❌ Geocoding failed: {resp.status}"
        geo_data = await resp.json()                   # Line 41 - session closed here!

if not geo_data:
    return f"❌ Location not found: {location}"

lat = geo_data[0]["lat"]
lon = geo_data[0]["lon"]

# Line 53 - session is ALREADY CLOSED, attempting to use it causes hang
async with session.get(weather_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
```

**Problem:** The `async with session.get(...)` block at line 37 creates and immediately closes the session at line 41 when the first `async with` block exits. The second `async with session.get(...)` at line 53 tries to reuse the closed `session` variable, which causes the bot to hang indefinitely.
---


## ❌ Blockers

1. **Session Use-After-Close (Lines 37-53):** `session` is closed after the geocoding request but reused for the weather request. This is an infinite hang, not a proper error.

2. **Blocking Hang:** Unlike a proper error that returns quickly, this bug causes the bot to hang indefinitely because `session.get()` on a closed session never completes.

---

## ✅ Passed

- Location extraction logic works correctly (Tokyo vs Jakarta parsing)
- Async/await structure is correct
- Timeout handling is proper
- Error messages are descriptive
- No hardcoded API keys

---

## ⚠️ Warnings

- No test exists for weather handler with mocked API responses
- The `aiohttp` import is done inside the try block (minor style issue)

---

## Required Fix

The weather handler must keep the session open for both API calls:

```python
async with aiohttp.ClientSession() as session:
    # Geocoding
    async with session.get(geo_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status != 200:
            return f"❌ Geocoding failed: {resp.status}"
        geo_data = await resp.json()
    
    if not geo_data:
        return f"❌ Location not found: {location}"
    
    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]
    city_name = geo_data[0].get("name", location)
    
    # Weather - MUST be inside same session block
    async with session.get(weather_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status != 200:
            return f"❌ Weather API error: {resp.status}"
        weather_data = await resp.json()
```

---

## Recommendation

**BLOCK MERGE** until the session lifecycle bug is fixed. The current code will cause the bot to hang indefinitely after any weather command.
