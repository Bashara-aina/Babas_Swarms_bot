---
title: Adr 060 Cleanup Redundant Import
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
summary: '**Proposed** | 2026-04-12'
wikilinks: []
confidence: medium
source: research
---
# ADR-060: Cleanup Redundant Import in llm_client/__init__.py

## Status
**Proposed** | 2026-04-12

## Context
In `llm_client/__init__.py`, inside function `generate_response` (around line 981), there is a local import:

```python
try:
    from core.intent_router import classify_intent_fast  # line 982 (redundant)

    _intent = classify_intent_fast(task)
    if _intent.confidence >= 0.65 and _intent.suggested_agent:
        agent_key = _intent.suggested_agent
except Exception:
    pass
```

However, `classify_intent_fast` is **already imported at module scope** at line 44:
```python
from core.intent_router import build_intent_hint, classify_intent_fast  # line 44
```

## Decision
Remove the redundant local import at line 982. The surrounding try block (lines 981-988) should remain intact to preserve graceful error handling for the `classify_intent_fast` call itself.

## Changes
1. **Delete line 982**: `from core.intent_router import classify_intent_fast`
2. **Preserve lines 984-988**: The call to `classify_intent_fast(task)` and the `except Exception: pass` remain, relying on the module-scope import

## Rationale
- The module-level import (line 44) already makes `classify_intent_fast` available in the entire module
- The local import was likely added as a defensive measure but is now dead code
- Removing it does not change runtime behavior since the symbol is already in scope
- Keeping the try/except preserves the fallback behavior (silently ignore errors from `classify_intent_fast`)

## Consequence
No negative consequences. The code path remains identical — `classify_intent_fast` is called the same way, just via the module-scope import instead of a redundant local import.
