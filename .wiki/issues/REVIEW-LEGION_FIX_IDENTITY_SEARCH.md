---
title: Review Legion Fix Identity Search
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
summary: All three fixes were audited with **305 tests passing** and **no blockers
  found**.
wikilinks: []
confidence: medium
source: research
---
All three fixes were audited with **305 tests passing** and **no blockers found**.
---


## FIX 1: Wiki Injection (core/wiki_loader.py, core/system_prompt_builder.py, .wiki/profiles/bashara-aina.md)

### ✅ Passed

| Check | Status |
|-------|--------|
| No hardcoded API keys | ✅ |
| Async compliance (all I/O uses asyncio) | ✅ |
| Type hints present | ✅ |
| Error handling (try/except specific) | ✅ |
| LRU cache for performance | ✅ |
| Proper wiki path handling | ✅ |
| Cache invalidation function | ✅ |
| `get_bashara_identity_context()` always returns guaranteed identity block | ✅ |
| `system_prompt_builder.py` correctly imports and injects wiki context | ✅ |

### ℹ️ Notes

- `wiki_loader.py` uses `Path.read_text(encoding="utf-8", errors="ignore")` — proper error handling
- Priority files (MASTER-INTELLIGENCE.md, profiles/, 06-legion-instructions/) are loaded first
- Budget-aware loading with `max_chars` limit prevents context overflow
- `invalidate_wiki_cache()` provided for runtime updates

### ⚠️ Minor Observation

The `load_wiki_context()` function skips files containing `.obsidian`, `_archive`, or `_quarantine` in path — this is intentional but not documented in code comments. Acceptable.

---

## FIX 2: Language Enforcement (core/character_enforcer.py, SOUL.md)

### ✅ Passed

| Check | Status |
|-------|--------|
| CJK/Arabic detection using Unicode ranges | ✅ |
| `has_non_allowed_script()` correctly identifies non-Latin scripts | ✅ |
| `strip_non_allowed_script()` with replacement dictionary | ✅ |
| `enforce_language()` called FIRST in `enforce_character()` pipeline | ✅ |
| Type hints on all new functions | ✅ |
| Specific exception handling (no bare except) | ✅ |
| No time.sleep() or blocking I/O | ✅ |
| SOUL.md LANGUAGE RULES section added | ✅ |

### ℹ️ Notes

- Language enforcement runs BEFORE forbidden phrase stripping — correct pipeline order
- CJK_REPLACEMENTS dictionary handles common Chinese leaks: "好奇"→"penasaran", "很好"→"bagus", "谢谢"→"terima kasih"
- `enforce_language()` logs warning when stripping occurs (useful for debugging)
- SOUL.md now includes explicit LANGUAGE RULES (lines 63-69) and SEARCH BEFORE ADMITTING IGNORANCE (lines 71-83)

---

## FIX 3: Self-Awareness Gate (core/self_awareness_gate.py, llm_client/__init__.py, tools/web_search.py, SOUL.md)

### ✅ Passed

| Check | Status |
|-------|--------|
| `should_search_instead()` correctly intercepts ignorance signals | ✅ |
| Core knowledge names (bashara, cekwajar, rumahlabuh) trigger mandatory search | ✅ |
| Search intent keywords recognized | ✅ |
| DuckDuckGo web search (no API key required) | ✅ |
| Graceful fallback if duckduckgo-search not installed | ✅ |
| Proper integration in `llm_client.chat()` at line 1255-1272 | ✅ |
| `search_web()` returns formatted Indonesian results | ✅ |
| SOUL.md SEARCH BEFORE ADMITTING IGNORANCE section | ✅ |

### ℹ️ Notes

- `self_awareness_gate.py` is pure logic (no I/O) — no async issues
- `web_search.py` uses `duckduckgo_search` package which requires no API key
- Search gate is wired correctly in `llm_client.chat()`:
  - Called AFTER `postprocess_response()` and `enforce_character()`
  - Results are APPENDED to response (not replacing)
  - If search fails, original response is returned unchanged
- `build_search_query_from_message()` intelligently extracts search intent

### ⚠️ Minor Observation

The search gate in `llm_client.chat()` does:
```python
if should_search_instead(result, task):
    search_query = build_search_query_from_message(task)
    search_results = await search_web(search_query)
    if search_results:
        result = f"{result}\n\n{search_results}"
```

This approach appends search results rather than regenerating the response with enriched context. This is a design choice (avoids double LLM call) but means the model doesn't get to reformulate its answer with the new information. Acceptable given the pragmatic trade-off.

---

## Architecture & Conventions

### ✅ Passed

| Check | Status |
|-------|--------|
| New files follow project conventions | ✅ |
| Import order (stdlib → third-party → local) | ✅ |
| No _old or _backup files created | ✅ |
| All new modules import correctly | ✅ |
| Existing tests pass (305/305) | ✅ |

---

## Security Audit

### ✅ Passed

| Check | Status |
|-------|--------|
| No hardcoded API keys in new files | ✅ |
| No secrets logged | ✅ |
| `duckduckgo_search` requires no API key | ✅ |
| ALLOWED_USER_ID checks remain in handlers | ✅ |
| Web search results are user-initiated only | ✅ |

---

## No Regressions

- ✅ No `parse_mode="Markdown"` introduced in new code
- ✅ Existing parse_mode usage in `main.py` and `business_handler.py` unchanged
- ✅ All 305 tests pass

---

## What Was Done Well

1. **Layered language enforcement**: CJK/Arabic stripping happens FIRST in the pipeline, before any other text processing
2. **Guaranteed identity context**: `get_bashara_identity_context()` provides fallback if wiki loading fails
3. **Performance**: `wiki_loader.py` uses LRU cache and budget-aware loading
4. **Graceful degradation**: All new components have fallback paths if dependencies unavailable
5. **Proper async**: `web_search.py` properly uses `async def` for the search function
6. **Comprehensive ignorance detection**: `IGNORANCE_SIGNALS` list covers Indonesian and English phrases
7. **Critical topic awareness**: Bashara-related queries always trigger search (not just general ignorance)

---

## Recommendations (Non-Blocking)

1. **Consider adding a regeneration option** in self-awareness gate: Instead of appending search results, could call the LLM again with enriched context for better answers. Current append approach is pragmatic but leaves answer formulation to the user.

2. **Consider metrics for search gate**: Track how often `should_search_instead()` triggers vs. how often search results actually provide new information.

3. **CJK replacement dictionary expansion**: The current dictionary is small (11 entries). Consider adding common Indonesian-mixed Chinese phrases that might leak through in technical contexts.

---

## Final Verdict

### ✅ **APPROVED**

All three fixes pass the audit checklist:
- ✅ No blockers
- ✅ Security requirements met
- ✅ Async compliance verified
- ✅ Type hints present
- ✅ Error handling specific
- ✅ No regressions (305 tests pass)
- ✅ Architecture follows conventions
- ✅ Wiki injection correctly wired
- ✅ Language enforcement at correct pipeline point
- ✅ Search gate correctly intercepts ignorance

The implementation is solid and ready for use.
