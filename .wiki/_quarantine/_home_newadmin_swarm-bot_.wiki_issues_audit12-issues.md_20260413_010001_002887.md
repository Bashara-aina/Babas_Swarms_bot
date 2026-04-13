---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/issues/audit12-issues.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.002912"
}
---

# Audit 12 Review — Nihongo Mode User Isolation

**Date:** 2026-04-12
**Reviewer:** @reviewer (LEGION AUDIT 12)
**Status:** ✅ APPROVED

---

## Files Reviewed

| File | Change | Verdict |
|------|--------|---------|
| `handlers/nihongo_handler.py:117` | Added `/nihongo_off` alias | ✅ Correct |
| `tests/test_nihongo_isolation.py` | New 4-test suite | ✅ Approved |

---

## Changes Verified

### 1. `handlers/nihongo_handler.py:117`

```python
elif text in ["/stopp", "/stop", "/nihongo_off"]:
    NihongoModeManager.deactivate(user_id)
```

- `/nihongo_off` correctly added as alias for deactivation
- Uses `user_id = update.effective_user.id` (line 49) — correct per-user isolation
- No breaking changes to existing logic

### 2. `tests/test_nihongo_isolation.py`

4 tests, all passing:
- `test_nihongo_mode_activation_is_per_user` — user A activate does NOT affect user B
- `test_nihongo_mode_deactivation_is_per_user` — user A deactivate does NOT affect user B
- `test_nihongo_sessions_are_independent` — each user gets their own session with independent sub_modes
- `test_user_id_different_means_isolation` — different user IDs = completely isolated sessions

---

## Isolation Guarantees Verified

| Check | Status |
|-------|--------|
| `_sessions: dict[int, NihongoSession]` per-user storage | ✅ |
| `activate(user_id, ...)` uses user_id as sole key | ✅ |
| `deactivate(user_id)` uses user_id as sole key | ✅ |
| `is_active(user_id)` uses user_id as sole key | ✅ |
| Handler extracts `update.effective_user.id` per message | ✅ |
| `handlers/ai.py:743-760` calls `is_active(user_id)` before nihongo routing | ✅ |
| No global/shared mutable state between users | ✅ |

---

## Test Results

```
tests/test_nihongo_isolation.py::test_nihongo_mode_activation_is_per_user PASSED [ 25%]
tests/test_nihongo_isolation.py::test_nihongo_mode_deactivation_is_per_user PASSED [ 50%]
tests/test_nihongo_isolation.py::test_nihongo_sessions_are_independent PASSED [ 75%]
tests/test_nihongo_isolation.py::test_user_id_different_means_isolation PASSED [100%]

============================== 4 passed in 0.06s ===============================
```

---

## ✅ Passed
- `/nihongo_off` alias correctly added (line 117)
- All 4 isolation tests created and passing
- Per-user session storage via `user_id` dict key
- No code path allows user A's nihongo state to leak to user B
- All `activate/deactivate/is_active` use `user_id` as sole isolation key

## ⚠️ Warnings
- None

## ❌ Blockers
- None

---

**Final Verdict: APPROVED**
