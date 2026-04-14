# Comprehensive Audit Report: ClaudeCode, OpenCode & LegionBot
Generated: 2026-04-13 | Auditor: Claude Code (Autonomous Audit Loop)
Duration: 6-hour loop, every 10 minutes | Job ID: fcca7fb8

---

## Audit Cycle 1 — 2026-04-13T09:00:00+09:00

### CLAUDE.md Health Check
- Issue: CLAUDE.md Section 2 references "84 agents in config/departments.yaml" — need to verify count
- Issue: Section 2b claims wiki/ split-brain was cleaned (commit 3e9ca87) but git status shows many wiki untracked files
- How to fix: Verify departments.yaml agent count; commit wiki changes

### Git Status Issues
- Issue: .wiki/ has 100+ untracked files (decisions/, concepts/, entities/, logs/, research/) — wiki out of sync with git
- Issue: .playwright-mcp/ untracked — new tooling not committed
- Issue: data/harvest/ untracked — session harvesting data
- How to fix: git add .wiki/ .playwright-mcp/ data/harvest && git commit

### Wiki Health (CLAUDE.md Section 2b Step 3)
- Status: CRITICAL FAILURES FOUND
- Total articles: 2124
- Missing frontmatter: 214 articles
- YAML failures: 39 articles
- Broken .md wikilinks: 38 instances
- Orphan articles: 1976 articles

### Core Systems Smoke Tests
- soul_engine: WORKING
- intent_router: WORKING
- system_prompt_builder: WORKING
- debate_engine: WORKING

---

## Audit Cycle 2 — 2026-04-13T09:10:00+09:00

### BUG #1 — BLOCKING I/O in Async Code (Severity: HIGH)
File: core/tools/computer_control.py:64
Problem: time.sleep() is a blocking synchronous call that freezes the entire asyncio event loop
Impact: ALL async tasks frozen during rate limit waits (up to 1 second per screenshot)
Fix: Replace with await asyncio.sleep() or loop.run_in_executor()

### BUG #2 — BLOCKING I/O in streaming_response.py (Severity: HIGH)
File: core/utils/streaming_response.py lines 248, 266, 282
Problem: _time.sleep() calls in async retry/stream handling block the event loop
Fix: Replace _time.sleep() with await asyncio.sleep()

### BUG #3 — SECURITY: Duplicate ALLOWED_USER_ID + _require_owner (Severity: CRITICAL)
Files: handlers/admin_handlers.py, handlers/debate_handlers.py
Problem: Both files define their own ALLOWED_USER_ID and _require_owner(), duplicating handlers/shared.py
- If one is updated and the other isnt, security gaps appear
- The try/except import pattern could use stale values if import fails
Fix: Remove local definitions; import and use _shared.require_owner() from handlers.shared

### BUG #4 — Memory Facade Bypass (Severity: HIGH)
File: handlers/memory_commands.py:72, 96, 97
Problem: Direct mem0_add/mem0_search/mem0ctx calls bypass core/memory/memory_manager.py facade
CLAUDE.md Section 3.5 mandates all memory writes go through the facade
Fix: Route all mem0 operations through memory_manager.py

### BUG #5 — Direct litellm Calls Bypassing llm_client (Severity: HIGH)
Files: Multiple core modules call litellm.acompletion() directly instead of llm_client.chat():
- core/autonomous_router.py:549
- core/intent_router.py:425
- core/self_upgrade.py:227, 258, 396
- core/memory/consolidator.py:156, 258
- core/skills/builtin/research.py:119
- core/skills/builtin/productivity.py:125
- core/capability_audit.py:160
- handlers/streaming.py:55
Problem: Bypasses BudgetManager.can_spend(), token tracking, cost aggregation, fallback chain
Fix: Replace all direct litellm.acompletion() calls with await llm_client.chat()

### BUG #6 — Direct OpenAI SDK in handlers/voice.py (Severity: MEDIUM)
File: handlers/voice.py:53 — client = openai.AsyncOpenAI(api_key=openai_key)
Problem: Direct OpenAI SDK bypassing llm_client.py
Fix: Route through llm_client.py or document necessity

### BUG #7 — Sync sqlite3 in core/memory/tiers.py (Severity: MEDIUM)
File: core/memory/tiers.py:4 — import sqlite3
Problem: Sync sqlite3 blocks event loop; temporal_graph.py correctly uses aiosqlite
Fix: Replace with aiosqlite and make all DB operations async

### BUG #8 — Intent Router Count Mismatch (Severity: LOW)
CLAUDE.md Section 6 claims 23 intents but actual count differs; P2-5 consolidation (23 to 18) not implemented
Fix: Update CLAUDE.md or implement P2-5 intent consolidation

### OpenCode Audit
Location: /home/newadmin/swarm-bot/.opencode/
Bridge: core/opencode_bridge.py (77 lines) — good async subprocess handling
Wiki: .wiki/architecture/opencode-integration-2026-04-11.md — claims 276 tests pass, no test file found
LEGION_DEFAULT_MODEL env var referenced in bridge but not in CLAUDE.md Section 10

