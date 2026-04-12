# AUDIT 05 — Core Module Wiring
> Paste this entire prompt into a new OpenCode session.
> Goal: every file in core/ is actively used; every export matches what callers import.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 05 — Core Module Wiring                           ║
║  Fix: no orphan core modules; all exports match imports         ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — LIST ALL CORE FILES
List every .py file in core/.

STEP 2 — FOR EACH CORE FILE: WHO CALLS IT?
For each core module, grep the entire codebase for imports of that module.
Example: grep -r "from core.soul_engine" . --include="*.py"
If NO file imports a core module → dead module → classify and decide:
  Option A: Wire it in (find where it SHOULD be called, add the call)
  Option B: Mark it with FEATURE_X_ENABLED = False and add a comment

STEP 3 — EXPORT/IMPORT MISMATCH
For every import statement found in Step 2:
  from core.xxx import YYY
Verify YYY actually exists in core/xxx.py.
If not → Type A broken wire → add the missing function/class or fix the import.

STEP 4 — core/__init__.py AUDIT
Read core/__init__.py.
List what it exports.
Search for any code that does: from core import XYZ
Verify XYZ is in core/__init__.py.
Fix any missing re-export.

STEP 5 — KEY MODULE CONNECTION CHECKS

  soul_engine.py:
    → Must be called by system_prompt_builder.py
    → get_system_prompt() must return a non-empty string
    → Verify it loads SOUL.md from the correct path

  memory_engine.py:
    → Must be called by system_prompt_builder.py (read) and message handler (write)
    → read_memory(user_id) must return string or list
    → write_memory(user_id, content) must persist data

  skill_registry.py:
    → Must scan skills/ directory at startup
    → Must be called by autonomous_router.py or intent_router.py
    → get_skill(name) must return callable skill

  system_prompt_builder.py:
    → Must call soul_engine, memory_engine, wiki retrieval
    → Must return complete messages[] list ready for litellm

  intent_router.py:
    → Must cover all major intents (search, wiki, memory, nihongo, voice, code, chat)
    → Must return structured intent object, not just a string

STEP 6 — FIX AND VERIFY
Fix every broken wire found.
Run: python -c "from core import soul_engine, memory_engine, skill_registry, system_prompt_builder, intent_router" and confirm no ImportError.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
