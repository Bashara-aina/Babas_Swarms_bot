---
date: "2026-04-12"
task: "Fix nihongo mode so it is fully per-user and cannot leak between users"
planner: "@planner (MiniMax M2.7)"
---
# LEGION AUDIT 12 — Planner Log

## Subtask Decomposition

### Subtask 1: FIND NIHONGO MODE FLAG STORAGE
**Assigned to:** @worker

**Commands/Files to examine:**
- `skills/nihongo/mode_manager.py` — NihongoModeManager class
- `grep -n "_sessions\|_active\|user_id" skills/nihongo/mode_manager.py`

**Success Criteria:**
- Identify where `_sessions` dict is defined (line 48: `_sessions: dict[int, NihongoSession] = {}`)
- Verify key is `user_id` (int)
- Confirm class-level storage uses `user_id` as key

---

### Subtask 2: VERIFY PER-USER STORAGE ISOLATION
**Assigned to:** @worker

**Commands/Files to examine:**
- `skills/nihongo/mode_manager.py` — `get_session()`, `is_active()`, `activate()`, `deactivate()`
- `tests/test_nihongo_mode.py` — existing isolation tests

**Success Criteria:**
- `get_session(user_id)` returns only that user's session
- `activate(user_id_A)` does NOT affect `is_active(user_id_B)` when `user_id_A != user_id_B`
- Session data (words_seen, grammar_seen, etc.) is isolated per user

---

### Subtask 3: VERIFY ACTIVATION COMMAND HANDLER
**Assigned to:** @worker

**Commands/Files to examine:**
- `handlers/nihongo_handler.py:47-66` — `handle_nihongo_command()`
- `handlers/ai.py:750-757` — nihongo intercept in main handler

**Success Criteria:**
- `/nihonko` command calls `NihongoModeManager.activate(user_id, ...)` with correct `user_id`
- `user_id` is sourced from `update.effective_user.id` (line 49, 748)
- No global flag mutation

---

### Subtask 4: VERIFY DEACTIVATION COMMAND
**Assigned to:** @worker

**Commands/Files to examine:**
- `handlers/nihongo_handler.py:117-125` — `/stopp` and `/stop` handlers
- Search for `/nihongo_off` in codebase

**Success Criteria:**
- `/stopp` or `/stop` calls `NihongoModeManager.deactivate(user_id)`
- If `/nihongo_off` is missing, CREATE it as alias to `/stopp`
- Deactivation is per-user (uses `user_id` from `update.effective_user.id`)

---

### Subtask 5: VERIFY MAIN MESSAGE HANDLER CHECKS PER-USER FLAG
**Assigned to:** @worker

**Commands/Files to examine:**
- `handlers/ai.py:755-757` — `if NihongoModeManager.is_active(user_id):`
- `handlers/nihongo_handler.py:240-267` — `handle_nihongo_message()`

**Success Criteria:**
- `is_active(user_id)` is called with the correct per-user `user_id`
- Messages from user A do NOT trigger nihongo mode for user B
- Flag check is BEFORE any LLM call

---

### Subtask 6: CREATE AND RUN ISOLATION TEST
**Assigned to:** @worker

**Commands/Files to examine/create:**
- `tests/test_nihongo_isolation.py` — NEW file for this audit
- Existing: `tests/test_multi_user_isolation.py:10-24`

**Success Criteria:**
- Test file `tests/test_nihongo_isolation.py` created with:
  - `test_user_a_nihongo_does_not_affect_user_b()` — activate for user A, verify user B is not active
  - `test_concurrent_users_isolated()` — two users, one activates nihongo, other stays normal
  - `test_deactivate_only_affects_target_user()` — user A deactivates, user B remains active
- Run: `pytest tests/test_nihongo_isolation.py -v`
- All tests pass

---

### Subtask 7: VERIFY LEGION SOUL PRESERVATION IN NIHONGO MODE
**Assigned to:** @worker

**Commands/Files to examine:**
- `skills/nihongo/sensei_prompt.py` — `build_sensei_system_prompt()`
- `tests/test_soul_persistence.py:46` — `test_nihongo_mode_does_not_contaminate_soul()`

**Success Criteria:**
- `test_nihongo_mode_does_not_contaminate_soul()` passes
- Sensei prompt does NOT contain Legion markers: "SOUL", "MASTER_PROMPT", "Soul Engine"
- Confirmed by `test_sensei_prompt_no_legion_content()` in `tests/test_nihongo_mode.py:33-45`

---

## Review Task
**Assigned to:** @reviewer

**Review all changes:**
1. Verify `NihongoModeManager` uses `user_id` as key (not global flag)
2. Verify `/stopp`/`/stop` deactivates per-user only
3. Verify `test_nihongo_isolation.py` covers all isolation scenarios
4. Confirm all 7 subtasks have passing success criteria

---

## Status: IN PROGRESS
