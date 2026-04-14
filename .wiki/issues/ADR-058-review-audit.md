---
title: Adr 058 Review Audit
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
summary: '| # | Item | Status |'
wikilinks: []
confidence: medium
source: research
---

---


## ✅ Passed

| # | Item | Status |
|---|------|--------|
| 1 | Lines 42, 43, 44 — import source files all exist | ✅ Verified |
| 2 | `build_narrative_context` defined at `core/episodic_narrative.py:50` | ✅ |
| 3 | `build_cognition_system_fragment` defined at `core/cognition_pipeline.py:75` | ✅ |
| 4 | `build_intent_hint` defined at `core/intent_router.py:384` | ✅ |
| 5 | `classify_intent_fast` defined at `core/intent_router.py:317` | ✅ |
| 6 | `_cif` is the correct local alias for `classify_intent_fast` (line 982) | ✅ |

---

## ⚠️ Warnings

| # | Finding | Location | Severity |
|---|---------|----------|----------|
| W1 | Import ordering violation: `from tools.letta_personality` (line 41) inserted before `core.*` imports (lines 42-44). Local packages should be grouped together. | Lines 41-44 | Low |
| W2 | `build_intent_hint` expects `IntentResult` object (line 384 `intent_router.py`), not a raw string. Caller passes `_cif(task)` which returns `IntentResult` — this is correct. | Line 1120 | None |

---

## ❌ Blockers (must be fixed before merge)

### B1: `_cif` used outside its defining scope — **NameError will be silently swallowed**

**Location**: Line 1120

**Problem**: `_cif` is defined as a local alias inside the `try` block at lines 982–984 within `chat()`. The reference at line 1120 is in the for-loop context builder (lines 1116–1127). If `agent_key` was already provided (bypassing the `if not agent_key:` guard at line 979), the `try` block at 979–988 never executes, so `_cif` is never defined.

```python
# Line 979 - guard that must pass for _cif to be defined
if not agent_key:
    try:
        from core.intent_router import classify_intent_fast as _cif  # line 982 — _cif defined HERE
        _intent = _cif(task)                                          # line 984
        ...
    except Exception:
        pass

# Line 1120 - _cif referenced in for-loop (140 lines later)
for _ctx_name, _ctx_getter in [
    ...
    ("intent_hint", lambda: build_intent_hint(_cif(task))),  # BUG: _cif may be undefined!
]:
```

**Impact**: `NameError: cannot access local variable '_cif' where it was not defined` — immediately raised when the lambda is evaluated (line 1123), then silently swallowed by `except Exception: pass` at line 1126. This causes `intent_hint` context to be silently dropped.

**Fix**: Move the `_cif` import to module-level (with other `core.*` imports) or ensure it is defined unconditionally before line 1116.

---

### B2: Import ordering — local packages not grouped together

**Location**: Lines 41–44

**Current order**:
```python
from core.system_prompt_builder import SystemPromptBuilder   # line 40 — core.*
from tools.letta_personality import ...                       # line 41 — tools.*
from core.episodic_narrative import ...                       # line 42 — core.*
from core.cognition_pipeline import ...                      # line 43 — core.*
from core.intent_router import build_intent_hint              # line 44 — core.*
```

**Problem**: `tools.letta_personality` (local) is wedged between `core.system_prompt_builder` and other `core.*` imports. Standard Python import convention (enforced by ruff) is `stdlib → third-party → local`. All `core.*` and `tools.*` are local and should be grouped.

**Fix**: Move `from tools.letta_personality import ...` after all `core.*` imports, or group them with other `tools.*` imports if any existed.

---

## Patterns That Could Cause Silent Failures

| Pattern | Location | Risk |
|---------|----------|------|
| Bare `except Exception: pass` swallowing all errors | Lines 987, 999, 1060, 1071, 1084, 1113, 1126, 1136, 1158, 1167, etc. | **High** — errors in context builders are invisible |
| Lambda captures `_cif` from enclosing scope | Line 1120 | **High** — captured late, may be undefined |
| Late-bound lambda variables in loop | Lines 1117, 1119, 1120, 1141–1151 | Medium — closure captures loop variable |

---

## Recommended Actions

1. **B1 Fix**: Move the `_cif` import to module level with other `core.*` imports (around line 44):
   ```python
   from core.intent_router import build_intent_hint, classify_intent_fast as _cif
   ```
   Then remove lines 982–984.

2. **B2 Fix**: Move `from tools.letta_personality import ...` (line 41) to after line 44 (after all `core.*` imports).

3. **Consider**: Replace bare `except Exception: pass` blocks with logging to detect silent context failures in production.

---

## Files Verified

| File | Line | Existence |
|------|------|-----------|
| `core/episodic_narrative.py` | 50 | ✅ |
| `core/cognition_pipeline.py` | 75 | ✅ |
| `core/intent_router.py` | 317, 384 | ✅ |
| `core/agent_registry.py` | 689 | ✅ (`detect_agent`) |
