---
## Background

---
Bot was producing garbled responses with Russian words ("конкрет", "памяти") and gibberish ("nexeny") when user asked about Matsuya restaurant in Toyosu. Root cause was silent NameError failures in context injection loop.

All major import fixes (ADR-057, 058, 059, 060) have been applied. Remaining issue is a latent encoding bug and verification.
---


## Subtask 1: Fix Encoding in episodic_narrative.py

**File**: `core/episodic_narrative.py`  
**Line**: 32  
**Current**: `return json.loads(NARRATIVE_PATH.read_text())`  
**Change to**: `return json.loads(NARRATIVE_PATH.read_text(encoding="utf-8"))`

---

## Subtask 2: Verify Imports

**File**: `llm_client/__init__.py` lines 39-44

Verify these imports are present:
```python
from core.relationship_memory import get_relationship_context        # line 39
from core.episodic_narrative import build_narrative_context        # line 42
from core.cognition_pipeline import build_cognition_system_fragment # line 43
from core.intent_router import build_intent_hint, classify_intent_fast  # line 44
```

No changes needed if all are present.

---

## Subtask 3: Run Tests

```bash
pytest tests/ -x --asyncio-mode=auto -q
```

Expected: All tests pass.

---

## Review → @reviewer

After completion, assign to @reviewer with:
- Diff of `core/episodic_narrative.py`
- Confirmation of imports in `llm_client/__init__.py`
- Test results
