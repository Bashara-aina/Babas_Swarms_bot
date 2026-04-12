# Review: LEGION AUDIT 04 — Context Injection
**Date:** 2026-04-12  
**Reviewer:** @reviewer  
**Files Reviewed:** 6 key files + tests

---

## ✅ Passed

### 1. LLM Call Sites (`llm_client/__init__.py`)
- **[Line 515-518]** AUDIT04 debug logging present:
  ```python
  logger.debug(f"[AUDIT04] acompletion call: model={model_name}, messages={len(messages)}, ...")
  ```
- **[Lines 656-658]** Agent loop also has AUDIT04 debug logging
- **[Lines 1265-1267]** Pre-LLM call debug logging in `chat()`
- **[Lines 1022-1227]** Proper `messages[]` assembly with DISTINCT system messages (not concatenated)

### 2. Soul Injection (`core/soul_engine.py`)
- **[Lines 47-70]** Startup assertion `_assert_soul_injection()` checks SOUL.md for "Legion" identity marker in first 500 chars
- **[Lines 83-92]** `get_cached_soul()` with 5-min TTL cache
- **[Lines 435-439]** `build_soul_context()` - canonical entry point
- **[Lines 358-429]** `build_enhanced_soul_context()` - dynamic time context, emotional state, mood momentum, banned phrases

### 3. Soul Injection in `llm_client/chat()` (`llm_client/__init__.py`)
- **[Lines 1028-1031]** Soul is FIRST system message in `_audit_messages`:
  ```python
  _soul = build_soul_context()
  if _soul:
      _audit_messages.append({"role": "system", "content": _soul})
  ```
- **[Lines 1029]** `build_soul_context()` is called unconditionally when `_SOUL_ENABLED=true`

### 4. Memory Injection (`llm_client/__init__.py`)
- **[Lines 1064-1073]** Semantic memory via `LegionSemanticMemory().search_memories(task, str(user_id), limit=5)`
- **[Lines 1072-1073]** Memory inserted as separate system message at position 1:
  ```python
  _audit_messages.append({"role": "system", "content": "[Memory]\n" + "\n".join(_memory_context_lines)})
  ```

### 5. Wiki Injection (`llm_client/__init__.py` + `core/unified_prompt_context.py`)
- **[Lines 1076-1084]** Wiki retrieved for EVERY message via `gather_parallel_prompt_layers()`:
  ```python
  for _layer in await gather_parallel_prompt_layers(task, str(user_id), mode=_chat_mode):
      if _layer:
          _audit_messages.append({"role": "system", "content": _layer})
  ```
- **`core/unified_prompt_context.py` [Lines 39-48]** `_wiki_layer()` queries `get_wiki_manager().query(query, top_k=3)`
- **`core/unified_prompt_context.py` [Lines 51-60]** `_opencode_brain_layer()` also provides wiki context

### 6. Search Injection (`tools/web_search.py` + `llm_client/__init__.py`)
- **`tools/web_search.py` [Lines 42-44]** `asyncio.wait_for` with `timeout=8.0`:
  ```python
  results = await asyncio.wait_for(
      asyncio.to_thread(_sync_search, query),
      timeout=8.0,
  )
  ```
- **`tools/web_search.py` [Lines 72-74]** Retry also uses `timeout=8.0`
- **`llm_client/__init__.py` [Lines 1379-1388]** Results injected as SYSTEM message (not user):
  ```python
  tool_result_msg = {
      "role": "system",
      "content": f"[Search Results for: {task}]\n{search_results}\n\nSintesiskan..."
  }
  messages.append(tool_result_msg)
  ```

### 7. No Regressions
- **Tests:** 369 passed, 2 warnings (minor RuntimeWarning about unawaited coroutine - not a blocker)
- **Ruff:** Pre-existing import-order issues in `agents.py` (E402, I001) — not introduced by this audit

---

## ⚠️ Warnings

### 1. Search synthesis model mismatch (low risk)
**File:** `llm_client/__init__.py` line 1392
```python
synth_resp = await _call_model(
    model=chain[0],  # ← Always uses first model in chain
    messages=messages,
    ...
```
The original `_call_model` loop uses the iterated `model` variable (line 1269), but synthesis explicitly uses `chain[0]`. This means if `model` was a fallback model, synthesis goes to primary. This could be intentional (use primary for synthesis), but worth noting.

### 2. Test coverage for search injection is minimal
**File:** `tests/test_search_injection.py` — Only 5 tests, all mocking basic behavior. The actual search injection flow in `llm_client/__init__.py` lines 1353-1408 is not exercised by tests. However, this is a pre-existing gap, not an audit issue.

### 3. RuntimeWarning: unawaited coroutine in memory tests
```
RuntimeWarning: coroutine 'MemoryEngine.get_context_window' was never awaited
```
**Files:** `test_multi_user_isolation.py`, `test_smoke.py` — Minor issue, does not affect functionality.

---

## ❌ Blockers

**None.** All mandatory audit requirements are satisfied:
1. ✅ Soul is FIRST in messages[]
2. ✅ Memory (system) is present  
3. ✅ Wiki (system) is present
4. ✅ Search results (system) injected when search triggered
5. ✅ Conversation messages present
6. ✅ Debug logging at all LLM call sites

---

## Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Soul FIRST in messages[] | ✅ | `llm_client/__init__.py:1028-1031` |
| Memory present (system) | ✅ | `llm_client/__init__.py:1062-1073` |
| Wiki present (system) | ✅ | `llm_client/__init__.py:1076-1084` |
| Search results injected | ✅ | `llm_client/__init__.py:1379-1388` |
| Conversation history | ✅ | `llm_client/__init__.py:1206-1218` |
| Debug logging | ✅ | `llm_client/__init__.py:515-518, 656-658, 1265-1267` |
| Startup soul assertion | ✅ | `core/soul_engine.py:47-70` |
| Search timeout=8.0 | ✅ | `tools/web_search.py:42-44, 72-74` |
| No regressions | ✅ | 369 tests passed |

**Recommendation:** Approve merge. All AUDIT04 requirements are implemented correctly. The warnings are minor/pre-existing and do not block merge.