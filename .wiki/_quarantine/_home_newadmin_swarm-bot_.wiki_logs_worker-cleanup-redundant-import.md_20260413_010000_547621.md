---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/worker-cleanup-redundant-import.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.547649"
}
---

# Worker Cleanup: Redundant Import Removal

**Date**: 2026-04-12  
**Agent**: Worker (@worker)  
**Task**: Remove redundant local import in `llm_client/__init__.py`

## Change Made

**File**: `llm_client/__init__.py`  
**Line removed**: 982 (redundant local import inside try block)

### Before (lines 981-988):
```python
        try:
            from core.intent_router import classify_intent_fast

            _intent = classify_intent_fast(task)
            if _intent.confidence >= 0.65 and _intent.suggested_agent:
                agent_key = _intent.suggested_agent
        except Exception:
            pass
```

### After (lines 981-986):
```python
        try:
            _intent = classify_intent_fast(task)
            if _intent.confidence >= 0.65 and _intent.suggested_agent:
                agent_key = _intent.suggested_agent
        except Exception:
            pass
```

## Rationale
- `classify_intent_fast` is already imported at **module scope** (line 44):  
  `from core.intent_router import build_intent_hint, classify_intent_fast`
- The local import inside the try block was redundant — the function was already accessible via the module-level import
- Removing it keeps the try block focused on the actual logic (intent classification with fallback on error)

## Verification

| Check | Result |
|-------|--------|
| `python -m py_compile llm_client/__init__.py` | ✅ PASS (no syntax errors) |
| `ruff check llm_client/__init__.py` | ✅ PASS (16 pre-existing issues unrelated to this change; 0 new issues introduced) |
| Try block structure | ✅ Valid — exception handling preserved |

## Notes
- All 16 ruff errors are pre-existing issues (import sorting, undefined names in lambdas, unused variables) — not introduced by this change
- The edit was minimal — only the redundant import line was removed
- The `classify_intent_fast` reference at line 984 now uses the module-level import (available from line 44)
