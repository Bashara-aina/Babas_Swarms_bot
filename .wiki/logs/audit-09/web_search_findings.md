---
title: Web Search Findings
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Generated: 2026-04-12'
wikilinks: []
confidence: medium
source: research
---
# Web Search Skill Audit — LEGION AUDIT 09
> Generated: 2026-04-12

## Interface Verification: `skills/web_search.py`

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Class name | `WebSearch` | `WebSearch` (line 99) | ✅ PASS |
| Public async method | `search()` | `async def search(self, query: str, num_results: int = 5) -> list[dict[str, Any]]` (line 102) | ✅ PASS |
| Return type | `list[dict]` | `list[dict[str, Any]]` | ✅ PASS |
| `format_for_telegram()` exists | Yes | Yes (line 119, synchronous method) | ✅ PASS |
| Returns `[]` on failure | Yes | Both `_duckduckgo_search()` (line 62) and `_serpapi_search()` (line 96) return `[]` on exception | ✅ PASS |

## ⚠️ VIOLATION: Timeout Specification

| Location | Current Value | Expected Value | Severity |
|----------|---------------|-----------------|----------|
| `_duckduckgo_search()` line 31 | `aiohttp.ClientTimeout(total=10)` | `total=8` | **⚠️ FLAG** |

**Spec states timeout should be 8s, but DuckDuckGo search uses 10s.**

## Additional Findings

1. **SerpAPI timeout** is 15s (line 78) — no spec violation (SerpAPI is fallback, larger payloads)
2. **Error handling**: Both search functions use `except Exception` and log warning, return `[]` — compliant with "no silent failures"
3. **DuckDuckGo status check**: Returns `[]` if `resp.status != 200` (line 32-33) — correct
4. **SerpAPI status check**: Returns `[]` if `resp.status != 200` (line 80-81) — correct

## Verdict

- **Interface**: ✅ Fully compliant
- **Error handling**: ✅ Returns `[]` on failure (not silent)
- **Timeout**: ⚠️ 10s instead of 8s spec for DuckDuckGo
