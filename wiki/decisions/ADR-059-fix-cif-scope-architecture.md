# ADR-059: Fix `_cif` Scope Bug in llm_client/__init__.py

## Status
- **Created**: 2026-04-12
- **Author**: @planner
- **Reviewer**: @reviewer

## Context

**Bug (B1)**: In `llm_client/__init__.py`, the `_cif` alias for `classify_intent_fast` is defined **only** inside the `if not agent_key:` conditional block at lines 979–988:

```python
if not agent_key:
    agent_key = detect_agent(task)
    try:
        from core.intent_router import classify_intent_fast as _cif  # ← defined here
        _intent = _cif(task)  # ← used here
        ...
    except Exception:
        pass
```

However, `_cif` is referenced **~140 lines later** at line 1120 inside a lambda in a for loop that runs unconditionally:

```python
for _ctx_name, _ctx_getter in [
    ...
    ("intent_hint", lambda: build_intent_hint(_cif(task))),  # ← line 1120
]:
```

**Failure mode**: When `agent_key` is already set (truthy) at call time, the `if not agent_key:` block is skipped entirely, `_cif` is never defined, yet the for loop at 1116–1127 still executes and captures `_cif` → `NameError` silently swallowed by the bare `except Exception: pass`.

## Solution Evaluation

| # | Solution | Pros | Cons |
|---|----------|------|------|
| 1 | Move `classify_intent_fast` import to **module level** (call directly) | Cleanest, eliminates alias entirely, no scope issues | Must handle `ImportError` gracefully |
| 2 | Move `_cif` definition **outside** the conditional | Minimal code change | Wastesfully calls `detect_agent()` when `agent_key` already set |
| 3 | Initialize `_cif = None` before conditional, assign inside | None - still fails when `agent_key` is truthy | Same scope problem, now `TypeError: None is not callable` |
| 4 | Pass `_cif` as parameter to the lambda scope | Avoids closure issue | More complex refactoring of the for loop |

## Decision

**Selected: Solution 1** — Move `classify_intent_fast` import to module level.

**Rationale**:
- `core/intent_router.py` does NOT import from `llm_client` (verified), so no circular import risk
- Eliminates the `_cif` alias entirely, removing the scope dependency
- Consistent with how other imports (e.g., `get_relationship_context`) are handled at module level
- The import already sits inside a try/except, so ImportError is handled gracefully

## Changes Required

### Subtask 1: Add module-level import
- **File**: `llm_client/__init__.py`
- **Action**: Add `classify_intent_fast` to the module-level imports from `core.intent_router`
- **Location**: Find existing `from core.intent_router import ...` line and add `classify_intent_fast`
- **Note**: Keep the try/except import inside `if not agent_key:` as it may serve a fallback purpose, but the module-level import ensures the name is always available

### Subtask 2: Remove `_cif` alias usage at line 1120
- **File**: `llm_client/__init__.py`
- **Action**: Change `lambda: build_intent_hint(_cif(task))` → `lambda: build_intent_hint(classify_intent_fast(task))`
- **Line**: ~1120

### Subtask 3: Remove stale `_cif` alias inside `if not agent_key:` block (optional cleanup)
- **File**: `llm_client/__init__.py`
- **Action**: Change `from core.intent_router import classify_intent_fast as _cif` → `from core.intent_router import classify_intent_fast` (remove alias)
- **Line**: ~982
- **Note**: If the local alias is still used at line 984 (`_intent = _cif(task)`), change to `classify_intent_fast(task)`

### Subtask 4: Verify no other references to `_cif`
- **File**: `llm_client/__init__.py`
- **Action**: Grep for `_cif` to confirm all references updated

## Verification

1. `grep -n "_cif" llm_client/__init__.py` should return no matches
2. `grep -n "classify_intent_fast" llm_client/__init__.py` should show module-level import
3. `pytest tests/ -x --asyncio-mode=auto -q` passes
4. Code review confirms `classify_intent_fast` is called directly at line ~1120

## Reviewer Checklist

- [ ] Module-level import of `classify_intent_fast` added
- [ ] All `_cif` references replaced with `classify_intent_fast`
- [ ] No hardcoded API keys or .env changes
- [ ] `pytest tests/ -x --asyncio-mode=auto -q` passes
- [ ] No circular import introduced
