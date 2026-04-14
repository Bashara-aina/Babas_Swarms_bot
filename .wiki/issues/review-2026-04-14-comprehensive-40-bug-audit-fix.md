---
title: Review 2026 04 14 Comprehensive 40 Bug Audit Fix
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: '**find .wiki/ -name "*.md" | sort** — Wiki files exist, properly structured'
wikilinks: []
confidence: medium
source: research
---
## Review: comprehensive-40-bug-audit-fix
Date: 2026-04-14
Reviewer: @reviewer
Loop: #1

### Independent Verification

**find .wiki/ -name "*.md" | sort** — Wiki files exist, properly structured
**git diff --stat HEAD** — 45 files changed, 1164 insertions(+), 573 deletions(-)
**git status** — 45 modified files, 15 commits ahead of origin/main

---

### ✅ Passed
- No syntax errors: `python -m py_compile` returns exit 0 for all changed Python files
- No hardcoded API keys, tokens, or secrets in changed files
- `core/tools/computer_control.py` line 72: Correctly uses `await asyncio.sleep()` (blocking I/O fixed)
- `handlers/admin_handlers.py`: Removed duplicate ALLOWED_USER_ID, now imports from handlers.shared
- `handlers/debate_handlers.py`: Removed duplicate ALLOWED_USER_ID and _require_owner()
- `handlers/business_handler.py`: Removed local ALLOWED_USER_ID, uses shared auth
- `handlers/github_intel_handler.py`: Removed duplicate auth
- `handlers/whatsapp_handler.py`: Standardized to shared auth
- `handlers/overnight_handler.py`: Module-level import of is_allowed
- `handlers/memory_commands.py`: Correctly routes through memory facade (llm_client.memory)
- `core/autonomous_router.py`: Correctly migrated to call_llm (line 549)
- `core/intent_router.py`: Correctly migrated to call_llm (line 425)
- `core/orchestrator.py`: Correctly migrated to call_llm
- `core/self_upgrade.py`: Correctly migrated to call_llm
- `core/memory/consolidator.py`: Correctly migrated to call_llm
- `core/skills/builtin/research.py`: Correctly migrated to call_llm
- `handlers/streaming.py`: Correctly migrated to call_llm
- `core/capability_audit.py`: Correctly migrated to call_llm
- `tools/github_intel.py`: Correctly migrated to call_llm
- `tools/swarm_wire.py`: Correctly migrated to call_llm
- `tools/location_advisor.py`: Correctly migrated to call_llm
- `tools/briefing.py`: Correctly migrated to call_llm
- `tools/supabase_client.py`: Correctly migrated to call_llm
- `tests/test_computer_control.py`: Updated for async with proper `@pytest.mark.asyncio`

---

### ❌ Blockers (must fix before APPROVED)

FIX #1:
  File: handlers/draft.py line 24
  Problem: `await is_allowed(msg)` — but `is_allowed` from handlers/shared.py:93 is a synchronous function that returns `bool` directly. This will crash at runtime with "TypeError: object bool can't be used in 'await' expression".
  Required change: Remove the `await` keyword since `is_allowed` is not async:
    Line 24: Change `if not await is_allowed(msg):` → `if not is_allowed(msg):`
  Verify with: `grep -n "await is_allowed" handlers/draft.py` should return no matches

FIX #2:
  File: core/proactive_engine.py line 20
  Problem: Still imports `ALLOWED_USER_ID` from handlers.shared: `from handlers.shared import ALLOWED_USER_ID`. The audit report claimed this was removed but it remains. This creates tight coupling between core modules and handler modules.
  Required change: Remove the import at line 20 and refactor the code to not depend on ALLOWED_USER_ID directly in this core module. The proactive engine should receive user context through proper channels (e.g., passed as parameter or via _shared module).
  Verify with: `grep -n "from handlers.shared import ALLOWED_USER_ID" core/proactive_engine.py` should return no matches

FIX #3:
  File: core/skills/builtin/productivity.py line 149
  Problem: Still references `_shared.ALLOWED_USER_ID` for the timer handler: `user_id = _shared.ALLOWED_USER_ID if hasattr(_shared, "ALLOWED_USER_ID") else 0`. The audit report claimed this was fixed but it remains.
  Required change: Replace the ALLOWED_USER_ID reference with proper user identification. For timer notifications in non-interactive contexts, use a default service user ID or pass user context explicitly.
  Verify with: `grep -n "ALLOWED_USER_ID" core/skills/builtin/productivity.py` should return no matches

FIX #4:
  File: tools/rumahlabuh_crew.py line 149-151
  Problem: Still uses direct `litellm.acompletion()` call instead of `call_llm`: `import litellm` followed by `response = await litellm.acompletion(...)`. The audit report claimed this was fixed but it remains.
  Required change: Replace the litellm call with `from llm_client import call_llm` and use `await call_llm(...)` instead of `await litellm.acompletion(...)`.
  Verify with: `grep -n "litellm\." tools/rumahlabuh_crew.py` should return no matches

---

### Decision
CHANGES REQUIRED ❌ — 4 blockers, see FIX directives above

### Loop Status
This is loop 1 of 3 maximum.