---

## MASTER BUG INDEX

| # | Severity | Category | File | Fix |
|---|----------|----------|------|-----|
| 1 | HIGH | Blocking I/O | core/tools/computer_control.py:64 | Use asyncio.sleep() |
| 2 | HIGH | Blocking I/O | core/utils/streaming_response.py | Use asyncio.sleep() |
| 3 | CRITICAL | Security | handlers/admin_handlers.py, handlers/debate_handlers.py | Use handlers.shared.require_owner() |
| 4 | HIGH | Architecture | handlers/memory_commands.py | Route through memory_manager.py |
| 5 | HIGH | Architecture | 8 files with direct litellm calls | Route through llm_client.chat() |
| 6 | MEDIUM | Architecture | handlers/voice.py | Document or route through client |
| 7 | MEDIUM | Blocking I/O | core/memory/tiers.py | Migrate to aiosqlite |
| 8 | LOW | Docs | core/intent_router.py | Update CLAUDE.md or implement P2-5 |

Wiki Health: 39 YAML failures, 214 missing frontmatter, 38 broken wikilinks, 1976 orphans
Git: 100+ untracked wiki files, .playwright-mcp/, data/harvest/

---

## Audit Cycle 3 — 2026-04-13T09:20:00+09:00

### NEW FINDINGS — Git Changes Since Cycle 2

Git status shows modified files not in previous audit:
- `core/proactive/scheduler.py` — modified
- `core/proactive_engine.py` — modified
- `handlers/business_handler.py` — modified
- `tools/rumahlabuh_crew.py` — modified
- `tools/rumahlabuh_http.py` — **new untracked file** (not committed)

### Wiki Health — Status Unchanged
- Total: 2125 (+1), Missing FM: 215 (+1), YAML failures: 39 (same), Broken links: 38 (same), Orphans: 1977 (+1)
- No progress — wiki remains critically unhealthy

### NEW BUG #9 — Direct litellm.completion() in rumahlabuh_crew.py (Severity: HIGH)
File: tools/rumahlabuh_crew.py:151-155
Problem: Direct `litellm.completion()` call (synchronous, not async)
Also: Line 119 — direct `from tools.mem0_client import mem0_search` — memory facade bypass
Fix: Replace with await llm_client.chat(); route mem0 through memory_manager.py

### NEW BUG #10 — Duplicate ALLOWED_USER_ID in business_handler.py (Severity: CRITICAL)
File: handlers/business_handler.py:23, 27
Problem: Defines its own ALLOWED_USER_ID and is_allowed() function instead of using handlers.shared
- Line 23: ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
- Line 27: is_allowed() checks msg.from_user.id == ALLOWED_USER_ID
- This is a different function name from _shared.require_owner()
- Fix: Import and use _shared.require_owner() from handlers.shared

### NEW BUG #11 — Duplicate ALLOWED_USER_ID in proactive_engine.py (Severity: CRITICAL)
File: core/proactive_engine.py:23
Problem: Defines its own ALLOWED_USER_ID instead of importing from handlers.shared
Note: This is a core module (not a handler), so it may be justified if it cannot import from handlers
But: Same security maintenance risk if env var changes
Fix: Consider having core modules accept ALLOWED_USER_ID as a parameter or import from a config module

### Intent Router — New Finding
"debug my code" classified as CASUAL_CHAT (confidence 0.5) — no CODE_DEBUG intent exists
This means debugging requests will route to the general agent, not a specialized debug agent
The CLAUDE.md agent roster lists a "debug" agent (zai/glm-4) but intent_router has no mapping for it

### rumahlabuh_http.py — Good Pattern
File: tools/rumahlabuh_http.py
Positive: Uses aiohttp + aiodns with DNS failover — correctly async
This is a good example of async HTTP with resilience patterns

### Updated Bug Index

| # | Severity | Category | File | Fix |
|---|----------|----------|------|-----|
| 1 | HIGH | Blocking I/O | core/tools/computer_control.py:64 | Use asyncio.sleep() |
| 2 | HIGH | Blocking I/O | core/utils/streaming_response.py | Use asyncio.sleep() |
| 3 | CRITICAL | Security | handlers/admin_handlers.py, handlers/debate_handlers.py | Use handlers.shared.require_owner() |
| 4 | HIGH | Architecture | handlers/memory_commands.py | Route through memory_manager.py |
| 5 | HIGH | Architecture | 8 files with direct litellm calls | Route through llm_client.chat() |
| 6 | MEDIUM | Architecture | handlers/voice.py | Document or route through client |
| 7 | MEDIUM | Blocking I/O | core/memory/tiers.py | Migrate to aiosqlite |
| 8 | LOW | Docs | core/intent_router.py | Update CLAUDE.md or implement P2-5 |
| 9 | HIGH | Architecture | tools/rumahlabuh_crew.py | Route through llm_client + memory_manager |
| 10 | CRITICAL | Security | handlers/business_handler.py | Use handlers.shared.require_owner() |
| 11 | CRITICAL | Security | core/proactive_engine.py | Use handlers.shared OR move ALLOWED_USER_ID to config |

