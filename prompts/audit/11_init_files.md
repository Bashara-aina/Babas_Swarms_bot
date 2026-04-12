# AUDIT 11 — `__init__.py` Import Glue Files
> Paste this entire prompt into a new OpenCode session.
> Goal: every __init__.py correctly re-exports what callers expect.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 11 — __init__.py Import Glue Files                ║
║  Fix: every package exports the right names; no ImportErrors    ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — LIST ALL __init__.py FILES
Find every __init__.py in the project:
  handlers/__init__.py
  core/__init__.py
  skills/__init__.py
  agents/__init__.py
  bridges/__init__.py
  llm_client/__init__.py
  tools/__init__.py
  legion/__init__.py
  (any others found)

STEP 2 — FOR EACH __init__.py: WHAT DO CALLERS EXPECT?
For each package, grep the entire codebase for:
  from handlers import XYZ
  from core import XYZ
  from skills import XYZ
  (etc.)

Build a list: what names do callers expect each __init__.py to export?

STEP 3 — MISMATCH CHECK
For each expected export name:
  Is it in the __init__.py? If not → add it:
    from handlers.ai import handle_ai
    from handlers.voice import handle_voice
  Does the name actually exist in the submodule? If not → broken export → fix the submodule or remove the import.

STEP 4 — EMPTY __init__.py AUDIT
For any __init__.py that is empty (0 bytes or just a comment):
  Check if any code does from package import XYZ
  If yes: the __init__.py must export XYZ
  Add the necessary imports

STEP 5 — IMPORT ERROR GUARD
For any __init__.py that imports optional dependencies:
  Wrap in try/except:
    try:
        from bridges.voicevox_bridge import VoiceVoxBridge
        VOICEVOX_AVAILABLE = True
    except ImportError:
        VoiceVoxBridge = None
        VOICEVOX_AVAILABLE = False

STEP 6 — VERIFY
Run each package import:
  python -c "import handlers; import core; import skills; import bridges; print('all OK')"
Fix any ImportError until this command succeeds.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
