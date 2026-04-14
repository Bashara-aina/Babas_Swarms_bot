---
title: Adr 059 Review Audit
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: from core.intent_router import build_intent_hint, classify_intent_fast
wikilinks: []
confidence: medium
source: research
---
### 1. Line 44 — Module-level import
```python
from core.intent_router import build_intent_hint, classify_intent_fast
```
**Status**: ✅ Correctly added. `classify_intent_fast` is now imported at module level alongside `build_intent_hint`.

### 2. Lines 979–988 — Conditional block refactor
```python
if not agent_key:
    agent_key = detect_agent(task)
    try:
        from core.intent_router import classify_intent_fast  # <-- local import now redundant
        _intent = classify_intent_fast(task)
        if _intent.confidence >= 0.65 and _intent.suggested_agent:
            agent_key = _intent.suggested_agent
    except Exception:
        pass
```
**Status**: ⚠️ **Warning** — The `from core.intent_router import classify_intent_fast` inside the `try` block (line 982) is now redundant since the function is already imported at module level (line 44). This is not a blocker — it causes no functional harm (re-import of already-imported symbol is a no-op), but it defeats the intent of the refactor and creates maintenance confusion. Recommend removing this redundant local import.

### 3. Line 1120 — Lambda fix
```python
("intent_hint", lambda: build_intent_hint(classify_intent_fast(task))),
```
**Status**: ✅ Correct. Now uses the module-level `classify_intent_fast` directly instead of the old `_cif` alias.
---


## Verification

| Check | Result |
|-------|--------|
| `classify_intent_fast` resolves at module level | ✅ `OK: <function classify_intent_fast at ...>` |
| File passes `py_compile` | ✅ Syntax OK |
| No remaining `_cif` references in file | ✅ `grep` returned zero matches |

---

## Findings

### ✅ Passed
- `classify_intent_fast` is correctly imported at module level (line 44)
- The lambda at line 1120 uses `classify_intent_fast` directly (no alias)
- No remaining `_cif` alias references anywhere in `llm_client/__init__.py`
- File has valid Python syntax
- Function is importable from the module

### ⚠️ Warnings
- **Redundant local import (line 982)**: The `from core.intent_router import classify_intent_fast` inside the `try` block (line 982) is now dead code. Since the symbol is already at module scope, this import does nothing on each call. It should be removed to avoid misleading future maintainers.

### ❌ Blockers
- **None** — No blocking issues found.

---

## Recommendation

The fix is functionally correct and the scope bug is resolved. However, the redundant local import on line 982 should be removed in a follow-up cleanup:

```python
# BEFORE (lines 979-988)
if not agent_key:
    agent_key = detect_agent(task)
    try:
        from core.intent_router import classify_intent_fast  # redundant
        _intent = classify_intent_fast(task)
        if _intent.confidence >= 0.65 and _intent.suggested_agent:
            agent_key = _intent.suggested_agent
    except Exception:
        pass

# AFTER (clean)
if not agent_key:
    agent_key = detect_agent(task)
    try:
        _intent = classify_intent_fast(task)
        if _intent.confidence >= 0.65 and _intent.suggested_agent:
            agent_key = _intent.suggested_agent
    except Exception:
        pass
```

This is a non-critical warning. **Merge readiness: APPROVED** with follow-up cleanup recommended.
