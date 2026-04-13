---
# LEGION AUDIT 12 — Worker Completion Log

**Date:** 2026-04-12  
**Agent:** @worker  
**Scope:** Nihongo Mode per-user isolation audit

---

## Subtask Results

### SUBTASK 1 — FIND NIHONGO MODE FLAG STORAGE ✅
- **File:** `skills/nihongo/mode_manager.py:48`
- **Code:** `_sessions: dict[int, NihongoSession] = {}`
- **Status:** Confirmed — per-user keyed dict

### SUBTASK 2 — VERIFY PER-USER STORAGE ISOLATION ✅
- `activate(user_id, ...)` at line 62 — activates only that user_id
- `deactivate(user_id)` at line 72 — deactivates only that user_id
- `is_active(user_id)` at line 57 — checks only that user_id
- `_sessions` dict ensures user A's session is completely isolated from user B

### SUBTASK 3 — VERIFY ACTIVATION COMMAND ✅
- **File:** `handlers/nihongo_handler.py:47-66`
- `/nihonko` command calls `NihongoModeManager.activate(user_id, NihongoSubMode.CHAT)` with `user_id = update.effective_user.id`
- Confirmation sent in Japanese (mixed JP/ID/EN)

### SUBTASK 4 — VERIFY DEACTIVATION COMMAND ⚠️ FIXED
- **File:** `handlers/nihongo_handler.py:117`
- Previously only handled `/stopp` and `/stop`
- **FIXED:** Added `/nihongo_off` alias: `text in ["/stopp", "/stop", "/nihongo_off"]`

### SUBTASK 5 — VERIFY MAIN MESSAGE HANDLER ✅
- **File:** `handlers/ai.py:743-760`
- Nihongo intercept check: `if NihongoModeManager.is_active(user_id):` before routing
- Runs BEFORE any other message routing

### SUBTASK 6 — CREATE AND RUN ISOLATION TEST ✅
- **Created:** `tests/test_nihongo_isolation.py`
- **Tests:** 4 tests covering:
  1. `test_nihongo_mode_activation_is_per_user` — user A active ≠ user B active
  2. `test_nihongo_mode_deactivation_is_per_user` — deactivate A doesn't affect B
  3. `test_nihongo_sessions_are_independent` — different sub_modes per user
  4. `test_user_id_different_means_isolation` — concrete user A ≠ user B proof
- **Result:** 4/4 PASSED

### SUBTASK 7 — VERIFY LEGION SOUL PRESERVATION ✅
- `sensei_prompt.py` line 6: "You are NOT Legion. You are NOT a general AI assistant."
- No Legion markers in nihongo mode prompts
- `SenseiSoul` is a separate dynamic layer (mood, relationship metrics) — ON TOP of sensei base, not replacing
- `build_sensei_system_prompt()` assembles prompt from components, soul is additive layer

---

## Changes Made

| # | File | Change |
|---|------|--------|
| 1 | `handlers/nihongo_handler.py:117` | Added `/nihongo_off` to deactivation command list |
| 2 | `tests/test_nihongo_isolation.py` | **Created** — 4 isolation tests |

---

## Test Results

```
pytest tests/ -x --asyncio-mode=auto -q
373 passed, 2 warnings in 41.48s
```

All 373 tests pass (including 4 new nihongo isolation tests).

---

## Summary

| Category | Status |
|----------|--------|
| Per-user flag storage | ✅ Correct — `_sessions: dict[int, NihongoSession]` |
| activate() isolation | ✅ User A ≠ User B |
| deactivate() isolation | ✅ User A ≠ User B |
| is_active() check | ✅ Per-user, not global |
| Activation command | ✅ `/nihonko` with `update.effective_user.id` |
| Deactivation command | ✅ `/stopp`, `/stop`, `/nihonko_off` (fixed) |
| Message handler intercept | ✅ `is_active(user_id)` check before routing |
| Isolation test | ✅ Created and passing |
| Legion soul preservation | ✅ Sensei is NOT Legion; soul is additive layer |

## Remaining Issues
None.
