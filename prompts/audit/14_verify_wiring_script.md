# AUDIT 14 — Automated Wiring Verification Script
> Paste this entire prompt into a new OpenCode session.
> Goal: create and run a script that auto-verifies all wiring; must exit 0.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 14 — Automated Wiring Verification Script         ║
║  Fix: write verify_wiring.py, run it, fix everything until 0    ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — CREATE scripts/verify_wiring.py
Create the file with the following content (implement fully):

```python
#!/usr/bin/env python3
"""Legion Wiring Verification — run after any major change.
Exit 0 = all wiring OK. Exit 1 = broken wires found."""
import sys
import importlib
import ast
from pathlib import Path

passed = []
failed = []

def check(label, condition, fix_hint=""):
    if condition:
        passed.append(label)
        print(f"✅ {label}")
    else:
        failed.append((label, fix_hint))
        print(f"❌ {label}" + (f" → {fix_hint}" if fix_hint else ""))

# ── SECTION 1: Module Imports ─────────────────────────────────────
MODULES = [
    "handlers.ai", "handlers.voice", "handlers.message_handler",
    "handlers.memory_commands", "handlers.research", "handlers.inline",
    "handlers.swarm_handler", "handlers.orchestrate", "handlers.wiki",
    "handlers.nihongo_handler" if Path("handlers/nihongo_handler.py").exists() else None,
    "handlers.github_intel_handler", "handlers.streaming",
    "core.soul_engine", "core.memory_engine", "core.skill_registry",
    "core.system_prompt_builder", "core.intent_router", "core.autonomous_router",
    "core.task_router",
]
for mod in [m for m in MODULES if m]:
    try:
        importlib.import_module(mod)
        check(f"import {mod}", True)
    except ImportError as e:
        check(f"import {mod}", False, str(e))
    except Exception as e:
        check(f"import {mod} (runtime)", False, str(e))

# ── SECTION 2: main.py Registrations ─────────────────────────────
main_text = Path("main.py").read_text() if Path("main.py").exists() else ""
KEY_REGISTRATIONS = {
    "voice handler": "handle_voice",
    "inline query handler": "InlineQueryHandler",
    "nihongo command": "nihongo",
    "memory commands": "memory",
    "research handler": "research",
    "wiki handler": "wiki",
    "callback query handler": "CallbackQueryHandler",
}
for label, token in KEY_REGISTRATIONS.items():
    check(f"main.py registers {label}", token in main_text,
          f"Add {token} registration to main.py")

# ── SECTION 3: Soul Injection ─────────────────────────────────────
soul_file = Path("SOUL.md")
check("SOUL.md exists", soul_file.exists(), "Create SOUL.md")
check("SOUL.md non-empty", soul_file.exists() and len(soul_file.read_text()) > 100,
      "SOUL.md is empty")

if Path("core/system_prompt_builder.py").exists():
    spb = Path("core/system_prompt_builder.py").read_text()
    check("system_prompt_builder references soul",
          "soul" in spb.lower() or "SOUL" in spb,
          "Inject soul_engine.get_system_prompt() into system_prompt_builder")
    check("system_prompt_builder references memory",
          "memory" in spb.lower(),
          "Inject memory_engine.read_memory() into system_prompt_builder")

# ── SECTION 4: LLM Client ────────────────────────────────────────
llm_exists = Path("llm_client.py").exists() or Path("llm_client/__init__.py").exists()
check("llm_client exists", llm_exists, "Create llm_client.py or llm_client/ package")

# ── SECTION 5: Skills Registry ──────────────────────────────────
skills_dir = Path("skills")
if skills_dir.exists():
    skill_files = list(skills_dir.glob("*.py")) + list(skills_dir.glob("**/*.py"))
    skill_files = [f for f in skill_files if f.name != "__init__.py"]
    check("skills/ has skill files", len(skill_files) > 0, "Add skill files to skills/")
    if Path("core/skill_registry.py").exists():
        sr = Path("core/skill_registry.py").read_text()
        check("skill_registry scans skills dir",
              "skills" in sr,
              "Add skills/ directory scanning to skill_registry.py")

# ── SECTION 6: Async Safety ──────────────────────────────────────
critical_files = [
    "handlers/ai.py", "handlers/voice.py", "core/memory_engine.py",
    "core/autonomous_router.py"
]
for fpath in critical_files:
    if Path(fpath).exists():
        content = Path(fpath).read_text()
        has_requests = "requests.get" in content or "requests.post" in content
        check(f"{fpath}: no blocking requests.get", not has_requests,
              f"Replace requests.get with httpx AsyncClient in {fpath}")

# ── SUMMARY ──────────────────────────────────────────────────────
print(f"\n{'═'*60}")
print(f"PASSED: {len(passed)} | FAILED: {len(failed)}")
if failed:
    print("\nFAILED CHECKS:")
    for label, hint in failed:
        print(f"  ❌ {label}")
        if hint:
            print(f"     → {hint}")
    print(f"\n⛔ Wiring incomplete. Fix all failures above.")
    sys.exit(1)
else:
    print("\n🟢 ALL WIRING CHECKS PASSED")
    sys.exit(0)
```

STEP 2 — RUN THE SCRIPT
  python scripts/verify_wiring.py

STEP 3 — FIX EVERY FAILURE
For each ❌ failure:
  Read the fix hint.
  Apply the minimum fix needed.
  Re-run the script.
  Repeat until 0 failures.

STEP 4 — MAKE IT A MAKEFILE TARGET (optional but recommended)
If Makefile or scripts/ directory exists, add:
  verify:
      python scripts/verify_wiring.py

Add to .github/workflows/ci.yml if CI exists:
  - name: Verify wiring
    run: python scripts/verify_wiring.py

STEP 5 — GENERATE FINAL REPORT
After exit 0, create WIRING_VERIFIED_[date].md:
  # Wiring Verified — [date]
  All XX checks passed.
  Script: scripts/verify_wiring.py
  Run: python scripts/verify_wiring.py → EXIT 0 ✅

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
