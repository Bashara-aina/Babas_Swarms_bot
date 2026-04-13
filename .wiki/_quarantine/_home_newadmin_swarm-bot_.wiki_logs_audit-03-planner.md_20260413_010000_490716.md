---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/audit-03-planner.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.490742"
}
---

# AUDIT 03 — Router Layer Coverage
## Planner Subtask Decomposition

## Current State Summary

### Router Chain (ACTUAL):
```
message_handler.py
  └── task_router.py (OPTIONAL via LEGION_TASK_ROUTER_ENABLED=1)
  └── autonomous_router.py (always active) → dispatches to handlers
```

### Router Chain (DECLARED vs REALITY):
| File | Role | Status |
|------|------|--------|
| `router.py` (root) | Thin shim re-exporting from `agents.py` | NOT a message router |
| `core/autonomous_router.py` | Primary skill router | ✅ ACTIVE |
| `core/intent_router.py` | Intent classification | ⚠️ NOT in main flow (imported by llm_client only) |
| `core/task_router.py` | Optional pre-router | ⚠️ OPTIONAL (disabled by default) |

### Broken Wires Identified:
1. **`intent_router.py`** — defined but never called in message_handler
2. **`task_router.py`** — disabled by default (LEGION_TASK_ROUTER_ENABLED=0)
3. **`router.py`** (root) — imports agents but never routes messages
4. **`intent_router.py`** — has richer Intent enum but is bypassed

---

## ATOMIC SUBTASKS

### Subtask 1: Audit router.py (root) — Confirm it's a dead shim
**File:** `/home/newadmin/swarm-bot/router.py`
**Action:** 
- Read router.py completely
- Confirm it's ONLY a re-export shim (no message routing logic)
- Search entire codebase for callers that import from this `router.py` (root) expecting message routing
- Document findings: if no one calls it for message routing, mark as "dead legacy shim" — NOT a broken wire

**Deliverable:** Report whether router.py root is actually used in message flow or is dead code

---

### Subtask 2: Audit intent_router.py integration
**File:** `/home/newadmin/swarm-bot/core/intent_router.py`
**Action:**
- Search for ALL imports of `intent_router.py` in the codebase
- Check if `classify_intent`, `classify_intent_fast`, or `IntentRouter` are called in:
  - `handlers/message_handler.py`
  - `llm_client/__init__.py` (found: line 873, 999)
  - Any other handler files
- Document exact line numbers where it's imported vs actually called
- If it's imported but never `await route()` or `classify_intent()` called → broken wire

**Deliverable:** List of all import + call sites with line numbers

---

### Subtask 3: Audit task_router.py integration
**File:** `/home/newadmin/swarm-bot/core/task_router.py`
**Action:**
- Read message_handler.py lines 146-176
- Confirm `LEGION_TASK_ROUTER_ENABLED` is off by default
- Check if any OTHER code path enables task_router
- If task_router returns `None` for SIMPLE_CHAT, trace where that None goes

**Deliverable:** Confirm task_router is properly gated and its None return is handled

---

### Subtask 4: Map autonomous_router SKILL_PATTERNS → handler keys
**File:** `/home/newadmin/swarm-bot/core/autonomous_router.py` lines 24-452
**Action:**
- Extract every `skill_name` and its `handler` value from SKILL_PATTERNS
- Cross-reference each `handler` key with actual code in `message_handler.py`
- Find ALL handler dispatch blocks (lines 199-358) and map them
- Mark any handler key that has NO dispatch block

**Handler keys in SKILL_PATTERNS:**
| Skill | Handler | Has Dispatch? |
|-------|---------|----------------|
| computer_control | /do | ✅ line 222 |
| deep_research | /research | ✅ line 252 |
| code_generation | /run | ✅ line 228 |
| deep_reasoning | /think | ✅ line 236 |
| multi_agent_swarm | /swarm | ✅ line 244 |
| memory_search | memory_recall | ✅ line 200 |
| system_control | /cmd | ✅ line 309 |
| email_management | email | ✅ line 321 |
| runbook_maintenance | runbook | ✅ line 326 |
| business_query | business | ✅ line 331 |
| location_advice | location | ✅ line 336 |
| whatsapp_action | whatsapp | ✅ line 341 |
| github_intel | github_intel | ✅ line 346 |
| strategic_simulation | simulation | ✅ line 260 |
| jarvis_orchestrate | jarvis | ✅ line 274 |
| codebase_understanding | codebase_reader | ✅ line 351 |
| debate_opinion | debate | ✅ line 301 |
| conversation | chat | ✅ line 194 (implicit) |

**Deliverable:** Confirm all 18 handler keys have dispatch blocks

---

### Subtask 5: Audit ALL return values in task_router
**File:** `/home/newadmin/swarm-bot/core/task_router.py`
**Action:**
- Read every async method: `_run_research`, `_run_code`, `_run_browser`, `_run_document`, `_run_computer`, `_run_simulation`, `_run_debate`, `_run_multi_step`
- Confirm each returns `str` (not None)
- Check line 176: `return None` — confirm this is only for SIMPLE_CHAT case (correct fallback)
- Check caller in message_handler.py lines 166-174: does it properly handle `routed is not None`?

