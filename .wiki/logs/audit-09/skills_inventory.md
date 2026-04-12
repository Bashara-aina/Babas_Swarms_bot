# Skills Inventory — LEGION AUDIT 09
> Generated: 2026-04-12

## Skills in `skills/` Directory

| File | Class | Public Async Methods | Notes |
|------|-------|---------------------|-------|
| `web_search.py` | `WebSearch` | `search(query: str, num_results: int = 5) -> list[dict[str, Any]]` | DuckDuckGo primary + SerpAPI fallback. `format_for_telegram()` also present (sync). Returns `[]` on failure. **⚠️ ISSUE: DuckDuckGo timeout is 10s (line 31), not 8s spec.** |
| `database_agent.py` | `DatabaseAgent` | `execute_nl_query(nl_query: str, user_id: str) -> str` | NL→SQL via litellm, safety validated (SELECT only), Supabase backend. Returns HTML formatted string. |
| `geo_intelligence.py` | `GeoIntelligence` | `recommend_restaurants()`, `recommend_hotels()`, `nearby_places()` | All 3 methods are async. Uses `WebSearch` internally. Returns HTML formatted strings. |

## Summary

- **Total skill files:** 3
- **Total classes:** 3
- **Total public async methods:** 5
- **Violation:** `web_search.py` DuckDuckGo timeout is 10s, not 8s spec
