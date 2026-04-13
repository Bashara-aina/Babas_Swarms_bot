---

---
# AUDIT 07 — Orphan & Stub Handler Plan (REVISED)
> Planner: Bashara | Date: 2026-04-12 | Files: 10 high-risk handlers

## Executive Summary

After reading all 10 handlers plus their dependencies, here are the classifications:

| File | Classification | Notes |
|------|---------------|-------|
| `swarm_handler.py` | **UTILITY** | Pure parse helper, no router needed |
| `runbook_handler.py` | **WORKING** | Full impl + deps exist |
| `streaming.py` | **BROKEN** | Line 18: `import router as agents` is wrong (no `handlers/router.py`) |
| `whatsapp_handler.py` | **WORKING** | Full impl + bridge exists |
| `overnight_handler.py` | **WORKING** | Full impl + asyncio tasks (not APScheduler) |
| `enterprise.py` | **WORKING** | All _shared attrs initialized |
| `legion_extras.py` | **WORKING** | All deps exist |
| `communications.py` | **WORKING** | Full impl + composio_hub exists |
| `session_handler.py` | **WORKING** | Full impl + mneme_session exists |
| `inline.py` | **WORKING** | Correct signature |

**CRITICAL FIX NEEDED**: `streaming.py` line 18 has `import router as agents` which will fail at import time — no `handlers/router.py` exists.

---

## Subtasks

### Subtask 1: Audit `swarm_handler.py` → @worker
**Already audited.** No fix needed — UTILITY class.
- Only contains `parse_swarm_args()` helper (34 lines)
- Used by `handlers/ai.py` lines 101-103 ✅
- No router (correct — pure utility)
- **Classification**: UTILITY

### Subtask 2: Audit `runbook_handler.py` → @worker
**Already audited.** No fix needed.
- `tools/runbook_engine.py` exists with `execute_runbook()` + `list_runbook_summaries()` ✅
- Registered in `handlers/__init__.py` line 22 ✅
- **Classification**: WORKING

### Subtask 3: Fix `streaming.py` → @worker (CRITICAL)
**File**: `/home/newadmin/swarm-bot/handlers/streaming.py`
**Issue**: Line 18: `import router as agents` — `handlers/router.py` does not exist
**Fix**: Replace with `import agents` (the `agents` top-level module)
**Additional**: Also verify line 48 `from agents import AGENT_MODELS, get_fallback_chain` — `get_fallback_chain` must be checked
**After fix**: Confirm `stream_chat` is called somewhere OR add DEPRECATED flag + comment

### Subtask 4: Audit `whatsapp_handler.py` → @worker
**Already audited.** No fix needed.
- `bridges/whatsapp_bridge.py` exists with full `WhatsAppBridge` class ✅
- Registered in `handlers/__init__.py` line 56 ✅
- **Classification**: WORKING

### Subtask 5: Audit `overnight_handler.py` → @worker
**Already audited.** No fix needed.
- `tools/overnight.py` exists with full impl ✅
- `tools/dashboard.py` exists with `build_ascii_dashboard` + `build_png_dashboard` ✅
- Background tasks use `asyncio.create_task` (lines 119, 267, 319, 380, 419) ✅
- Registered in `handlers/__init__.py` line 71 ✅
- **Classification**: WORKING

### Subtask 6: Audit `enterprise.py` → @worker
**Already audited.** No fix needed.
- All `_shared` attrs set at module level (lines 79-89 of shared.py) ✅
- Registered in `handlers/__init__.py` line 67 ✅
- **Classification**: WORKING

### Subtask 7: Audit `legion_extras.py` → @worker
**Already audited.** No fix needed.
- `core/jarvis_orchestrator.py` exists with `compose_jarvis_response` + `gather_jarvis_bundle` ✅
- `tools/simulation_tool.py` exists with `run_simulation` ✅
- Registered in `handlers/__init__.py` line 80 ✅
- **Classification**: WORKING

### Subtask 8: Audit `communications.py` → @worker
**Already audited.** No fix needed.
- `tools/composio_hub.py` exists with `get_unread_emails` + `get_calendar_events` ✅
- Registered in `handlers/__init__.py` line 52 ✅
- **Classification**: WORKING

### Subtask 9: Audit `session_handler.py` → @worker
**Already audited.** No fix needed.
- `tools/mneme_session.py` exists with all referenced functions ✅
- Registered in `handlers/__init__.py` line 62 ✅
- **Classification**: WORKING

### Subtask 10: Audit `inline.py` → @worker
**Already audited.** No fix needed.
- `llm_client.chat(text, agent_key, user_id)` signature correct ✅
- Registered in `handlers/__init__.py` line 74 ✅
- **Classification**: WORKING

### Subtask 11: Generate AUDIT07 Final Report → @reviewer
Write final report to `/home/newadmin/swarm-bot/.wiki/logs/AUDIT07_REPORT.md`
Include: all 10 handler classifications, fix applied to streaming.py, any warnings

---

## Execution Order
1. Subtasks 1-10 (audit only, all working except streaming which needs fix)
2. Subtask 3 (streaming.py fix — the only broken file)
3. Subtask 11 (final report)
