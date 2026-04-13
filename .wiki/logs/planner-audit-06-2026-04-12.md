---
date: "2026-04-12"
task: "Fix: unified client, tool calls returned, fallback wired"
---
# AUDIT 06 — LLM Client Layer

## Step 1 — Find All LLM Client Files

| Path | Type | Status |
|------|------|--------|
| `/llm_client.py` | Root shim | ✅ Already a shim re-exporting from `llm_client/` |
| `/llm_client/__init__.py` | Package (68710 bytes) | ✅ Contains all real logic |
| `/tools/mirofish/backend/app/utils/llm_client.py` | Unrelated mirofish tool | ✅ Not part of this audit |

**Imports found:** 107 files import from `llm_client` — all point to `llm_client/` package correctly.

**Verification test:**
```
python -c "from llm_client import call_llm; print('OK')"
→ ImportError: cannot import name 'call_llm'
```
**Conclusion: `call_llm` function does NOT exist and must be created.**

---

## Step 2 — Consolidation Status

✅ **Already consolidated.** `llm_client.py` is a backwards-compatibility shim that re-exports from `llm_client/__init__.py`. No duplication issue.

---

## Step 3 — Verify The Interface

**Canonical signature needed:**
```python
async def call_llm(
    messages: list[dict],
    model: str = None,
    tools: list = None,
    stream: bool = False,
    **kwargs
) -> str | dict
```

**Return value spec:**
- Plain string (extracted message content) for normal calls
- Dict with `{"type": "tool_call", "name": ..., "args": ...}` when LLM returns tool_call
- Never return raw litellm response object

**Current state:**
- `_call_model()` exists but returns raw litellm response object
- `agent_loop()` handles tool_calls internally but via a full agentic loop
- `call_llm()` as specified does NOT exist

---

## Step 4 — Tool Call Return

**litellm.acompletion() calls found:** 31 locations

**`_call_model()` at line ~348:**
- Calls `acompletion(**kwargs)` 
- Returns raw `response` object directly
- No extraction of tool_calls
- No return of `{"type": "tool_call", ...}` dict

**`agent_loop()` at line ~510:**
- Correctly handles tool_calls: parses `tc.function.name` and `tc.function.arguments`
- But this is a full agentic loop, not a single `call_llm()` function

**Missing:** A standalone `call_llm()` function that:
1. Calls `_call_model()` (or directly `acompletion()`)
2. Checks for `tool_calls` in the response
3. Returns `{"type": "tool_call", "name": ..., "args": ...}` if found
4. Returns plain string content otherwise

---

## Step 5 — Model Fallback

**Current state:**
- `get_fallback_chain()` exists in `core/conversation_interface.py`
- `_call_model()` accepts `_fallback_chain: list[str]` parameter
- `chat()` uses `get_fallback_chain(agent_key)` to build the chain
- Rate limiting handled with `_mark_rate_limited()` / `_is_rate_limited()`
- OPENROUTER_API_KEY loaded from env in `_call_model()` line ~382

**What's missing:**
- A top-level `call_llm()` that exposes `model` and `**kwargs` but doesn't expose the internal fallback chain directly — the chain should be used internally from `get_fallback_chain()`
- The `call_llm()` should loop through the fallback chain automatically

---

## Step 6 — Verification

- ❌ `from llm_client import call_llm` fails — function doesn't exist
- ❌ No `{"type": "tool_call", ...}` dict return pattern found
- ❌ `call_llm()` spec not implemented

---

## Subtask Assignments

### Subtask 1: Implement `call_llm()` function in `llm_client/__init__.py`
**Worker:** @worker  
**File:** `/home/newadmin/swarm-bot/llm_client/__init__.py`
**Changes:**
1. Add `async def call_llm(messages, model=None, tools=None, stream=False, **kwargs)` function
2. Use `get_fallback_chain()` to get the model chain
3. Call `acompletion()` via `_call_model()` logic
4. Check `response.choices[0].message.tool_calls`
5. Return `{"type": "tool_call", "name": tc.function.name, "args": json.loads(tc.function.arguments)}` if tool_calls found
6. Return plain string `(response.choices[0].message.content or "").strip()` otherwise
7. Handle rate limits via existing `_is_rate_limited()` / `_mark_rate_limited()` infrastructure
8. Re-export `call_llm` in `__all__`

### Subtask 2: Add `call_llm` to root shim `llm_client.py`
**Worker:** @worker  
**File:** `/home/newadmin/swarm-bot/llm_client.py`
**Changes:**
1. Add `call_llm` to the `from llm_client import (...)` list
2. Add `call_llm` to `__all__`

### Subtask 3: Verify all imports still work
**Worker:** @worker  
**Changes:**
1. Run: `python -c "from llm_client import call_llm; print('OK')"`
2. Run: `pytest tests/test_core_utils.py -x --asyncio-mode=auto -q` (llm_client tests)
3. Run: `python -c "from llm_client import chat, agent_loop, call_llm; print('All OK')"`

### Review: all changes
**Assigned to:** @reviewer

---

## Notes

- `mirofish` llm_client is unrelated and not part of this audit
- 107 files import from llm_client — all currently point to `llm_client/` package correctly
- `llm_client.py` root is already a shim (no changes needed there except adding `call_llm`)
- The `_call_model()` function is the internal workhorse; `call_llm()` should be a cleaner public interface
- No changes to SOUL.md, CLAUDE.md, or LEGION_MASTER.md