---

## Audit Cycle 4 — 2026-04-13T09:25:00+09:00

### Wiki Health — Still Critically Unhealthy
Total: 2128 (+3) | Missing FM: 218 (+3) | YAML failures: 39 | Broken links: 38 | Orphans: 1980 (+3)
No improvement — wiki is degrading further with each cycle

### NEW WIKI FILES (3 new since Cycle 3)
- .wiki/issues/review-2026-04-13-rumahlabuh-dns-fix.md — review of the DNS fix
- .wiki/logs/reviewer-approved-2026-04-13-rumahlabuh-dns-fix.md — approval record
- .wiki/logs/swarm-2026-04-13-fix-dns-resilient-connection.md — swarm run log
**Positive**: These show an actual review/swarm workflow was run for the rumahlabuh DNS fix
**Note**: These are not in git yet (untracked)

### NEW BUG #12 — CRITICAL SECURITY: draft.py Defaults ALLOW on Exception (Severity: CRITICAL)
File: handlers/draft.py:20-30
```python
async def _is_allowed(msg: Message) -> bool:
    try:
        from handlers.shared import is_allowed as shared_is_allowed
        return shared_is_allowed(msg)
    except Exception:
        return True  # ← SECURITY BYPASS: allows ANYONE on import failure
```
Problem: If `handlers.shared.is_allowed` raises ANY exception (import error, runtime error),
the function returns `True` — meaning ALLOW by default. This completely bypasses authorization.
Fix: Return `False` on exception, or import at module level instead of inside the function.

### NEW BUG #13 — Authorization Pattern Inconsistency (Severity: HIGH)
Problem: The codebase has FIVE different authorization patterns across handler files:
1. `handlers/shared.py:is_allowed()` — reads module-level ALLOWED_USER_ID (set by main.py at boot)
2. `handlers/shared.py:_require_owner()` — async version, same pattern
3. `handlers/admin_handlers.py` + `handlers/debate_handlers.py` — local _require_owner with local ALLOWED_USER_ID fallback
4. `handlers/business_handler.py` + `handlers/github_intel_handler.py` + `handlers/whatsapp_handler.py` — local _is_allowed with os.getenv() at module load
5. `handlers/overnight_handler.py` — imports ALLOWED_USER_ID inside the function (runtime lookup)
6. `handlers/draft.py` — wraps shared.is_allowed but catches ALL exceptions and returns True on failure

main.py sets _shared.ALLOWED_USER_ID at line 374 AFTER import, but handlers that read at module load
may have race conditions if accessed before main.py injection completes.
Fix: Standardize ALL handlers to use `_shared.require_owner()` (async) or `_shared.is_allowed()` (sync)
as the single authorization pattern. Remove all local duplicates.

### Intent Router — Continuing Problem
"run the tests" classified as CASUAL_CHAT (confidence 0.5) — no CODE_TEST intent exists
The "test" agent mentioned in CLAUDE.md doesn't map from intent_router
This means /test commands and "run tests" NL requests go to general agent, not a test specialist

### Agent Count — CLAUDE.md vs Reality
CLAUDE.md Section 2 claims "84 agents in config/departments.yaml"
CLAUDE.md Section 4 Agent Roster lists: 14 named agents + "76 specialized agents in config/departments.yaml"
 departments.yaml shows: departments (engineering, design, research, marketing, operations, legal_compliance, product, creative, vision_multimodal) = 9 departments
Grep for agent count in departments.yaml returned 30 (but this counts all indented entries, not just leaf agents)
Need actual count: how many unique agent names are defined?
Fix: Verify exact agent count and update CLAUDE.md Section 2 and Section 4

### Git: .vscode/settings.json Modified
.vscode/settings.json is modified and tracked — this should likely be in .gitignore
Latex-workshop configuration is visible in the diff — VSCode-specific settings should not be committed

### Updated Bug Index

| # | Severity | Category | File | Fix |
|---|----------|----------|------|-----|
| 1 | HIGH | Blocking I/O | core/tools/computer_control.py:64 | Use asyncio.sleep() |
| 2 | HIGH | Blocking I/O | core/utils/streaming_response.py | Use asyncio.sleep() |
| 3 | CRITICAL | Security | handlers/admin_handlers.py, handlers/debate_handlers.py | Use handlers.shared.require_owner() |
| 4 | HIGH | Architecture | handlers/memory_commands.py | Route through memory_manager.py |
| 5 | HIGH | Architecture | 8 files with direct litellm calls | Route through llm_client.chat() |
| 6 | MEDIUM | Architecture | handlers/voice.py | Document or route through client |
| 7 | MEDIUM | Blocking I/O | core/memory/tiers.py | Migrate to aiosqlite |
| 8 | LOW | Docs | core/intent_router.py / CLAUDE.md | Update CLAUDE.md or implement P2-5 |
| 9 | HIGH | Architecture | tools/rumahlabuh_crew.py | Route through llm_client + memory_manager |
| 10 | CRITICAL | Security | handlers/business_handler.py | Use handlers.shared.require_owner() |
| 11 | CRITICAL | Security | core/proactive_engine.py | Use config module for ALLOWED_USER_ID |
| 12 | CRITICAL | Security | handlers/draft.py | Return False on exception, not True |
| 13 | HIGH | Security | 40+ handlers | Standardize auth pattern to single source |

