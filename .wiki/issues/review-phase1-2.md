---
title: Review Phase1 2
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
summary: '**Status: PARTIAL PASS**'
wikilinks: []
confidence: medium
source: research
---
# Review: Phase 1-2 Changes (2026-04-12)

## SUBTASK 1.1 — Web search result injection
**Status: PARTIAL PASS**

| Check | Result |
|-------|--------|
| `tools/web_search.py` — search properly awaited | ✅ PASS (line 26-28: `asyncio.wait_for(asyncio.to_thread(...)`) |
| `llm_client/__init__.py:1298` — results injected BEFORE reply generation | ✅ PASS (search_results obtained at 1298, injected at 1302-1310, re-call at 1314) |
| 8-second timeout | ✅ PASS (`timeout=8.0` at line 28) |
| Error message for empty/failed search | ✅ PASS (lines 32, 62, 74-75, 78-79) |
| Fallback retry with simplified query | ✅ PASS (lines 44-74) |
| **Circuit breaker applied** | ❌ **FAIL** — `core/circuit_breaker.py` exists but `web_search.py` does NOT import or use it |

---

## SUBTASK 1.2 — Silent exception swallowing
**Status: PASS**

| File:Line | Check | Result |
|-----------|-------|--------|
| `simulation_config_generator.py:522-530` | Exception properly raised after logging | ✅ PASS — line 525 has `raise` |
| `oasis_profile_generator.py:646` | Exception not silently swallowed | ✅ PASS — logs warning at 664, continues to recovery path at 666+ |

**Note:** `oasis_profile_generator.py` does not re-raise at line 664, but this is intentional — it's inside a recovery block ("5. 如果还是失败") that attempts alternative extraction. This is not silent swallowing.

---

## SUBTASK 1.3 + 2.1 — LLM call hardening
**Status: PARTIAL PASS (one blocker)**

| Check | Result |
|-------|--------|
| 30s hard timeout with `asyncio.wait_for` | ✅ PASS (`llm_client/__init__.py:412`) |
| Exponential backoff 1s→2s→4s | ⚠️ **WARN** — `range(3)` gives 0,1,2 attempts. `2**0=1s`, `2**1=2s`, but attempt 2 breaks without sleep (no 4s). Actually: attempt0→1s→attempt1→2s→attempt2→break. Only 2 sleeps, not 3. |
| Max 3 retries | ✅ PASS (`range(3)` at line 410) |
| Retry on RateLimitError, APIConnectionError, Timeout | ✅ PASS (line 413) |
| Model fallback chain | ✅ PASS (lines 365-427 outer loop over `chain`, breaks inner retry loop to try next model) |
| **Token budget guard** | ❌ **FAIL** — No guard preventing excessive token spend across retries. `max_tokens` is accepted as param but no cumulative budget tracking. |

---

## SUBTASK 2.5 — Circuit breaker pattern
**Status: PARTIAL PASS (implementation correct, not applied)**

| Check | Result |
|-------|--------|
| `core/circuit_breaker.py` created | ✅ PASS (146 lines) |
| States: CLOSED, OPEN, HALF_OPEN | ✅ PASS (lines 27-30: `CircuitState` enum) |
| `failure_threshold=5` | ✅ PASS (default at line 39) |
| `recovery_timeout=60s` | ✅ PASS (default at line 40) |
| Async context manager (`async with`) | ✅ PASS (lines 84-109 `__aenter__`/`__aexit__`) |
| **Applied to external services** | ❌ **FAIL** — `tools/web_search.py` does NOT use `with_circuit()` or `CircuitBreaker`. Circuit breaker exists but is unused. |

---

## INCOMPLETE SUBTASKS (flagged for rework)

| Subtask | Status | Notes |
|---------|--------|-------|
| SUBTASK 1.3 | ⚠️ INCOMPLETE | 100+ `asyncio.create_task()` calls still need safe wrapper (e.g., `asyncio.TaskGroup` or tracked wrapper) |
| SUBTASK 2.2 | ⚠️ INCOMPLETE | Memory engine needs per-user locks (`asyncio.Lock` per user_id) |
| SUBTASK 2.3 | ⚠️ INCOMPLETE | Wiki needs hash deduplication, quality gate, jitter on writes |
| SUBTASK 2.4 | ⚠️ INCOMPLETE | Telegram handler needs `split_message()`, retry logic |

---

## Summary

### ✅ Passed (verified correct)
- Web search timeout and retry logic
- Web search result injection before LLM synthesis
- Exception handling in mirofish services (proper raise/log)
- `_call_model` timeout, retry logic, model fallback chain
- Circuit breaker class implementation (correct but unused)

### ⚠️ Warnings
- Backoff timing slightly off: 1s→2s with only 2 sleeps before fallback (no 4s)
- `oasis_profile_generator.py` doesn't re-raise but recovery path exists

### ❌ Blockers (must fix before merge)
1. **Token budget guard missing** — `llm_client/__init__.py:_call_model` must track cumulative tokens and abort if exceeded
2. **Circuit breaker not applied** — `tools/web_search.py` must wrap search in `with_circuit("duckduckgo", ...)`
3. **Incomplete subtasks** — 1.3, 2.2, 2.3, 2.4 remain unimplemented

---

*Reviewer: @reviewer | Date: 2026-04-12*