**Deliverable:** List each _run_* method and its return type, confirm no None leak

---

### Subtask 6: Audit return values in autonomous_router
**File:** `/home/newadmin/swarm-bot/core/autonomous_router.py`
**Action:**
- `analyze()` returns `SkillMatch` (guaranteed, lines 498-511)
- `analyze_async()` returns `SkillMatch` (guaranteed, lines 513-533)
- `_llm_classify()` returns `SkillMatch | None` (line 535) — but this is caught internally
- Confirm ALL paths return a SkillMatch (never None)

**Deliverable:** Confirm analyze() and analyze_async() always return SkillMatch

---

### Subtask 7: Audit intent_router return values
**File:** `/home/newadmin/swarm-bot/core/intent_router.py`
**Action:**
- `classify_intent_fast()` returns `IntentResult` (lines 317-381) — guaranteed
- `classify_intent_llm()` returns `IntentResult` (lines 400-464) — guaranteed
- `classify_intent()` returns `IntentResult` (lines 467-493) — guaranteed
- `IntentRouter.route()` returns `IntentResult` (lines 502-504)
- `IntentRouter.route_sync()` returns `IntentResult` (lines 506-508)
- Confirm no path returns None

**Deliverable:** Confirm all intent_router functions return non-None values

---

### Subtask 8: Check for unhandled handler keys
**File:** `/home/newadmin/swarm-bot/handlers/message_handler.py`
**Action:**
- Read lines 350-358 (the generic fallback)
- If handler_key is something unexpected (not in known list), does it fall through to generic fallback correctly?
- Trace: if `handler_key = "something_unexpected"` and `skill_match.confidence >= 0.4`, where does it go?

**Deliverable:** Confirm fallback path handles unknown handler keys gracefully

---

### Subtask 9: Verify handler imports at top of message_handler.py
**File:** `/home/newadmin/swarm-bot/handlers/message_handler.py`
**Action:**
- Check imports for all dispatched handlers: email, runbook, business, location, whatsapp, github_intel, codebase_reader
- Confirm each import is at top or properly imported inside the handler function
- Note any imports that happen inside functions (lazy imports) vs top-level

**Deliverable:** List all lazy imports (inside functions) vs top-level imports for handler functions

---

### Subtask 10: Document the complete routing diagram
**Action:** Based on all findings, draw the COMPLETE routing chain:
```
User message
    │
    ▼
message_handler.handle_plain_message()
    │
    ├─[LEGION_TASK_ROUTER_ENABLED=1?]──► task_router.route() ──► _run_* methods
    │                                         │
    │                                    returns str or None
    │                                         │
    │◄──── returns None ──────────────────────┘
    │
    ▼
autonomous_router.analyze_async()
    │
    ├─► keyword scoring ──► SkillMatch
    │
    └─► LLM fallback (if confidence<0.55 or words>30) ──► SkillMatch
    │
    ▼
SKILL_PATTERNS[skill_name]["handler"]
    │
    ├─► /do ──────────► _run_agent_loop()
    ├─► /run ─────────► _execute_chat(forced_agent="coding")
    ├─► /think ───────► _execute_chat(forced_agent="think")
    ├─► /swarm ───────► _execute_chat(forced_agent="architect")
    ├─► /research ────► _execute_chat(forced_agent="researcher")
    ├─► /cmd ─────────► run_shell_command()
    ├─► memory_recall ► memory.search() → _execute_chat()
    ├─► simulation ───► run_simulation_agent()
    ├─► jarvis ───────► gather_jarvis_bundle() → compose_jarvis_response()
    ├─► debate ───────► _execute_chat(forced_agent="debate")
    ├─► email ────────► _handle_email()
    ├─► runbook ──────► _handle_runbook()
    ├─► business ─────► _handle_business()
    ├─► location ─────► _handle_location()
    ├─► whatsapp ─────► _handle_whatsapp()
    ├─► github_intel ─► _handle_github_intel()
    ├─► codebase_reader► _handle_codebase_understanding()
    └─► chat (default)► _execute_chat()
```

**Deliverable:** Final routing diagram with file:line references

---

## SUMMARY OF FIXES NEEDED

Based on audit so far, fixes required:

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | `intent_router.py` not integrated | message_handler.py | Either integrate it OR document it's deprecated |
| 2 | `task_router.py` disabled by default | message_handler.py or env | Enable by default OR remove dead code |
| 3 | `router.py` (root) is a dead shim | router.py | Either wire it into message flow OR document it's legacy |

**No fixes needed for:**
- autonomous_router return values (all paths return SkillMatch)
- task_router return values (all _run_* return str, None only for SIMPLE_CHAT which is correct)
- intent_router return values (all paths return IntentResult, never None)
- Handler key dispatch coverage (all 18 keys have dispatch blocks)

---

*Generated by Planner for AUDIT 03 — 2026-04-12*