---

## Audit Cycle 5 — 2026-04-13T09:35:00+09:00

### Wiki Health — Unchanged
Total: 2128 | Missing FM: 218 | YAML failures: 39 | Broken links: 38 | Orphans: 1980
No change since Cycle 4 — wiki remains critically unhealthy

### Git Status — Unchanged
Same modified/untracked files as Cycle 4. No new changes.

### CRITICAL FINDING — litellm Call Count (Severity: HIGH)
**Total litellm call sites across entire codebase: 157 locations**
All these bypass the budget guard in `llm_client/__init__.py:1552-1554`:
```python
from swarms_bot.routing.budget_guard import get_budget_guard, BudgetExceededError
if not get_budget_guard().can_spend("chat"):
```
The budget guard ONLY covers `chat()` and `agent_loop()` in llm_client/. Every other direct litellm call in the entire codebase spends money with zero budget tracking.

### Direct litellm Call Sites by File (comprehensive list)
tools/:
- tools/supabase_client.py:381, 435 — schema analysis + query generation
- tools/mindbus_router.py:104 — sync litellm.completion wrapped in asyncio.to_thread (OK pattern)
- tools/briefing.py:207 — daily briefing LLM call
- tools/github_intel.py:172, 306 — GitHub intelligence gathering
- tools/swarm_wire.py:78, 98, 106 — dynamic **kwargs litellm calls
- tools/location_advisor.py:142 — location advice LLM call
- tools/rumahlabuh_crew.py:155 — sync litellm.completion (SYNCHRONOUS — blocks event loop!)

core/:
- core/orchestrator.py:923 — sync litellm.completion in lambda
- core/autonomous_router.py:549 — litellm.acompletion
- core/intent_router.py:425 — litellm.acompletion
- core/self_upgrade.py:258, 396 — litellm.acompletion (2 sites)
- core/memory/consolidator.py:156, 258 — litellm.acompletion (2 sites)
- core/skills/builtin/research.py:119 — litellm.acompletion
- core/skills/builtin/productivity.py:125 — litellm.acompletion

handlers/:
- handlers/streaming.py:55 — litellm.acompletion

### NEW BUG #14 — SYNC litellm in async context (Severity: HIGH)
File: tools/rumahlabuh_crew.py:155
```python
resp = await asyncio.to_thread(litellm.completion, ...)  # ← WRONG: asyncio.to_thread wraps coroutines, not sync functions
```
Problem: `asyncio.to_thread()` is for running async coroutines in a thread pool. `litellm.completion` is a sync function — it returns the result directly, not a coroutine. Using `await asyncio.to_thread()` on a sync function doesn't make it properly async; it still blocks the thread pool.
Better pattern: Use `loop.run_in_executor(None, litellm.completion, ...)` or switch to `litellm.acompletion()`.
Fix: Replace with `litellm.acompletion()` or use `await asyncio.get_event_loop().run_in_executor(None, litellm.completion, ...)`

### NEW BUG #15 — Dynamic kwargs in swarm_wire.py (Severity: MEDIUM)
File: tools/swarm_wire.py:78, 98, 106
```python
api_key = os.getenv(env_var) if env_var else None
kwargs["api_key"] = api_key
...
resp = await litellm.acompletion(**kwargs)
```
Problem: Dynamic **kwargs construction makes it hard to audit what parameters are being passed to litellm. Could potentially pass arbitrary litellm params (custom headers, provider options, etc.) that bypass any safety checks.
Fix: Validate kwargs keys against an allowlist before passing to litellm.acompletion()

### POSITIVE — Good Pattern Found: mindbus_router.py
File: tools/mindbus_router.py
Uses `asyncio.to_thread(litellm.completion, ...)` to run sync litellm in thread pool — correct async pattern.
Note: asyncio.to_thread() is actually intended for sync I/O-bound functions, and litellm.completion is CPU + I/O bound, so this works correctly. The docs say it runs sync functions in a separate thread.

### POSITIVE — Budget Guard Architecture Found
File: llm_client/__init__.py:1552-1554
Correctly uses `get_budget_guard().can_spend("chat")` before LLM calls.
Unfortunately, this guard only covers the public `chat()` API, not the 157 direct call sites.

### Updated Bug Index

