---
title: Review 2026 04 10 Legion Upgrade Phases 5 10
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
summary: '- **276 tests pass** (`pytest tests/ -x --asyncio-mode=auto -q`)'
wikilinks: []
confidence: medium
source: research
---
- **276 tests pass** (`pytest tests/ -x --asyncio-mode=auto -q`)
- **All imports clean** — no ImportError on new modules
- **Async/await** — correctly used in `scheduler.py`, `self_upgrade.py`, `capability_audit.py`, `web_search.py`, `geo_intelligence.py`, `database_agent.py`, `check_booking_alerts()`
- **Type hints** — present on all public methods
- **Docstrings** — present on all new classes and public functions
- **No hardcoded secrets** — all API keys use `os.getenv()`
- **SQL injection protection** — `database_agent.py` uses allowlist (`_ALLOWED_TABLES`) + `_is_safe_sql()` blocking 11 dangerous keywords
- **`_BLOCKED_PATTERNS`** in `self_upgrade.py` covers `eval`, `exec`, `os.system`, `subprocess.call`, `__import__ os`, `rm -rf`, `shutil.rmtree`
- **Requirements** — `duckduckgo-search` and `apscheduler` added to `requirements.txt`
- **New files**: `skills/web_search.py`, `skills/geo_intelligence.py`, `skills/database_agent.py`, `core/capability_audit.py` — all correctly structured
---


## ⚠️ Warnings

### 1. Unused dependency: `duckduckgo-search`
`requirements.txt` includes `duckduckgo-search>=4.0.0` (line 96), but `skills/web_search.py` implements its own DuckDuckGo API via raw `aiohttp` to `api.duckduckgo.com`. The pip package is never imported. Safe to remove from requirements or switch to using the package.

### 2. LLM calls bypass `llm_client.py`
`self_upgrade.py`, `capability_audit.py`, `database_agent.py`, and `rumahlabuh_crew.py` all import and call `litellm` directly. Per `AGENTS.md`: *"LLM calls go through llm_client.py — never call litellm directly."* This bypasses centralized retry logic, error handling, and fallback chains. Note: 23 files across the codebase share this pattern — it's systemic, not unique to these phases.

---

## ❌ Blockers

### 1. `litellm.completion` (sync) called in async function — event loop BLOCKER
**File**: `tools/rumahlabuh_crew.py:152`
**Function**: `draft_guest_reply()` — async
**Issue**: `litellm.completion` is **synchronous** (verified: `asyncio.iscoroutinefunction(litellm.completion) == False`). It is called without `await`, without `asyncio.to_thread()`, and without any non-blocking wrapper inside an `async def`.

```python
async def draft_guest_reply(...):
    ...
    response = litellm.completion(  # ← BLOCKING CALL, not awaited!
        model=...,
        messages=[{"role": "user", "content": prompt}],
        ...
    )
```

**Impact**: When `draft_guest_reply()` is called (e.g., via `run_crew_task()`), it **blocks the entire asyncio event loop** for the duration of the LLM call (~seconds). On a busy bot with many concurrent handlers, this causes timeouts and unresponsiveness.

**Fix**: Wrap in `asyncio.to_thread()`:
```python
response = await asyncio.to_thread(
    litellm.completion,
    model=os.getenv("DEFAULT_MODEL", "groq/llama-3.3-70b-versatile"),
    messages=[{"role": "user", "content": prompt}],
    max_tokens=300,
    temperature=0.7,
)
```

---

## Summary

| Phase | Component | Status |
|-------|-----------|--------|
| 5 | `core/proactive/scheduler.py` | ✅ OK |
| 6 | `skills/web_search.py` | ✅ OK (warning: unused dep) |
| 6 | `skills/geo_intelligence.py` | ✅ OK |
| 7 | `core/self_upgrade.py` | ✅ OK (warning: direct litellm) |
| 7 | `core/capability_audit.py` | ✅ OK (warning: direct litellm) |
| 8 | `tools/rumahlabuh_crew.py` | ❌ BLOCKER (sync litellm in async fn) |
| 8 | `skills/database_agent.py` | ✅ OK (warning: direct litellm) |
| 9 | Wiki/ADR docs | ✅ OK |
| 10 | `requirements.txt` | ⚠️ unused dep |

**Verdict**: Fix the `litellm.completion` blocker in `rumahlabuh_crew.py` before merge. The blocker is isolated to `draft_guest_reply()` which is not in the critical path, but it is still a correctness issue that will cause observable problems under load.
