---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/issues/review-2026-04-10-tasks-2-4-5.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-11T18:14:42.300700"
}
---

# Review: Tasks 2, 4, 5 — Parallelize Startup / Test Coverage / mypy

**Date:** 2026-04-10
**Reviewer:** @reviewer
**Status:** CHANGES REQUESTED — test failure must be fixed

---

## Task 2: Parallelize Startup Sequence (`main.py`)

### ✅ Passed
- `_run_group_a_startup()` properly uses `asyncio.wait_for()` with `asyncio.gather()` and `return_exceptions=True` — all 12 tasks run in parallel
- 30-second timeout is reasonable for startup tasks
- Group B runs sequentially after parallel tasks complete (correct dependency management)
- Group C fire-and-forget tasks unchanged (correct)
- All startup tasks wrapped in try/except with non-fatal logging (proper error handling)
- Async/await correctness maintained throughout
- No blocking `time.sleep()` calls

### ⚠️ Warnings
- `_start_n8n()` calls `start_n8n_webhook_listener()` — if this is synchronous and not awaited, it runs fire-and-forget inside a gather. This is intentional per the docstring, but worth flagging.

### ❌ Blockers
- None

---

## Task 4: Raise Test Coverage to 70%

### ✅ Passed
- `pyproject.toml`: `fail_under = 70` correctly raises threshold
- All 6 new test files created with proper structure
- Tests use `pytest.mark.asyncio` correctly for async operations
- Tests use temporary directories (`tmp_path` fixture) correctly

### ⚠️ Warnings
- None

### ❌ Blockers
- **`tests/test_cost_router.py::TestClassifyComplexity::test_classify_expert_architecture`** — **TEST FAILURE**

  **Issue:** Test asserts `result == TaskComplexity.EXPERT` but the test input string is only ~131 characters long:
  ```
  "design a microservices architecture for scalable distributed system 
   with proper load balancing and fault tolerance"
  ```

  The `classify_complexity()` function at `swarms_bot/routing/cost_router.py:120` requires:
  ```python
  if "architecture" in t and length > 300:
      return TaskComplexity.EXPERT
  ```
  Since the input is ~131 chars (not > 300), it falls through to `return TaskComplexity.MODERATE`.

  **Fix:** Either:
  1. Extend the test input string to be > 300 characters to trigger EXPERT classification, OR
  2. Change assertion to `assert result == TaskComplexity.MODERATE` (since the current implementation intentionally requires length > 300 for architecture to be EXPERT)

  **Recommendation:** Option 1 — extend test input. The test comment says "Architecture + length should be expert" which aligns with the implementation requiring length > 300.

---

## Task 5: Add mypy Type Enforcement

### ✅ Passed
- `[tool.mypy]` config added to `pyproject.toml` with `python_version = "3.11"`, `ignore_missing_imports = true`, `warn_unused_configs = true`, `strict = false`
- `.github/workflows/typecheck.yml` created with correct structure (checkout, setup-python, pip install mypy, mypy run)

### ⚠️ Warnings
- `mypy` not installed in environment — could not validate actual mypy output. Workflow appears correct per spec.
- `strict = false` is a lenient setting — mypy will not catch many type errors. Consider enabling more checks in future.

### ❌ Blockers
- None (configuration appears valid)

---

## Summary

| Task | Status | Blockers |
|------|--------|----------|
| Task 2 (Parallelize Startup) | ✅ PASS | 0 |
| Task 4 (Test Coverage 70%) | ❌ FAIL | 1 (test_classify_expert_architecture) |
| Task 5 (mypy Type Enforcement) | ✅ PASS | 0 |

**Action Required:** Fix `test_classify_expert_architecture` — extend input string to > 300 chars OR change expected result to `TaskComplexity.MODERATE`.

---

**Tests Run:** `pytest tests/ -x --asyncio-mode=auto -q`
**Result:** 1 failed, 72 passed