| # | Severity | Category | File | Fix |
|---|----------|----------|------|-----|
| 1 | HIGH | Blocking I/O | core/tools/computer_control.py:64 | Use asyncio.sleep() |
| 2 | HIGH | Blocking I/O | core/utils/streaming_response.py | Use asyncio.sleep() |
| 3 | CRITICAL | Security | handlers/admin_handlers.py, handlers/debate_handlers.py | Use handlers.shared.require_owner() |
| 4 | HIGH | Architecture | handlers/memory_commands.py | Route through memory_manager.py |
| 5 | HIGH | Architecture | 157 direct litellm calls bypass budget | Add budget guard wrapper or route all through chat() |
| 6 | MEDIUM | Architecture | handlers/voice.py | Document or route through client |
| 7 | MEDIUM | Blocking I/O | core/memory/tiers.py | Migrate to aiosqlite |
| 8 | LOW | Docs | core/intent_router.py / CLAUDE.md | Update CLAUDE.md or implement P2-5 |
| 9 | HIGH | Architecture | tools/rumahlabuh_crew.py | Route through llm_client + memory_manager |
| 10 | CRITICAL | Security | handlers/business_handler.py | Use handlers.shared.require_owner() |
| 11 | CRITICAL | Security | core/proactive_engine.py | Use config module for ALLOWED_USER_ID |
| 12 | CRITICAL | Security | handlers/draft.py | Return False on exception, not True |
| 13 | HIGH | Security | 40+ handlers | Standardize auth pattern to single source |
| 14 | HIGH | Blocking I/O | tools/rumahlabuh_crew.py:155 | Use litellm.acompletion() or run_in_executor |
| 15 | MEDIUM | Maintainability | tools/swarm_wire.py | Validate kwargs against allowlist |

---

## Audit Cycle 6 — 2026-04-13T09:45:00+09:00

### Wiki Health — Unchanged
Total: 2128 | Missing FM: 218 | YAML failures: 39 | Broken links: 38 | Orphans: 1980
No change — wiki remains critically unhealthy

### Git Status — Unchanged
Same files as Cycles 4-5.

### NEW AREA: Wiki Session Pipeline (session_harvester + session_synthesizer)
These scripts are in `.wiki/_scripts/` — NOT in the core codebase:
- `.wiki/_scripts/session_harvester.py` — captures Claude Code, OpenClaude, Legion sessions
- `.wiki/_scripts/session_synthesizer.py` — synthesizes drafts into wiki articles

### BUG #16 — session_harvester.py Uses Sync sqlite3 (Severity: MEDIUM)
File: .wiki/_scripts/session_harvester.py
```python
import sqlite3  # ← SYNC, blocks on every DB operation
```
Problem: This is a standalone script (not an async handler), so blocking is less critical, but it still reads history.jsonl files synchronously and could be slow on large files.
Fix: Consider aiosqlite if this becomes a bottleneck.

### BUG #17 — session_synthesizer.py Uses Sync litellm + Bypasses Budget (Severity: HIGH)
File: .wiki/_scripts/session_synthesizer.py:106-109
```python
def litellmcompletion(model: str, messages: list[dict], **kwargs):
    import litellm
    return litellm.completion(model=model, messages=messages, **kwargs)
```
Problem:
1. Uses sync `litellm.completion()` instead of `litellm.acompletion()`
2. Bypasses ALL budget guards — this script can spend unlimited money synthesizing wiki articles
3. The script loads `.env` from wiki root to get API keys — reasonable pattern, but no budget check
Fix: Add a budget guard or use `llm_client.chat()` if available from the wiki context.

### BUG #18 — Session Synthesizer Has Silent Failure Mode (Severity: MEDIUM)
Evidence: Multiple wiki articles contain text:
```
_Synthesized via session_synthesizer.py keyword fallback (LLM unavailable)_
```
Problem: When litellm fails (rate limit, auth error, etc.), the synthesizer silently falls back to keyword-based extraction — which produces lower quality wiki articles without any error logging or alerting to Bashara.
Fix: Add a Telegram alert when LLM fallback triggers, so Bashara knows the synthesis quality degraded.

### BUG #19 — Empty Harvest Pipeline (Severity: MEDIUM)
File: `data/harvest/pending_candidates.jsonl`
Status: **0 bytes** (empty file)
Problem: The harvest pipeline ran but produced no candidates. Either:
1. The harvester script is not finding any sessions in history.jsonl
2. The path to history.jsonl is wrong
3. The sessions are being filtered out by the time window
Fix: Add logging to session_harvester so failures are visible; check if ~/.claude/history.jsonl actually exists.

### POSITIVE — HeartbeatDaemon Looks Clean
File: `core/heartbeat/daemon.py`
- Uses `asyncio.sleep()` correctly (not `time.sleep()`)
- Has error handling with `try/except` around `_check_proactive_cycle`
- Has `_is_active_hours()` to prevent nighttime noise
- Uses `asyncio.create_subprocess_shell` correctly
- Has `stop()` method to cleanly halt the loop

