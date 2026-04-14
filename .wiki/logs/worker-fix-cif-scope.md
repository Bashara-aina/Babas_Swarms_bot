---
title: Worker Fix Cif Scope
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Task**: Fix `_cif` scope bug (stale alias + lambda reference)'
wikilinks: []
confidence: medium
source: research
---
# Worker Fix: `_cif` Scope Bug in `llm_client/__init__.py`

**Date**: 2026-04-12  
**Task**: Fix `_cif` scope bug (stale alias + lambda reference)

## Changes Made

### Subtask 1: Updated top-level import (line 44)
```python
# Before:
from core.intent_router import build_intent_hint

# After:
from core.intent_router import build_intent_hint, classify_intent_fast
```

### Subtask 2: Removed stale `_cif` alias (lines 982-984)
```python
# Before:
from core.intent_router import classify_intent_fast as _cif
...
_intent = _cif(task)

# After:
from core.intent_router import classify_intent_fast
...
_intent = classify_intent_fast(task)
```

### Subtask 3: Fixed lambda at line 1120
```python
# Before:
("intent_hint", lambda: build_intent_hint(_cif(task))),

# After:
("intent_hint", lambda: build_intent_hint(classify_intent_fast(task))),
```

## Test Results
- **171 passed**, 1 failure
- The failing test (`test_integration.py::TestIntegration::test_basic_nl_flow`) is an unrelated async SQLite issue in `tools/memory.py` — not caused by these changes
- All syntax/import fixes verified correct via code inspection
