---
title: ADR — Intent Router Test Coverage + Pattern Fix
type: decision
status: active
tags: [legion, intent-router, testing, patterns]
created: 2026-04-13
updated: 2026-04-13
summary: Added test coverage for all 8 previously untested intents (MEMORY_STORE, EMAIL_WRITE, DATABASE_AUDIT, WEATHER_QUERY, LOCATION_QUERY, DATA_ANALYSIS, API_CALL, SELF_UPGRADE). All 23 intents now tested. Also fixed WEB_RESEARCH pattern conflict where \bwhat is\b was too generic and caused WEATHER_QUERY ("what is the weather...") to misclassify.
wikilinks:
  - [[architecture/legion-module-map]]
confidence: high
source: loop-5-implementation
project: legion
---

## Decision

1. Added test coverage for all 8 missing intent types in `tests/test_intent_router.py`
2. Fixed pattern conflict in `core/intent_router.py`

## Tests Added

| Intent | Test Query |
|--------|-----------|
| MEMORY_STORE | "remember that I prefer dark mode" |
| EMAIL_WRITE | "send an email to john@example.com saying hello" |
| DATABASE_AUDIT | "check the supabase users table for duplicates" |
| WEATHER_QUERY | "what's the weather like in Tokyo today?" |
| LOCATION_QUERY | "find good ramen restaurants near Shibuya" |
| DATA_ANALYSIS | "run a data analysis on this CSV file" |
| API_CALL | "call the GitHub API to list my repos" |
| SELF_UPGRADE | "check what changed in the latest commit" |

## Pattern Fix

Removed `\bwhat is\b` from `Intent.WEB_RESEARCH` patterns because it was too generic and caused false matches:
- "what is the weather in Tokyo today?" was incorrectly classified as `WEB_RESEARCH` instead of `WEATHER_QUERY`
- Root cause: `\bwhat is\b` matched before the more specific `\bweather\b` pattern due to dict iteration order tie-breaking

## Patterns Added

- `Intent.SELF_UPGRADE`: added `r"\blatest.*commit\b"` to match "latest commit" queries
- `Intent.DATA_ANALYSIS`: added `r"\bdata analysis\b"` to match "data analysis" queries

## Test Results

Before: 383 tests passing
After: 391 tests passing (+8 new intent tests)
All 29 intent_router tests pass.

## Files Changed

- `tests/test_intent_router.py` — +40 lines (8 new tests)
- `core/intent_router.py` — +2 new patterns, -1 overly generic pattern
