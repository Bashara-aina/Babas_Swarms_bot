---
title: "ADR-058: Fix Missing Imports in llm_client/__init__.py"
created: 2026-04-12
type: decision
tags: [ADR-058-fix-all-missing-imports]
---
# ADR-058: Fix Missing Imports in llm_client/__init__.py

## Status
- **Created**: 2026-04-12
- **Author**: @planner
- **Reviewer**: @reviewer

## Context

In `llm_client/__init__.py` lines 1113–1118, four items are referenced but not imported at module level. They sit inside try/except so failures are silent, meaning the context builders never actually add context.

| Line | Name | Defined at | Problem |
|------|------|------------|---------|
| 1114 | `build_narrative_context` | `core/episodic_narrative.py:50` | Never imported |
| 1116 | `build_cognition_system_fragment` | `core/cognition_pipeline.py:75` | Never imported |
| 1117 | `build_intent_hint` | `core/intent_router.py:384` | Never imported |
| 1117 | `classify_intent_fast` | `core/intent_router.py:68` (via `_cif` alias at 979) | Called as full name but only aliased locally |

The `get_relationship_context` import was added previously (line 39). Three more need the same treatment.

## Fix — Atomic Subtasks

### Subtask 1: Import `build_narrative_context`
- **File**: `llm_client/__init__.py`
- **Action**: Add import after line 39 (after `from core.relationship_memory import get_relationship_context`)
- **Change**:  
  ```python
  from core.episodic_narrative import build_narrative_context
  ```

### Subtask 2: Import `build_cognition_system_fragment`
- **File**: `llm_client/__init__.py`
- **Action**: Add import after the line added in Subtask 1
- **Change**:  
  ```python
  from core.cognition_pipeline import build_cognition_system_fragment
  ```

### Subtask 3: Import `build_intent_hint`
- **File**: `llm_client/__init__.py`
- **Action**: Add import after the line added in Subtask 2
- **Change**:  
  ```python
  from core.intent_router import build_intent_hint
  ```

### Subtask 4: Fix `classify_intent_fast` reference at line 1117
- **File**: `llm_client/__init__.py`
- **Action**: Change `classify_intent_fast(task)` → `_cif(task)`
- **Line**: 1117
- **Note**: `classify_intent_fast` is imported as `_cif` at line 979 inside a try/except. The full name is not available at module level. The lambda at line 1117 needs to reference the locally aliased `_cif`.

## Verification

All definitions confirmed:
- `core/episodic_narrative.py:50` → `def build_narrative_context(query: str) -> str:`
- `core/cognition_pipeline.py:75` → `def build_cognition_system_fragment(_user_id: str, user_message: str, routing_hint: Optional[str] = None) -> str:`
- `core/intent_router.py:384` → `def build_intent_hint(result: IntentResult) -> str:`
- `core/intent_router.py:68` → `classify_intent_fast` (aliased as `_cif` at line 979)

## Reviewer Checklist

- [ ] Imports added to `llm_client/__init__.py` top-level import block
- [ ] Line 1117 uses `_cif(task)` not `classify_intent_fast(task)`
- [ ] No hardcoded API keys or .env changes
- [ ] `pytest tests/ -x --asyncio-mode=auto -q` passes