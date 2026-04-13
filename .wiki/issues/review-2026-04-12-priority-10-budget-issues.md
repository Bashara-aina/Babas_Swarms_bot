---
## Summary

---
The new `build_system_prompt()` function with priority-based token budget management was added to `core/system_prompt_builder.py`, but it is **never called** by any active code path. All existing call sites continue to use the legacy stub from `agents.py`.
---


## ✅ Passed

1. **Soul is ALWAYS first and never compressed**
   - `LAYER_PRIORITY` lists `"soul"` as index 0 (line 51-52)
   - `build_system_prompt()` lines 329-335 explicitly prevent soul compression:
     ```python
     if layer_name == "soul":
         # Soul is NEVER compressed
     ```

2. **CONTEXT_BUDGET_RATIO = 0.35 is consistent with documentation**
   - Value: `0.35` (line 47)
   - Comment: "use max 35% of context for system prompt"
   - Internal logic uses `CONTEXT_BUDGET_RATIO` directly → consistent

3. **LAYER_PRIORITY order is logically sound**
   ```
   soul → user_profile → working_memory → relevant_memory → wiki_context → search_results → personality → skill_context
   ```
   - Correct: soul first (never compressed), user_profile always included, then descending priority
   - Progressive fallback: working_memory compressed if tight, relevant_memory dropped if very tight

4. **estimate_tokens() provides reasonable estimation**
   - Implementation: `max(1, len(text) // 4)` (lines 63-67)
   - Reasonable for English-dominated text (avg ~4 chars/token)

5. **All layer fetchers have try/except with logger.debug()**
   - Every `_get_*_content()` function wraps imports/calls in try/except
   - Failures logged at DEBUG level, never raise

---

## ⚠️ Warnings

1. **`compress_section()` has no test coverage**
   - Function exists at lines 70-89 but is not exercised by any test
   - The truncation-from-middle logic may have edge cases

2. **No verification that 0.35 ratio is optimal**
   - No comment explaining why 35% was chosen vs 30% or 40%
   - May need empirical tuning based on actual context window sizes

---

## ❌ Blockers

### CRITICAL: `build_system_prompt()` is never called

**Finding:** The new async `build_system_prompt()` function (lines 292-355 in `core/system_prompt_builder.py`) is **completely disconnected** from all active call sites.

**Evidence:**
| File | Import Source | Function Called |
|------|---------------|-----------------|
| `core/orchestrator.py:302` | `from agents import ... build_system_prompt` | Legacy stub from `agents.py:60` |
| `core/orchestrator.py:363` | `from agents import ... build_system_prompt` | Legacy stub from `agents.py:60` |
| `task_orchestrator.py:278,345` | `from agents import ... build_system_prompt` | Legacy stub |
| `tools/swarm_wire.py:30` | `from agents import ... build_system_prompt` | Legacy stub |
| `tools/overnight.py:189,373` | `from agents import ... build_system_prompt` | Legacy stub |
| `tools/deep_research.py:157` | `from agents import ... build_system_prompt` | Legacy stub |
| `tools/deep_think.py:45` | `from agents import ... build_system_prompt` | Legacy stub |
| `router.py:58` | `from agents import ... build_system_prompt` | Legacy stub |

**Legacy stub** (`agents.py:60-67`):
```python
def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
    wrapper = PERSONA_WRAPPER.strip() if PERSONA_WRAPPER else ""
    return f"{wrapper}\n\n{role_prompt}" if wrapper else role_prompt
```
This stub does **zero** priority-based budget management — it just prepends a personality wrapper.

**`llm_client/__init__.py`** (line 40):
```python
from core.system_prompt_builder import SystemPromptBuilder
```
Uses the **old class-based** `SystemPromptBuilder`, not the new `build_system_prompt()` function.

**Impact:** Priority 10 budget management code is dead code. No context window optimization occurs.

**Required Fix:** Either:
1. Update call sites to import and call `build_system_prompt()` from `core.system_prompt_builder` with proper async handling, OR
2. Update `llm_client/__init__.py` to use the new `build_system_prompt()` in its `chat()` function

---

## Verification Script Output

```
python scripts/verify_wiring.py
...
Handler Wiring: PASS
Core Imports: PASS
LLM Client: PASS
Tools: PASS
Bridges: PASS
Skills: PASS
Agents: PASS
All wiring checks passed!
```

**Note:** The wiring script only verifies imports succeed, not that the new function is actually invoked by production code paths.

---

## Recommendation

**BLOCK MERGE** until the new `build_system_prompt()` is wired into actual call sites. The budget management feature exists but provides zero value in its current state.

**Next Steps:**
1. Identify which call path is the primary LLM invocation (likely `llm_client/chat()`)
2. Update that path to use `await build_system_prompt(user_id, query, model, extras)` 
3. Add integration test that verifies budget enforcement
4. Remove or deprecate the legacy stub in `agents.py`