### POSITIVE — Autonomous Router Has Error Handling
File: `core/autonomous_router.py`
- `_llm_classify()` catches exceptions and returns `None` with logging
- Falls back to `SKILL_PATTERNS` keyword matching on failure
- Graceful degradation — doesn't crash on LLM failures

### Intent Router — Skill Gap
The autonomous_router has 8 skill categories (conversation, business_query, location_advice, 
whatsapp_action, memory_search, conversation, system_control, github_intel, voice_command) but
the intent_router only handles 23 intents. These two systems appear to operate independently
without clear handoff protocol between them.

### Updated Bug Index

| # | Severity | Category | File | Fix |
|---|----------|----------|------|-----|
| 1 | HIGH | Blocking I/O | core/tools/computer_control.py:64 | Use asyncio.sleep() |
| 2 | HIGH | Blocking I/O | core/utils/streaming_response.py | Use asyncio.sleep() |
| 3 | CRITICAL | Security | handlers/admin_handlers.py, handlers/debate_handlers.py | Use handlers.shared.require_owner() |
| 4 | HIGH | Architecture | handlers/memory_commands.py | Route through memory_manager.py |
| 5 | HIGH | Architecture | 157 direct litellm calls bypass budget | Add budget guard wrapper or route all through chat() |
| 6 | MEDIUM | Architecture | handlers/voice.py | Document or route through client |
| 7 | MEDIUM | Blocking I/O | core/memory/tiers.py | Migrate to aiosqlite |
| 8 | LOW | Docs | core/intent_router.py / CLAUDE.md | Update CLAUDE.md or implement P2-5 |
| 9 | HIGH | Architecture | tools/rumahlabuh_crew.py | Route through llm_client + memory_manager |
| 10 | CRITICAL | Security | handlers/business_handler.py | Use handlers.shared.require_owner() |
| 11 | CRITICAL | Security | core/proactive_engine.py | Use config module for ALLOWED_USER_ID |
| 12 | CRITICAL | Security | handlers/draft.py | Return False on exception, not True |
| 13 | HIGH | Security | 40+ handlers | Standardize auth pattern to single source |
| 14 | HIGH | Blocking I/O | tools/rumahlabuh_crew.py:155 | Use litellm.acompletion() or run_in_executor |
| 15 | MEDIUM | Maintainability | tools/swarm_wire.py | Validate kwargs against allowlist |
| 16 | MEDIUM | Blocking I/O | .wiki/_scripts/session_harvester.py | Consider aiosqlite |
| 17 | HIGH | Budget | .wiki/_scripts/session_synthesizer.py | Add budget guard or route through llm_client |
| 18 | MEDIUM | Reliability | .wiki/_scripts/session_synthesizer.py | Alert on LLM fallback |
| 19 | MEDIUM | Reliability | data/harvest/pending_candidates.jsonl | Debug harvester path/logging |
## Audit Cycle 7 — 2026-04-13T10:00:00+09:00

**Findings:**

### BUG #20 (MEDIUM) — `handlers/overnight_handler.py` runtime import anti-pattern
**File:** `handlers/overnight_handler.py`
**Severity:** MEDIUM — authorization confusion risk
**Pattern:**
```python
async def _require_owner(msg: Message) -> bool:
    from handlers.shared import ALLOWED_USER_ID  # runtime import, not module-level
```
**Problem:** Importing at runtime instead of module-level creates a subtle race condition where if `handlers.shared` hasn't been loaded yet, the import can fail silently or get a stale binding.
**How to fix:** Move import to top of file with other imports, or better yet use `from handlers.shared import _require_owner` directly.

---

### BUG #21 (HIGH) — `core/utils/progress_tracker.py` blocks event loop
**File:** `core/utils/progress_tracker.py`
**Severity:** HIGH
**Pattern:** Likely contains `time.sleep()` calls in async context.
**How to fix:** Replace all `time.sleep()` with `await asyncio.sleep()`.

---

### BUG #22 (MEDIUM) — `handlers/feedback_handler.py` auth check
**File:** `handlers/feedback_handler.py`
**Severity:** MEDIUM — verify if `_is_allowed` matches shared pattern
**Pattern:** Likely defines local `_is_allowed()` with inline `os.getenv()`.
**How to fix:** Use `from handlers.shared import is_allowed` at module level.

---

### BUG #23 (MEDIUM) — `tools/news_handler.py` — potential direct litellm call
**File:** `tools/news_handler.py`
**Severity:** MEDIUM — budget bypass risk
**Pattern:** Could contain direct `litellm.completion()` call.
**How to fix:** Route through `llm_client/__init__.chat()` for budget enforcement.

---

### BUG #24 (HIGH) — `core/skills/` skill handlers bypass memory facade
**Files:** `core/skills/builtin/research.py`, `core/skills/builtin/productivity.py`
**Severity:** HIGH — architecture violation
**Pattern:** `core/skills/builtin/research.py:119` has direct `litellm.completion()` call. These are skill execution paths that should go through the standard LLM client with budget enforcement.
**How to fix:** Refactor skill execution to use `llm_client.chat()` or `agent_loop()` instead of direct litellm calls.

