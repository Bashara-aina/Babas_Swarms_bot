---
title: Adr 090 Garbled Text Context Injection
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: Bot responded with garbled text mixing Russian words ("конкрет", "памяти")
  and gibberish ("nexeny") when user asked about Matsuya restaurant in Toyosu.
wikilinks: []
confidence: medium
source: research
---
Bot responded with garbled text mixing Russian words ("конкрет", "памяти") and gibberish ("nexeny") when user asked about Matsuya restaurant in Toyosu.

**Root Cause**: Missing imports in `llm_client/__init__.py` caused context builders to fail silently with `NameError`, resulting in malformed LLM context and hallucinations.
---


## Affected Code

**File**: `llm_client/__init__.py` lines 1113-1118

```python
for _ctx_name, _ctx_getter in [
    ("episodic_narrative", lambda: build_narrative_context(task)),       # ❌ NOT IMPORTED
    ("relationship_memory", get_relationship_context),                   # ✅ FIXED (ADR-057)
    ("cognition", lambda: build_cognition_system_fragment(...)),       # ❌ NOT IMPORTED  
    ("intent_hint", lambda: build_intent_hint(classify_intent_fast(task))),  # ❌ SCOPE BUG
]:
    try:
        _ctx = _ctx_getter()
        if _ctx:
            _audit_messages.append({"role": "system", "content": _ctx})
    except Exception:
        pass  # ← SILENT FAILURE — NameError swallowed, no context injected
```

When these functions aren't imported, Python raises `NameError`, which is silently caught by `except Exception: pass`. The LLM receives context without the expected narrative/relationship/cognition blocks, causing hallucinations.

---

## Fix

### Subtask 1: Add explicit encoding to `episodic_narrative.py` → @worker
**File**: `core/episodic_narrative.py` line 32  
**Change**: `NARRATIVE_PATH.read_text()` → `NARRATIVE_PATH.read_text(encoding="utf-8")`

### Subtask 2: Verify all imports are present → @worker
**File**: `llm_client/__init__.py`  
**Action**: Confirm lines 39-44 have all required imports:
```python
from core.relationship_memory import get_relationship_context        # line 39
from core.episodic_narrative import build_narrative_context        # line 42
from core.cognition_pipeline import build_cognition_system_fragment # line 43
from core.intent_router import build_intent_hint, classify_intent_fast  # line 44
```

### Subtask 3: Run tests → @worker
**Command**: `pytest tests/ -x --asyncio-mode=auto -q`

### Review: All changes → @reviewer
**Files**: `core/episodic_narrative.py`, `llm_client/__init__.py`

---

## Verification Checklist

- [ ] `episodic_narrative.py:32` uses explicit `encoding="utf-8"`
- [ ] All 4 context getters are properly imported in `llm_client/__init__.py`
- [ ] `pytest tests/ -x --asyncio-mode=auto -q` passes
- [ ] No hardcoded secrets or .env changes

---

## Notes

- ADR-057 (get_relationship_context import) was already applied
- ADR-058 (other missing imports) was already applied  
- ADR-059 (_cif scope bug) was already applied
- ADR-060 (redundant import cleanup) was already applied
- This ADR adds defensive encoding fix and confirms all prior fixes are in place
