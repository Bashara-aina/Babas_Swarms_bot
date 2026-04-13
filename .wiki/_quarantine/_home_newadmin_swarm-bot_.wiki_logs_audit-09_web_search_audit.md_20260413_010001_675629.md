---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/audit-09/web_search_audit.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.675650"
}
---

# Web Search Full Audit — LEGION AUDIT 09
> Generated: 2026-04-12

## Call Path Trace

```
User message with search query
        │
        ▼
IntentRouter or SkillRegistry
        │
        ▼
WebSearch.search(query, num_results=5)
        │
        ├──► _duckduckgo_search(query, num_results)
        │         │
        │         └──► aiohttp GET to DuckDuckGo API
        │                    │
        │                    ├──► resp.status != 200 → return []
        │                    ├──► Exception → return [] (line 62)
        │                    └──► Success → parse JSON, return results
        │
        └──► _serpapi_search(query, num_results) [fallback]
                  │
                  └──► aiohttp GET to SerpAPI
                             │
                             ├──► No SERPAPI_KEY → return [] (line 71)
                             ├──► resp.status != 200 → return []
                             ├──► Exception → return [] (line 96)
                             └──► Success → parse JSON, return results
```

## Error Handling Verification

| Function | Returns `[]` on Exception | Returns `[]` on Non-200 | Verified |
|----------|---------------------------|-------------------------|----------|
| `_duckduckgo_search()` | ✅ Line 62: `except Exception as e: logger.warning(...); return []` | ✅ Line 32-33 | ✅ PASS |
| `_serpapi_search()` | ✅ Line 96: `except Exception as e: logger.warning(...); return []` | ✅ Line 80-81 | ✅ PASS |

## Timeout Check

| Location | Current | Expected | Status |
|----------|---------|----------|--------|
| `_duckduckgo_search()` line 31 | `aiohttp.ClientTimeout(total=10)` | `total=8` | ⚠️ **10s vs 8s spec** |
| `_serpapi_search()` line 78 | `aiohttp.ClientTimeout(total=15)` | No spec (fallback) | ✅ OK |

## End-to-End Test

### Test Code
```python
import asyncio
from skills.web_search import WebSearch

async def test_web_search():
    ws = WebSearch()
    # Test normal search
    results = await ws.search("test query", num_results=3)
    print(f"Normal search returned {len(results)} results")
    
    # Test format_for_telegram
    msg = ws.format_for_telegram(results, "test query")
    print(f"format_for_telegram output length: {len(msg)}")
    
    # Test empty results
    empty_msg = ws.format_for_telegram([], "nonexistent query")
    print(f"Empty results message: {empty_msg}")

asyncio.run(test_web_search())
```

### Expected Results
- `search()` returns list of dicts with title, url, snippet keys
- `format_for_telegram()` returns HTML formatted string
- Empty input returns "No results found" message

## Issues Found

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| Timeout too high | ⚠️ MEDIUM | line 31 | DuckDuckGo timeout is 10s, spec is 8s |

## Verdict

- ✅ Both search functions return `[]` on error (not silent)
- ⚠️ DuckDuckGo timeout is 10s instead of 8s spec
- ✅ `format_for_telegram()` exists and handles empty results
- ✅ Full call path is clear and correct