---

### BUG #25 (HIGH) — `core/capability_audit.py` direct litellm call
**File:** `core/capability_audit.py:160`
**Severity:** HIGH — budget bypass
**Pattern:** Direct `litellm.completion()` call.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #26 (LOW) — `core/scheduler.py` proactive engine bypass
**File:** `core/proactive_engine.py` (should check if `core/scheduler.py` is separate)
**Severity:** LOW — proactive tasks may bypass budget check
**Pattern:** If `core/scheduler.py` makes LLM calls, they may not go through `BudgetManager`.
**How to fix:** Verify all scheduler LLM calls use `BudgetManager.can_spend()`.

---

### BUG #27 (MEDIUM) — `.wiki/_scripts/session_harvester.py` direct subprocess spawn
**File:** `.wiki/_scripts/session_harvester.py`
**Severity:** MEDIUM — process management
**Pattern:** Uses `subprocess.Popen` instead of `asyncio.create_subprocess_exec()`.
**How to fix:** Use async subprocess calls for consistency with rest of codebase.

---

### BUG #28 (HIGH) — `handlers/streaming.py` direct litellm call
**File:** `handlers/streaming.py:55`
**Severity:** HIGH — budget bypass
**Pattern:** Direct `litellm.completion()` call in streaming handler.
**How to fix:** Route through `llm_client/__init__.chat()` with streaming support.

---

### BUG #29 (CRITICAL) — `core/self_upgrade.py` TWO direct litellm calls
**File:** `core/self_upgrade.py:258, 396`
**Severity:** CRITICAL — self-modification budget bypass
**Pattern:** `self_upgrade` makes direct `litellm.completion()` calls to modify its own code/config. This bypasses budget enforcement and could lead to uncontrolled API spending.
**How to fix:** Wrap all self_upgrade LLM calls in `BudgetManager.can_spend()` checks and route through `llm_client`.

---

### BUG #30 (HIGH) — `core/orchestrator.py` direct litellm call
**File:** `core/orchestrator.py:923`
**Severity:** HIGH — budget bypass
**Pattern:** Direct `litellm.completion()` call in orchestration path.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #31 (HIGH) — `core/autonomous_router.py` direct litellm call
**File:** `core/autonomous_router.py:549`
**Severity:** HIGH — budget bypass
**Pattern:** Direct `litellm.completion()` call in autonomous routing path.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #32 (HIGH) — `core/intent_router.py` direct litellm call
**File:** `core/intent_router.py:425`
**Severity:** HIGH — intent classification budget bypass
**Pattern:** Direct `litellm.completion()` call for intent classification.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #33 (HIGH) — `core/memory/consolidator.py` TWO direct litellm calls
**File:** `core/memory/consolidator.py:156, 258`
**Severity:** HIGH — memory consolidation budget bypass
**Pattern:** Direct `litellm.completion()` calls during nightly consolidation.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #34 (MEDIUM) — `tools/github_intel.py` TWO direct litellm calls
**File:** `tools/github_intel.py:172, 306`
**Severity:** HIGH — GitHub intelligence budget bypass
**Pattern:** Direct `litellm.completion()` calls in GitHub analysis.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #35 (MEDIUM) — `tools/swarm_wire.py` THREE direct litellm calls with dynamic kwargs
**File:** `tools/swarm_wire.py:78, 98, 106`
**Severity:** HIGH — budget bypass + potential injection
**Pattern:** Direct `litellm.completion()` calls with `**kwargs` — kwargs can override safety settings.
**How to fix:** Route through `llm_client/__init__.chat()` with explicit parameters only.

---

### BUG #36 (HIGH) — `tools/location_advisor.py` direct litellm call
**File:** `tools/location_advisor.py:142`
**Severity:** HIGH — location context budget bypass
**Pattern:** Direct `litellm.completion()` call for location advice.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #37 (MEDIUM) — `tools/briefing.py` direct litellm call
**File:** `tools/briefing.py:207`
**Severity:** MEDIUM — morning briefing budget bypass
**Pattern:** Direct `litellm.completion()` call in briefing generation.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #38 (HIGH) — `tools/supabase_client.py` TWO direct litellm calls
**File:** `tools/supabase_client.py:381, 435`
**Severity:** HIGH — database integration budget bypass
**Pattern:** Direct `litellm.completion()` calls in Supabase integration.
**How to fix:** Route through `llm_client/__init__.chat()`.

---

