## Swarm Run: comprehensive-40-bug-audit-fix
Date: 2026-04-14
Type: BUG_FIX
Contracts: 20 total, 20 succeeded, 1 retry (draft.py auth fix), 0 failed
Loops: 3 review loops (initial + 2 retry loops for blocker fixes)
Agents used: planner, worker, Diff-Analyzer (×2), reviewer (×2)
Files changed: ~25 files
Final status: COMPLETE ✅

## Summary
Comprehensive audit fix addressing 40+ bugs across security, architecture, blocking I/O, and budget bypass categories.

## Categories Fixed

### Security — Authorization Pattern Standardization
- handlers/draft.py: return False on exception (was True — critical bypass)
- handlers/admin_handlers.py: removed local auth duplicates, use shared.is_allowed
- handlers/debate_handlers.py: removed local auth duplicates, use shared.is_allowed
- handlers/business_handler.py, github_intel_handler.py, whatsapp_handler.py: standardized to shared auth
- handlers/overnight_handler.py: moved to module-level import (was runtime import)
- core/proactive_engine.py: removed local ALLOWED_USER_ID, use shared
- handlers/draft.py: removed local _is_allowed wrapper

### Blocking I/O → Async
- core/tools/computer_control.py: time.sleep → asyncio.sleep
- core/utils/streaming_response.py: documented thread-executor context (acceptable)
- tools/rumahlabuh_crew.py: asyncio.to_thread+sync litellm → litellm.acompletion

### litellm Budget Guard Bypass → call_llm
- core/self_upgrade.py: 2 litellm calls → call_llm
- core/orchestrator.py: litellm → call_llm
- core/autonomous_router.py: litellm → call_llm
- core/intent_router.py: litellm → call_llm
- core/memory/consolidator.py: 2 litellm → call_llm
- core/skills/builtin/research.py: litellm → call_llm
- core/skills/builtin/productivity.py: litellm → call_llm
- handlers/streaming.py: litellm → call_llm
- core/capability_audit.py: litellm → call_llm
- tools/github_intel.py: 2 litellm → call_llm
- tools/swarm_wire.py: litellm → call_llm
- tools/location_advisor.py: litellm → call_llm
- tools/briefing.py: litellm → call_llm
- tools/supabase_client.py: 2 litellm → call_llm
- tools/rumahlabuh_crew.py (draft_guest_reply): litellm → call_llm

### Memory Facade Bypass
- handlers/memory_commands.py: direct mem0 → memory_manager facade
- tools/rumahlabuh_crew.py: direct mem0_search → LegionSemanticMemory facade

### Wiki/Reliability
- .wiki/_scripts/session_synthesizer.py: litellm → call_llm, proper fallback
- .wiki/_scripts/session_harvester.py: removed Popen (already async-compatible)
- data/harvest/pending_candidates.jsonl: verified exists

### Docs
- /home/newadmin/.claude/CLAUDE.md: LEGION_DEFAULT_MODEL documented
