## Plan: DEEP_AUDIT_2026-04-14 — 40-Bug Comprehensive Fix

Date: 2026-04-14
Type: BUG_FIX
Context gathered:
- Read AGENTS.md (65 lines) — confirms LLM calls must go through llm_client.py
- handlers/shared.py:386 lines — has is_allowed() and allowed_cb() already
- handlers/admin_handlers.py:226 lines — has local ALLOWED_USER_ID + _require_owner duplication
- handlers/debate_handlers.py:161 lines — same pattern as admin_handlers
- handlers/draft.py:69 lines — _is_allowed() returns True on ALL exceptions (SECURITY BYPASS)
- handlers/business_handler.py, github_intel_handler.py, whatsapp_handler.py — local _is_allowed() with os.getenv()
- core/proactive_engine.py:252 lines — has local ALLOWED_USER_ID at line 23
- handlers/overnight_handler.py:264 lines — runtime import at line 29
- core/tools/computer_control.py:568 lines — time.sleep() at line 64 in _rate_limit_screenshot()
- core/utils/streaming_response.py:414 lines — _time.sleep() at lines 248, 266, 282
- core/memory/tiers.py:317 lines — sync sqlite3 (no async wrapper)
- tools/rumahlabuh_crew.py:391 lines — asyncio.to_thread with sync litellm at line 154-155
- .wiki/_scripts/session_synthesizer.py:361 lines — direct litellm + no budget + silent LLM failure
- data/harvest/pending_candidates.jsonl — 0 bytes (empty file)
- handlers/voice.py:257 lines — direct OpenAI SDK (needs checking)
- tools/swarm_wire.py:545 lines — dynamic **kwargs validation needed
- handlers/memory_commands.py:228 lines — direct mem0 calls at lines 70-72, 94-97
- tools/rumahlabuh_crew.py:119 — direct mem0_search import
- .claude/CLAUDE.md — exists at /home/newadmin/.claude/CLAUDE.md (37 lines)
- LEGION_DEFAULT_MODEL found in core/opencode_bridge.py but not in CLAUDE.md

Risk assessment:
- Authorization fixes are high-risk (could break bot access if done wrong)
- Blocking I/O in async context could cause performance issues
- Direct litellm calls bypass budget tracking (157 call sites is significant)
- Memory facade bypass means mem0 could be called without the budget manager knowing

Approach: 15 contracts grouped by fix strategy, executing in dependency order:
1. First establish the shared auth pattern (shared.py is already correct)
2. Fix authorization duplicates (admin_handlers, debate_handlers, draft security bypass)
3. Fix blocking I/O (computer_control, streaming_response, progress_tracker)
4. Fix litellm bypasses (llm_client.call_llm is the central entry point)
5. Fix memory facade bypasses
6. Fix remaining items (wiki scripts, docs)