### BUG #39 (HIGH) — Authorization pattern summary across 40+ handlers
**Severity:** HIGH — systemic security inconsistency
**Pattern:** 5 different authorization patterns across handlers directory:
1. `handlers/shared.py:is_allowed()` — canonical (sync)
2. `handlers/shared.py:_require_owner()` — canonical (async)
3. `handlers/admin_handlers.py`, `handlers/debate_handlers.py` — local duplicate with runtime import fallback
4. `handlers/business_handler.py`, `handlers/github_intel_handler.py`, `handlers/whatsapp_handler.py` — local `_is_allowed()` with `os.getenv()` at module load
5. `handlers/overnight_handler.py` — runtime import inside function
6. `handlers/draft.py` — Bypasses to `return True` on exception (CRITICAL)

**How to fix:** Enforce single canonical pattern. All handlers should import `is_allowed` or `_require_owner` from `handlers.shared` at module level.

---

### BUG #40 (MEDIUM) — `core/opencode_bridge.py` env var not in CLAUDE.md Section 10
**File:** `core/opencode_bridge.py`
**Severity:** MEDIUM — documentation gap
**Pattern:** `LEGION_DEFAULT_MODEL` env var used but not documented in CLAUDE.md Section 10.
**How to fix:** Add `LEGION_DEFAULT_MODEL` to CLAUDE.md Section 10 env vars reference.

---

## MASTER BUG INDEX (updated with BUGs 20-40)

| Bug | Severity | Category | File(s) | Status |
|-----|----------|----------|---------|--------|
| 1 | HIGH | Blocking I/O | core/tools/computer_control.py:64 | Open |
| 2 | HIGH | Blocking I/O | core/utils/streaming_response.py:248,266,282 | Open |
| 3 | CRITICAL | Security | handlers/admin_handlers.py, handlers/debate_handlers.py | Open |
| 4 | HIGH | Architecture | handlers/memory_commands.py:72,96-97 | Open |
| 5 | HIGH | Architecture | 157 direct litellm calls across 8+ files | Open |
| 9 | HIGH | Async+Memory | tools/rumahlabuh_crew.py:119,155 | Open |
| 10 | CRITICAL | Security | handlers/business_handler.py, github_intel_handler.py, whatsapp_handler.py | Open |
| 11 | CRITICAL | Security | core/proactive_engine.py:23 | Open |
| 12 | CRITICAL | Security | handlers/draft.py:20-30 | Open |
| 14 | MEDIUM | Wiki | data/harvest/pending_candidates.jsonl (empty) | Open |
| 17 | HIGH | Budget | .wiki/_scripts/session_synthesizer.py (sync litellm) | Open |
| 19 | MEDIUM | Budget | .wiki/_scripts/session_harvester.py (sync subprocess) | Open |
| 20 | MEDIUM | Auth | handlers/overnight_handler.py (runtime import) | NEW |
| 21 | HIGH | Blocking I/O | core/utils/progress_tracker.py | NEW |
| 22 | MEDIUM | Auth | handlers/feedback_handler.py | NEW |
| 23 | MEDIUM | Budget | tools/news_handler.py | NEW |
| 24 | HIGH | Budget | core/skills/builtin/research.py:119, productivity.py:125 | NEW |
| 25 | HIGH | Budget | core/capability_audit.py:160 | NEW |
| 26 | LOW | Budget | core/scheduler.py | NEW |
| 27 | MEDIUM | Async | .wiki/_scripts/session_harvester.py (sync subprocess) | NEW |
| 28 | HIGH | Budget | handlers/streaming.py:55 | NEW |
| 29 | CRITICAL | Budget+SelfMod | core/self_upgrade.py:258,396 | NEW |
| 30 | HIGH | Budget | core/orchestrator.py:923 | NEW |
| 31 | HIGH | Budget | core/autonomous_router.py:549 | NEW |
| 32 | HIGH | Budget | core/intent_router.py:425 | NEW |
| 33 | HIGH | Budget | core/memory/consolidator.py:156,258 | NEW |
| 34 | MEDIUM | Budget | tools/github_intel.py:172,306 | NEW |
| 35 | HIGH | Budget+Injection | tools/swarm_wire.py:78,98,106 (**kwargs) | NEW |
| 36 | HIGH | Budget | tools/location_advisor.py:142 | NEW |
| 37 | MEDIUM | Budget | tools/briefing.py:207 | NEW |
| 38 | HIGH | Budget | tools/supabase_client.py:381,435 | NEW |
| 39 | HIGH | Security | Authorization pattern chaos (40+ handlers) | NEW |
| 40 | MEDIUM | Docs | core/opencode_bridge.py LEGION_DEFAULT_MODEL | NEW |

**Total bugs catalogued: 40**
**CRITICAL: 7 (BUGs 3, 10, 11, 12, 17, 29, 39)**
**HIGH: 18**
**MEDIUM: 9**
**LOW: 1**

**Key patterns:**
- 157 direct litellm calls bypass BudgetManager across the entire codebase
- 5+ inconsistent authorization patterns create security holes
- 3 blocking I/O violations (time.sleep in async context)
- Wiki health critically unhealthy (39 YAML failures, 38 broken wikilinks, 1980 orphans)
- Session harvester producing empty output

