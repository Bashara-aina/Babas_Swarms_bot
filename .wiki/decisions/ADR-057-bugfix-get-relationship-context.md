# ADR-057-bugfix-get-relationship-context

**Date**: 2026-04-12  
**Type**: Bugfix (import missing)  
**Status**: Proposed  

---

## Error
```
NameError: name 'get_relationship_context' is not defined
```

---

## Root Cause
`llm_client/__init__.py` line 1114 references `get_relationship_context` in a context-injection loop:

```python
("relationship_memory", get_relationship_context),
```

However, `get_relationship_context` is **never imported** into `llm_client/__init__.py`. The function is defined in `core/relationship_memory.py` line 164 but has no import statement pointing to it in the `llm_client` package's import block (lines 1–50).

---

## Affected File
- `llm_client/__init__.py` — line 1114 (usage), import section (fix target)

---

## Fix
Add the missing import to the import block of `llm_client/__init__.py`:

```python
from core.relationship_memory import get_relationship_context
```

---

## Subtasks

### Subtask 1: Add missing import → assign to @worker
**File**: `llm_client/__init__.py`  
**Action**: Add `from core.relationship_memory import get_relationship_context` to the import block (around line 36, after other `core.*` imports).  

### Subtask 2: Verify fix → assign to @worker  
**Action**: Run `pytest tests/ -x --asyncio-mode=auto -q` to confirm no regressions.  

### Subtask 3: Review changes → assign to @reviewer  
**Files**: `llm_client/__init__.py` (diff)  
**Action**: Verify import was added correctly and tests pass.  

---

## Notes
- The function exists and is correctly defined in `core/relationship_memory.py` — no changes needed there.
- The error manifests when the bot processes any message that triggers context injection (e.g., food near Toyosu), because `get_relationship_context` is in the context loop.
- Fix is minimal: single import line.
