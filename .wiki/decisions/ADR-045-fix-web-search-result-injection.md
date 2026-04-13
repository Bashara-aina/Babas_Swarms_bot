---
title: "ADR-045: Fix Web Search Result Injection Pipeline"
date: "2026-04-12"
location: "`llm_client/__init__.py` lines 1255-1272"
status: "Active"
type: "Bug Fix"
---
# ADR-045: Fix Web Search Result Injection Pipeline

**Date:** 2026-04-12
**Status:** Active
**Type:** Bug Fix

## Problem

When Legion detects a web search intent (e.g. "cari di google siapa X"), it:
1. ✅ Detects the intent correctly
2. ✅ Shows a loading message ("Lagi cari...") - but message is NEVER actually sent to Telegram
3. ❌ NEVER returns the actual search result to the user
4. ❌ LLM generates a final reply WITHOUT the search result in context

The user sees: "Honestly? Search tool-nya belum ngasih output balik" — tool fired but result was silently dropped or never awaited.

## Root Cause Analysis

**Location:** `llm_client/__init__.py` lines 1255-1272

### Issue 1: Loading message is never sent
```python
from core.self_awareness_gate import (
    should_search_instead,
    get_search_trigger_message,  # ← IMPORTED BUT NEVER USED!
    build_search_query_from_message,
)
```
`get_search_trigger_message()` returns "🔍 Lagi cari info..." but this is never sent to Telegram.

### Issue 2: search_web() is async but blocks the event loop
In `tools/web_search.py`:
```python
async def search_web(query: str, max_results: int = 5) -> str:
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:  # ← SYNCHRONOUS context manager!
        results = list(ddgs.text(query, max_results=max_results))  # ← BLOCKING I/O
```
The `await` on `search_web()` does NOT make the blocking I/O non-blocking.

### Issue 3: Search results are appended, not re-injected
```python
if search_results:
    result = f"{result}\n\n{search_results}"  # ← Just string concatenation
```
Raw search results are dumped into the response string. The LLM never gets a chance to synthesize them properly.

### Issue 4: Silent exception swallowing
```python
try:
    # ... search logic ...
except Exception:
    pass  # ← ALL ERRORS SILENTLY DROPPED
```

### Issue 5: No timeout
The search has no timeout — can hang indefinitely.

### Issue 6: No retry/fallback
If DuckDuckGo fails, no second attempt with simplified query.

## Fix Requirements

1. **Web search result MUST be injected into LLM context BEFORE generating the reply**
   - Format: `{"role": "tool", "content": "<search_results>", "tool_call_id": "..."}`
   - OR: inject as a system message addendum: "Search results: {results}"

2. **If search returns empty / rate limited / fails:**
   Legion should say HONESTLY what happened:
   "Gw coba search tapi hasilnya kosong / rate limited / error: {reason}"
   NOT: "kemungkinan blah blah" without trying

3. **Add a timeout of 8 seconds on web search calls** — if it times out, say so explicitly

4. **Add a fallback:** if DuckDuckGo fails, try a second search attempt with simplified query

5. **For "cari siapa X" queries specifically:**
   - Search: "{name} researcher" OR "{name} {institution}"
   - Also try: "{name} site:linkedin.com OR site:researchgate.net"
   - Show raw results snippets if found, don't summarize into vague "no results"

6. **After fixing: test with these exact queries:**
   - "cari Bashara Aina Shibaura Institute of Technology"
   - "search who is Bashara Aina"
   - "google siapa presiden Indonesia sekarang"
   All three must return actual search result content in the reply.

## Files to Modify

1. `llm_client/__init__.py` — Fix the self-awareness gate to properly inject search results and send loading message
2. `tools/web_search.py` — Make search properly async with timeout
3. `core/self_awareness_gate.py` — Enhance query building for person searches

## DO NOT Modify
- SOUL.md, character_enforcer.py, nihongo mode files
- Legion's personality or memory system
