---
title: Adr 057 Review Audit
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
summary: '| Import statement at line 39 is syntactically correct | ✅ |'
wikilinks: []
confidence: medium
source: research
---
| Check | Status |
|
---
----|--------|
| Import statement at line 39 is syntactically correct | ✅ |
| `get_relationship_context` is properly defined in `core/relationship_memory.py` (line 164) | ✅ |
| Function signature: `def get_relationship_context() -> Optional[str]:` | ✅ |
| Function returns `Optional[str]` — compatible with usage at line 1115 | ✅ |
| Import follows established pattern (stdlib → third-party → local) | ✅ |
| Runtime import test: `from llm_client import get_relationship_context` succeeds | ✅ |
| Usage at line 1115 is correct (passed as reference, not called immediately) | ✅ |

---

## ⚠️ Warnings: Other Missing Imports in Same Code Block

The context loop at lines 1113–1118 uses **four** context getters, but only **one** (`get_relationship_context`) is properly imported:

```python
for _ctx_name, _ctx_getter in [
    ("episodic_narrative", lambda: build_narrative_context(task)),       # ❌ NOT IMPORTED
    ("relationship_memory", get_relationship_context),                  # ✅ IMPORTED (line 39)
    ("cognition", lambda: build_cognition_system_fragment(...)),        # ❌ NOT IMPORTED
    ("intent_hint", lambda: build_intent_hint(classify_intent_fast(task))),  # ❌ NOT IMPORTED
]:
```

| Function | Defined In | Imported? |
|----------|-----------|-----------|
| `build_narrative_context` | `core/episodic_narrative.py:50` | ❌ No |
| `get_relationship_context` | `core/relationship_memory.py:164` | ✅ Yes |
| `build_cognition_system_fragment` | `core/cognition_pipeline.py:75` | ❌ No |
| `build_intent_hint` | `core/intent_router.py:384` | ❌ No |
| `classify_intent_fast` | `core/intent_router.py` | ⚠️ Imported as `_cif` at line 979 but used as `classify_intent_fast` at line 1117 |

These NameErrors are **silently swallowed** by the `try/except` at lines 1119–1124, so the bot continues running but those context providers simply never execute.

---

## ❌ Blockers

**None** for the specific change under audit (`get_relationship_context` import).

However, the following blockers exist for the **broader code block** (lines 1113–1118) and should be fixed:

1. **Add import for `build_narrative_context`**:
   ```python
   from core.episodic_narrative import build_narrative_context
   ```

2. **Add import for `build_cognition_system_fragment`**:
   ```python
   from core.cognition_pipeline import build_cognition_system_fragment
   ```

3. **Add import for `build_intent_hint`**:
   ```python
   from core.intent_router import build_intent_hint
   ```

4. **Fix `classify_intent_fast` reference** at line 1117 — currently imports as `_cif` at line 979 but uses full name at line 1117:
   ```python
   # Either import it with proper name:
   from core.intent_router import classify_intent_fast
   # Or use the alias:
   ("intent_hint", lambda: build_intent_hint(_cif(task))),
   ```

---

## Recommendations

1. The audited import is **correct and complete** — no changes needed.
2. The Worker agent should add the three missing imports to line 39+ block to enable the other context providers.
3. Consider adding a unit test to verify all four context getters are callable and return expected types.

---

*Reviewer: @reviewer*  
*Audit file: `.wiki/issues/ADR-057-review-audit.md`