---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/planner-decomposition.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.247781"
}
---

# SwarmBot Planner Decomposition
**Date:** 2026-04-11  
**Task:** Bug fixes + MiniMax multi-modal integration + security audit

---

## 🔴 Critical Bug Fixes

### Bug #1: `agent_loop() got an unexpected keyword argument 'progress_cb'`
**File:** `handlers/shared.py` line 303  
**Issue:** Calls `agent_loop(task, progress_cb=on_progress, ...)` but `agent_loop()` expects `progress_fn`  
**Fix:** Change `progress_cb=on_progress` → `progress_fn=on_progress`

### Bug #2: `whatsapp_send_local()` wrong parameter name
**File:** `handlers/computer.py` line 147  
**Issue:** Calls `whatsapp_send_local(contact, message_text, progress_cb=_progress_local)` but function signature uses `_progress`  
**Fix:** Change `progress_cb=_progress_local` → `_progress=_progress_local`

### Bug #3: `tools/minimax_media.py` invalid Python syntax
**File:** `tools/minimax_media.py` lines 71, 95, 121, 185  
**Issue:** Tries to call `MiniMax - CodingPlan_understand_image(...)` etc. as Python functions - INVALID Python identifiers (spaces and hyphens)  
**Analysis:** These are MCP tool names meant for LLM tool-calling, not direct Python calls  
**Fix:** Either:
- (Option A) Remove this broken wrapper file - the tools are called via LLM/MCP, not direct Python
- (Option B) If direct Python access needed, use subprocess to call MiniMax CLI

---

## 🟡 Feature Integration Analysis

### Task #4: MiniMax MCP Tools Status
**Wiki says these tools are available:**
- `MiniMax-CodingPlan_understand_image` - image understanding
- `MiniMax-CodingPlan_web_search` - web search  
- `MiniMax-TokenPlan_image_generation` - image generation
- `MiniMax-TokenPlan_speech_generation` - speech synthesis

**Analysis:** These are MCP (Model Context Protocol) tools, NOT Python functions. They're called by the LLM when needed, not by direct Python code. The handlers in `media_tools.py` work correctly by using the tools in `tools/minimax_media.py`... except that file has broken syntax.

**Action:** Determine if direct Python access to MiniMax API is needed, or if LLM-based tool calling is sufficient.

### Task #5: Verify media_tools.py handler registration
**File:** `handlers/__init__.py`  
**Issue:** `media_tools.py` has handlers for `/imagine`, `/search`, `/speak`, photo analysis but may not be registered  
**Action:** Check router is imported and included in __init__.py

---

## 🔍 Security Audit Tasks

### Task #6: Audit API key handling - no hardcoding
**Search:** `rg "['\"][A-Z_]+API_KEY['\"]\s*=\s*['\"]"` --type py  
**Expected:** All API keys via `os.getenv()` or `os.environ.get()`  
**Files found with potential issues:** Need full codebase scan

### Task #7: Check for other `progress_cb` → `progress_fn` mismatches
**Search pattern:** `progress_cb=(?!on_progress|_progress|on_photo)`  
**Files with `progress_cb`:** 51 matches - verify each call site matches function signature

### Task #8: Audit handlers for other typos/bugs
**Focus areas:**
- Missing `await` on async calls
- Wrong parameter names in function calls  
- Missing error handling
- Bare `except:` clauses

---

## 📋 Subtask Assignment for Workers

### Subtask 1: Fix `agent_loop()` progress_cb bug
**Assigned to:** @worker  
**File:** `handlers/shared.py` line 303  
**Change:**
```python
# BEFORE (line 301-307):
response, model_used = await agent_loop(
    task,
    progress_cb=on_progress,
    photo_cb=on_photo,
    thread_id=thread_id,
    user_id=msg.from_user.id,
)

# AFTER:
response, model_used = await agent_loop(
    task,
    progress_fn=on_progress,
    photo_cb=on_photo,
    thread_id=thread_id,
    user_id=msg.from_user.id,
)
```

### Subtask 2: Fix `whatsapp_send_local()` parameter bug
**Assigned to:** @worker  
**File:** `handlers/computer.py` line 147  
**Change:**
```python
# BEFORE:
result = await computer_agent.whatsapp_send_local(
    contact,
    message_text,
    progress_cb=_progress_local,
)

# AFTER:
result = await computer_agent.whatsapp_send_local(
    contact,
    message_text,
    _progress=_progress_local,
)
```

### Subtask 3: Fix or remove broken `minimax_media.py`
**Assigned to:** @worker  
**File:** `tools/minimax_media.py`  
**Action:** 
1. Check if MiniMax tools should be called directly via Python or via LLM tool-calling
2. If direct access needed: rewrite with valid Python syntax using subprocess or proper API calls
3. If LLM-based: remove the file and document that tools are MCP-based
4. Write ADR if significant architectural decision

### Subtask 4: Audit API keys - ensure no hardcoding
**Assigned to:** @worker  
**Command:** `rg "['\"][A-Z_]+API_KEY['\"]\s*=\s*['\"]"` --type py  
**Fix:** Replace any hardcoded keys with `os.getenv()`

### Subtask 5: Verify media_tools.py is registered
**Assigned to:** @worker  
**File:** `handlers/__init__.py`  
**Action:** Check `media_tools` router is imported and included

### Subtask 6: Test bot startup
**Assigned to:** @worker  
**Command:** `cd /home/newadmin/swarm-bot && python -c "import handlers; print('OK')"`  
**Expected:** Imports without error

### Subtask 7: Review all changes
**Assigned to:** @reviewer  
**Files to review:**
- `handlers/shared.py`
- `handlers/computer.py`
- `tools/minimax_media.py` (if modified)
- Any API key changes

---

## 📁 Files Modified in This Session

| File | Change | Bug/Feature |
|------|--------|-------------|
| `handlers/shared.py` | Fix `progress_cb` → `progress_fn` | Bug #1 |
| `handlers/computer.py` | Fix `progress_cb` → `_progress` | Bug #2 |
| `tools/minimax_media.py` | Fix/remove broken tool wrappers | Bug #3 |
| `handlers/__init__.py` | Verify media_tools registration | Task #5 |
| (various) | Fix any hardcoded API keys | Task #6 |

---

## ✅ Completion Criteria

1. `python -c "import handlers.shared; import handlers.computer"` succeeds without error
2. The `progress_cb` error is resolved
3. `/imagine`, `/search`, `/speak` commands work (if registered)
4. Sending a photo triggers image understanding (via LLM tool-calling)
5. No hardcoded API keys found
6. `pytest tests/ -x --asyncio-mode=auto -q` passes (if tests exist)

---

## 🔧 Quick Reference: Function Signature Fixes

| Function | Expected Param | Called With | Fix |
|----------|---------------|-------------|-----|
| `agent_loop()` | `progress_fn` | `progress_cb` | Rename to `progress_fn` |
| `whatsapp_send_local()` | `_progress` | `progress_cb` | Rename to `_progress` |
| `orchestrate_task()` | `progress_cb` | `progress_cb` | ✅ Correct |
