# AUDIT 05 — Core Module Wiring
**Date:** 2026-04-12
**Status:** PLANNED

## Goal
Every file in `core/` is actively used; every export matches what callers import.

---

## Findings (Pre-planning)

### ✅ Key Module Imports — ALL PASS
```bash
python -c "from core import soul_engine, memory_engine, skill_registry, system_prompt_builder, intent_router"
# → All OK
```

### ✅ soul_engine → system_prompt_builder wire
- `build_soul_context()` returns **5557 chars** (non-empty, loads SOUL.md correctly)
- `read_beliefs()`, `get_pending_followups()`, `get_emotional_state()`, `get_time_context()` all work

### ✅ memory_engine → callers
- `MemoryEngine` instantiated with `store()`, `search()`, `get_context_window()` methods present
- Called by `llm_client/__init__.py` (line 1386), `handlers/system.py` (line 454), tests

### ⚠️ skill_registry → autonomous_router wire
- `get_skill()` is referenced in AGENTS.md but **does not exist** in `core/skill_registry.py`
- Only `load_skills()`, `skills_prompt_block()`, `skills_prompt_block_for_query()` exist
- `autonomous_router` imports `SKILL_PATTERNS` from `core.skills` (the package, not `skill_registry`)

### ⚠️ intent_router coverage
- Covers all major intents (COMPUTER_CONTROL, CODE_GENERATION, DEEP_REASONING, etc.)
- Returns structured `IntentResult` with `intent`, `confidence`, `method`, `needs_tools`, `needs_research`
- 21 intent types defined

### ⚠️ Orphan modules identified (need review)
From 70+ core/*.py files, these have **zero internal imports** (no other core/ file imports them):
- `core/agent.py` — standalone agent class
- `core/capability_audit.py` — scheduled task, no callers
- `core/character_voice.py` — unclear purpose
- `core/emotion_tracker.py` — only in tests
- `core/error_humanizer.py` — humanizes errors, no callers found
- `core/health.py` — separate from `health_check.py`, no callers
- `core/intent_classifier.py` — possibly redundant with `intent_router.py`
- `core/natural_command_parser.py` — no callers found
- `core/openai_agents_bridge.py` — lazy import only
- `core/opencode_bridge.py` — hooks into OpenCode, no internal callers
- `core/research_policy.py` — policy file, no callers
- `core/self_awareness_gate.py` — no callers found
- `core/swarm.py` — unclear swarm core, no callers
- `core/task_router.py` — only in tests
- `core/tmp_cleanup.py` — only in tests
- `core/watchdog.py` — daemon-like, no callers
- `core/wiki_auto_ingest.py` — possibly dead after wiki refactor
- `core/wiki_bridge.py` — no callers found
- `core/wiki_manager.py` — called from `handlers/wiki_handler.py` (external)

### ⚠️ Export mismatches in core/__init__.py
- `core/__init__.py` only exports: `classify_complexity`, `select_model` (from `model_router`), `FallbackChain`, `get_fallback_chain` (from `fallback_chain`)
- These are **NOT** imported by the standard "from core import X" pattern above — but work via direct module import
- Missing re-export: `soul_engine`, `memory_engine`, `intent_router`, `autonomous_router` are commonly imported as `from core import X` in tests

---

## Atomic Subtasks

### [SUBTASK-1] Verify soul_engine → system_prompt_builder wire
**Action:** Confirm `get_system_prompt()` in `system_prompt_builder.py` calls `build_soul_context()` and returns non-empty string. Verify SOUL.md loading path is correct.
**Files:** `core/system_prompt_builder.py`, `core/soul_engine.py`
**Method:** Read both files, trace the call chain, run test call

### [SUBTASK-2] Audit orphan modules — Classify as wire-in or disable
**Action:** For each orphan module, grep entire codebase for any import/reference. If callers exist, wire them in. If not, mark for disable/remove from repo plan.
**Orphans to check:** `agent.py`, `capability_audit.py`, `character_voice.py`, `emotion_tracker.py`, `error_humanizer.py`, `health.py`, `intent_classifier.py`, `natural_command_parser.py`, `openai_agents_bridge.py`, `opencode_bridge.py`, `research_policy.py`, `self_awareness_gate.py`, `swarm.py`, `task_router.py`, `tmp_cleanup.py`, `watchdog.py`, `wiki_auto_ingest.py`, `wiki_bridge.py`
**Method:** Grep for each module name in all .py files

### [SUBTASK-3] Verify memory_engine read_memory/write_memory exist
**Action:** Confirm `MemoryEngine` has working `store()` and `search()` methods that actually persist/retrieve data. Check that `read_memory`/`write_memory` (if those are the intended names) exist or are aliased.
**Files:** `core/memory_engine.py`
**Method:** Read class interface, verify all public methods are implemented

### [SUBTASK-4] Audit skill_registry → autonomous_router/intent_router
**Action:** Verify `skill_registry.py` exports what callers expect. Specifically check if `get_skill()` should exist (AGENTS.md references it) and whether `SKILL_PATTERNS` is the correct export from `core.skills` package.
**Files:** `core/skill_registry.py`, `core/skills/__init__.py`, `core/autonomous_router.py`, `core/intent_router.py`
**Method:** Read all three files, verify named exports match imports

### [SUBTASK-5] Verify system_prompt_builder returns complete messages[] list
**Action:** Confirm `SystemPromptBuilder.build()` returns a properly formatted string (or messages[] list if that interface exists). Check if there's a `build_messages()` variant that returns a list of message dicts.
**Files:** `core/system_prompt_builder.py`
**Method:** Read `SystemPromptBuilder` class, check return type of `build()` method

### [SUBTASK-6] Verify intent_router covers all major intents
**Action:** Confirm intent_router's `Intent` enum covers all major intent categories. Verify `classify_intent()` returns `IntentResult` with structured data including `intent`, `confidence`, `method`, `needs_tools`, `needs_research`.
**Files:** `core/intent_router.py`
**Method:** Read intent definitions and classify_intent pipeline

### [SUBTASK-7] Check export/import mismatches across core/
**Action:** For each module in `core/`, verify that all `__all__` exports (or all public symbols) actually exist in the source file. Catch NameError, AttributeError, ImportError issues.
**Files:** All core/*.py files with exports
**Method:** Grep `__all__` definitions, verify each exported name exists in the file

### [SUBTASK-8] Fix broken wires — any import errors found
**Action:** Based on findings from SUBTASK-1 through SUBTASK-7, fix any broken import/export wires found.
**Files:** TBD based on findings
**Method:** Edit files to fix broken wires

### [SUBTASK-9] Verify import verification command
**Action:** Run `python -c "from core import soul_engine, memory_engine, skill_registry, system_prompt_builder, intent_router"` — confirm it passes cleanly.
**Files:** `core/__init__.py`, all key modules
**Method:** Execute the verification command

### [SUBTASK-10] Write audit findings to .wiki/logs/
**Action:** Document all findings, orphan classifications, wire fixes, and final verification results to `.wiki/logs/audit-05-findings.md`.
**Files:** `.wiki/logs/audit-05-findings.md`
**Method:** Write summary markdown file

---

## Review
All changes → assign to @reviewer
