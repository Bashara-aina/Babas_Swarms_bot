# Planner Log: B1 `_cif` Scope Bug — 2026-04-12

## Task
Fix critical scope bug (B1) in `llm_client/__init__.py` where `_cif` (alias for `classify_intent_fast`) is defined inside `if not agent_key:` block but referenced ~140 lines later in an unconditional for loop.

## Status: IN PROGRESS

## Decomposition

### Subtask 1: Add module-level import → assign to @worker
- Add `classify_intent_fast` to existing `from core.intent_router import ...` line at module level in `llm_client/__init__.py`
- Verified no circular import risk (core/intent_router.py does not import from llm_client)

### Subtask 2: Fix line 1120 lambda → assign to @worker
- Change `lambda: build_intent_hint(_cif(task))` → `lambda: build_intent_hint(classify_intent_fast(task))`

### Subtask 3: Remove stale `_cif` alias (lines 982-984) → assign to @worker
- Change `from core.intent_router import classify_intent_fast as _cif` → `from core.intent_router import classify_intent_fast`
- Change `_intent = _cif(task)` → `_intent = classify_intent_fast(task)`

### Subtask 4: Verify no remaining `_cif` references → assign to @reviewer
- Run `grep -n "_cif" llm_client/__init__.py` to confirm clean

## Decision
ADR-059 written: Solution 1 (module-level import) selected over alternatives

## Next Action
@worker: Execute Subtasks 1-3
@reviewer: Verify Subtask 4
