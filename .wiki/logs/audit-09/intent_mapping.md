# Intent Mapping Audit — LEGION AUDIT 09
> Generated: 2026-04-12

## Manifest Skills → Intent Enum Mapping

| Skill ID | Manifest Handler | Intent Enum | Keywords in Manifest | Notes |
|----------|------------------|-------------|---------------------|-------|
| `web_search` | `WebSearch` | `Intent.WEB_RESEARCH` | search, google, lookup, look up, research | ✅ MAPPED |
| `geo_intelligence` | `GeoIntelligence` | `Intent.LOCATION_QUERY` | restaurant, hotel, nearby, where to eat, place to stay | ✅ MAPPED |
| `screenpipe_recall` | `screenpipe_tool` | **UNMAPPED** | screen, what's on screen, what did i see | ⚠️ No Intent for screen context |
| `mirofish_simulation` | `mirofish` | **UNMAPPED** | simulate, forecast, consensus | ⚠️ No Intent for simulation |
| `open_interpreter` | `interpreter_tool` | **UNMAPPED** | run code, execute, write and run | ⚠️ No Intent for code execution |
| `database_agent` | `DatabaseAgent` | `Intent.DATABASE_AUDIT` | database, supabase, sql, table, schema, query | ✅ MAPPED |

## Unmapped Skills Analysis

| Skill | Issue | Suggested Intent |
|-------|-------|------------------|
| `screenpipe_recall` | Screen/OCR context retrieval — no matching Intent | Could extend with `SCREEN_CONTEXT` |
| `mirofish_simulation` | Consensus forecasting — no matching Intent | Could use `DEEP_REASONING` or new `SIMULATION` |
| `open_interpreter` | Code execution — no matching Intent | Could use `CODE_GENERATION` or new `CODE_EXECUTION` |

## Intent Enum Reference

From `core/intent_router.py`:

```python
class Intent(Enum):
    COMPUTER_CONTROL = "computer_control"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    WEB_RESEARCH = "web_research"
    WEB_SCRAPE = "web_scrape"
    MEMORY_SEARCH = "memory_search"
    MEMORY_STORE = "memory_store"
    SCHEDULE_TASK = "schedule_task"
    EMAIL_READ = "email_read"
    EMAIL_WRITE = "email_write"
    SITE_ANALYSIS = "site_analysis"
    DATABASE_AUDIT = "database_audit"
    WEATHER_QUERY = "weather_query"
    LOCATION_QUERY = "location_query"
    FILE_OPERATION = "file_operation"
    TRANSLATION = "translation"
    MATH_REASONING = "math_reasoning"
    CREATIVE_WRITE = "creative_write"
    DATA_ANALYSIS = "data_analysis"
    API_CALL = "api_call"
    SELF_UPGRADE = "self_upgrade"
    CASUAL_CHAT = "casual_chat"
    DEEP_REASONING = "deep_reasoning"
```

## Verdict

- ✅ **3/6 skills mapped** to Intent values
- ⚠️ **3/6 skills unmapped** — external tools that may not route through intent system
