---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/raw/docs/legion-production-hardening.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-07T01:00:00.818212"
}
---

---
title: Legion Production Hardening
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- docs
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Paste everything below the horizontal rule into OpenCode.'
wikilinks: []
confidence: medium
source: research
---
# LEGION PRODUCTION HARDENING — OPENCODE MASTER PROMPT
> Paste everything below the horizontal rule into OpenCode.
> This is a single-session, fully autonomous task. Do not stop until all phases complete.

---

```
╔══════════════════════════════════════════════════════════════════════════╗
║         LEGION BOT — PRODUCTION HARDENING v1.0                         ║
║         Mission: Make EVERY feature mature, reliable, production-grade  ║
║         Scope: Full repo audit + targeted hardening per subsystem       ║
╚══════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0 — READ EVERYTHING FIRST (do not write a single line of code yet)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read these files IN FULL before doing anything:
  main.py
  SOUL.md
  CLAUDE.md
  LEGION_MASTER.md
  DEEP_AUDIT_2026-04-10.md        ← already-known issues list
  AUDIT_REPORT.md                  ← previous audit findings
  IMPLEMENTATION_STATUS.md         ← what's implemented vs stub
  core/autonomous_router.py
  core/intent_router.py
  core/task_router.py
  core/soul_engine.py
  core/memory_engine.py
  core/skill_registry.py
  core/system_prompt_builder.py
  core/conversation_interface.py
  handlers/ai.py                   ← main NL handler
  handlers/nihongo_handler.py

Then list every directory:
  core/, handlers/, skills/, agents/, bridges/, tools/,
  llm_client/, legion/, wiki/, data/, tests/, scripts/

Build a mental map of:
  1. Data flow: message → handler → router → LLM → response
  2. Which features are FULLY wired vs skeleton/stub
  3. Where try/except swallows errors silently
  4. Where async is misused (fire-and-forget without await)
  5. Where there is NO test coverage

ONLY after completing Phase 0, proceed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — CRITICAL BUG FIXES (blockers — fix these first)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIX 1.1 — WEB SEARCH RESULT INJECTION (CONFIRMED BROKEN)
Bug: Web search fires, shows "🔍 Lagi cari..." but NEVER returns results to user.
LLM generates reply WITHOUT search results in context.

Root cause to find and fix:
  - Locate where duckduckgo_search is called (core/tools/, skills/, handlers/)
  - Verify it is properly awaited: `results = await search_web(query)`
  - Verify results are injected into LLM context BEFORE generating reply:
    Method A: Append as system message addendum
      messages.append({"role": "system", "content": f"Search results:\n{results}"})
    Method B: Inject as tool result message
      messages.append({"role": "tool", "content": results, "tool_call_id": call_id})
  - Add 8-second timeout with asyncio.wait_for()
  - Add explicit error message if search fails/empty:
    "Gw coba search tapi hasilnya kosong / rate limited: {error}"
  - Add fallback: if DuckDuckGo fails → retry with simplified query (strip 3 words)
  - Test: "cari Bashara Aina Shibaura" → must show actual snippets in reply

FIX 1.2 — SILENT EXCEPTION SWALLOWING AUDIT
Scan ALL files for bare `except: pass`, `except Exception: pass`, 
`except Exception as e: logger.debug(e)` patterns.

For each one found:
  - If it's a non-critical path (UI formatting): keep but add logger.warning()
  - If it's a core feature (search, memory, LLM call): REPLACE with proper 
    error propagation that reaches the user as a humanized message
  - NEVER silently swallow errors in: tool execution, memory writes, 
    LLM API calls, search, voice processing, wiki reads

FIX 1.3 — ASYNC CORRECTNESS SWEEP
Scan for:
  - `asyncio.create_task()` calls with no error handling on the task
  - `async def` functions called without `await` (common in handler dispatch)
  - Blocking I/O inside async functions (file reads, subprocess calls, requests.get)
    → Replace with aiofiles, asyncio.subprocess, httpx/aiohttp

Fix every instance. Blocking I/O in async = latency spike for ALL users.

FIX 1.4 — IMPORT ERROR RESILIENCE
Every skill, handler, and core module must have graceful import guards:

```python
try:
    from skills.nihongo.sensei_soul import SenseiSoul
    NIHONGO_AVAILABLE = True
except ImportError as e:
    NIHONGO_AVAILABLE = False
    logger.warning(f"Nihongo mode unavailable: {e}")
```

If an optional dependency (pykakasi, voicevox, faster-whisper) is missing,
the bot must still start and all other features must work normally.
Missing optional features should show ONE clear startup warning, not crash.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — RESILIENCE & RELIABILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 2.1 — LLM CALL HARDENING (core/system_prompt_builder.py + LLM client)

Every LLM API call must have:
  a) Retry with exponential backoff:
     - Max 3 retries
     - Backoff: 1s → 2s → 4s
     - Retry on: RateLimitError, APIConnectionError, Timeout
     - Do NOT retry on: AuthenticationError, InvalidRequestError
  
  b) Model fallback chain (already have litellm — use its fallback):
     Primary → claude-3-5-haiku → gpt-4o-mini → gemini-2.0-flash
     If all fail: return humanized error, NOT a crash
  
  c) Token budget guard:
     - Estimate token count before call (tiktoken or len(text)//4)
     - If prompt > 90% of model context limit: trim oldest conversation turns
     - Log warning when trimming occurs
  
  d) Timeout:
     - Hard timeout: 30 seconds per LLM call
     - If timeout: "Gw lagi lemot nih, coba lagi sebentar?"

TASK 2.2 — MEMORY ENGINE HARDENING (core/memory_engine.py)

Current risks to fix:
  - Race condition: multiple messages arriving simultaneously write to same 
    user's memory without lock
    Fix: asyncio.Lock() per user_id in a dict: `_user_locks: dict[int, Lock]`
  
  - ChromaDB / mem0 failure should NOT crash the bot
    Fix: wrap ALL memory read/write in try/except with graceful degradation
    If memory unavailable: bot continues WITHOUT memory, logs warning
  
  - Memory write should be non-blocking (fire-and-forget is OK for writes,
    NOT for reads that the LLM needs):
    Fix: `asyncio.create_task(_write_memory(user_id, content))` for writes
         `await _read_memory(user_id)` for reads (blocking, needed before LLM call)

TASK 2.3 — WIKI SYSTEM HARDENING (core/wiki_bridge.py, wiki_manager.py)

  - All wiki reads must have a 5-second timeout
  - If wiki read times out: proceed without wiki context, log warning
  - wiki_auto_ingest.py: add duplicate detection (hash-based) before ingesting
  - wiki_quality_gate.py: ensure it actually BLOCKS bad content, not just logs
  - wiki_scheduler.py: add jitter to scheduled tasks (±10% of interval) 
    to prevent thundering herd on startup

TASK 2.4 — TELEGRAM HANDLER HARDENING (main.py + handlers/)

  - All handler functions must catch telegram.error.TelegramError specifically
  - Network error: retry message send once after 2 seconds
  - Message too long (>4096 chars): auto-split into chunks, send sequentially
    Implement split_message(text: str, limit: int = 4000) -> list[str]
  - Rate limit from Telegram (429): respect retry_after header, queue the message
  - If user blocks the bot: catch Forbidden error, clean up user state silently

TASK 2.5 — CIRCUIT BREAKER PATTERN (new: core/circuit_breaker.py)

Create a simple circuit breaker for external services:
  - States: CLOSED (normal), OPEN (failing, reject fast), HALF_OPEN (testing)
  - Threshold: 5 consecutive failures → OPEN
  - Recovery: after 60 seconds → HALF_OPEN → try once → if success: CLOSED
  - Apply to: DuckDuckGo search, VoiceVox TTS, ChromaDB, external APIs

```python
class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, 
                 recovery_timeout: int = 60):
        ...
    
    async def call(self, func, *args, **kwargs):
        """Execute func with circuit breaker protection"""
        ...
    
    def get_status(self) -> dict:
        """Return current state for /status command"""
        ...
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — OBSERVABILITY & DEBUGGING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 3.1 — STRUCTURED LOGGING (core/log_config.py upgrade)

Replace all bare print() calls with structured logging.
Every log entry must include:
  - timestamp (ISO 8601, JST)
  - level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  - component (which module/class)
  - user_id (when applicable, truncated for privacy: str(user_id)[-4:])
  - message
  - duration_ms (for LLM calls, tool calls, memory ops)

Log format (JSON for production, human-readable for dev):
```python
# Production (LOG_FORMAT=json in .env):
{"ts": "2026-04-12T16:00:00+09:00", "level": "INFO", 
 "component": "intent_router", "user": "****1234", 
 "msg": "search_tool_called", "query": "...", "duration_ms": 1243}

# Development (LOG_FORMAT=text):
[2026-04-12 16:00:00 JST] INFO intent_router user=****1234 
  search_tool_called query="..." duration=1243ms
```

TASK 3.2 — REQUEST TRACING (new: core/trace_context.py)

Add request_id to every message processing pipeline:
  - Generate UUID at message receipt: `request_id = uuid4().hex[:8]`
  - Pass through entire pipeline: handler → router → LLM → response
  - Log request_id at every stage
  - If Legion gives wrong answer, user can send "/debug last" to get 
    the request_id and trace what happened

TASK 3.3 — PERFORMANCE METRICS (core/observability.py upgrade)

Track and expose via /stats command:
  - Average LLM response time (last 100 requests)
  - Tool call success rate per tool (search, wiki, memory, voice)
  - Error rate by error type (last 24 hours)
  - Memory usage (psutil, already in requirements)
  - Active users last 24h
  - Circuit breaker statuses

/stats output format:
```
📊 LEGION STATUS — [timestamp]
━━━━━━━━━━━━━━━━━━━━━━━━
⚡ Avg response: 1.2s (p95: 3.4s)
🔍 Search: 94% success (last 50)
🧠 Memory: ✅ healthy (ChromaDB OK)
📚 Wiki: ✅ healthy (last ingest: 2h ago)
🎌 Nihongo mode: ✅ active
🔴 Circuit breakers: all CLOSED
💾 RAM: 412MB / 2GB
👥 Active users 24h: 3
```

TASK 3.4 — DEAD CODE ELIMINATION

Find and remove:
  - Functions defined but never called (use grep + AST analysis)
  - Imported modules never used
  - Feature flags set to False and never changed
  - Duplicate implementations of same functionality
  - .md files that are pure drafts with no code references

Do NOT delete: SOUL.md, CLAUDE.md, LEGION_MASTER.md, LEGION_NIHONGO_MODE.md
Do NOT delete: any test files
Log what was removed in a new CLEANUP_LOG_v2.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 — FEATURE COMPLETION (stubs → real implementations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 4.1 — AUDIT ALL STUB FUNCTIONS

Find every:
  - `pass` in a function body that should do something
  - `return None` where a real value is expected
  - `# TODO` / `# FIXME` / `# stub` comments
  - Functions that `raise NotImplementedError`
  - Empty `__init__.py` files that should wire up submodules

For each stub: implement it properly OR mark it with a feature flag 
`FEATURE_X_ENABLED = False` so it fails gracefully rather than silently.

TASK 4.2 — WIKI AUTO-INGEST COMPLETION (core/wiki_auto_ingest.py)

Verify the full pipeline works end-to-end:
  1. Source ingestion (RSS feeds, arxiv, web pages) — actually fires?
  2. Content extraction — returns text, not empty?
  3. Quality gate — actually rejects low-quality content?
  4. Embedding + storage — lands in ChromaDB correctly?
  5. Retrieval — wiki content actually appears in LLM context?

Test: ingest one URL manually, ask Legion about it, verify it knows.
Fix any broken step.

TASK 4.3 — MULTI-USER ISOLATION (core/multi_user.py)

Verify that user A's:
  - Memory does not leak to user B
  - Nihongo session state is isolated from user B
  - Active mode (nihongo on/off) is per-user, not global

Test with two simulated users in the same test:
  user_1 activates nihongo mode
  user_2 sends a message
  → user_2 should get Legion response, NOT nihongo mode
  → user_1's next message should still be in nihongo mode

TASK 4.4 — SOUL ENGINE ROBUSTNESS (core/soul_engine.py)

The soul/character must persist under ALL failure conditions:
  - LLM API down → queued response still uses Legion's voice when recovered
  - Memory engine down → Legion doesn't become generic/soulless
  - Long context → when trimming messages, NEVER trim the system prompt
  - Verify: SOUL.md content is always first in system prompt, 
    NEVER overridden by downstream code

Add assertion at startup:
  `assert "Legion" in system_prompt[:500], "SOUL INJECTION FAILED"`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 — SECURITY HARDENING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 5.1 — SECRET SCANNING
Scan ALL Python files for hardcoded secrets:
  - API keys (look for patterns: sk-, AIza, Bearer, token=, api_key=)
  - Passwords
  - Private keys
  - Database connection strings with credentials

If found: replace with os.getenv() and add to .env.example with placeholder.
Log findings in security_audit.txt (DO NOT commit this file — add to .gitignore).

TASK 5.2 — INPUT VALIDATION (handlers/)
All user input must be sanitized before:
  - Passing to shell commands (use shlex.quote or subprocess list form)
  - Passing to SQL (use parameterized queries only)
  - Passing to file paths (use pathlib.Path and validate no directory traversal)
  - Including in LLM prompts (strip null bytes, limit length to 10,000 chars)

TASK 5.3 — RATE LIMITING (core/rate_limiter.py upgrade)
Per-user rate limits:
  - Max 30 messages per minute per user
  - Max 5 voice messages per minute per user  
  - Max 10 tool calls per minute per user
  - If exceeded: "Lo ngirim terlalu cepet, slow down dulu 🙏"
  - Whitelist: ADMIN_USER_IDS from .env bypass rate limits

TASK 5.4 — ADMIN COMMAND PROTECTION
Every admin command (/reload, /stats, /debug, /shutdown) must:
  - Check user_id against ADMIN_USER_IDS env var
  - If unauthorized: log attempt with user_id, return generic error
  - Never reveal that the command exists to unauthorized users

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 6 — TEST COVERAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 6.1 — CRITICAL PATH TESTS (tests/)

Write tests for every critical path that currently has NO test:

tests/test_search_injection.py
  - test_search_result_in_llm_context()
  - test_search_timeout_handled_gracefully()
  - test_search_empty_result_message()
  - test_search_rate_limit_fallback()

tests/test_soul_persistence.py
  - test_soul_present_in_every_prompt()
  - test_soul_survives_memory_failure()
  - test_soul_survives_long_context_trimming()
  - test_nihongo_mode_does_not_contaminate_soul()

tests/test_multi_user_isolation.py
  - test_nihongo_mode_isolated_per_user()
  - test_memory_isolated_per_user()
  - test_rate_limit_isolated_per_user()

tests/test_circuit_breaker.py
  - test_circuit_opens_after_5_failures()
  - test_circuit_recovers_after_timeout()
  - test_fast_fail_when_circuit_open()

tests/test_resilience.py
  - test_bot_starts_without_chromadb()
  - test_bot_starts_without_voicevox()
  - test_bot_starts_without_optional_deps()
  - test_llm_retry_on_rate_limit()
  - test_message_split_at_4096_chars()

TASK 6.2 — INTEGRATION SMOKE TEST (tests/test_smoke.py)

A single end-to-end test that:
  1. Boots the bot in test mode (no real Telegram connection)
  2. Sends 5 representative messages:
     - Simple chat: "halo legion"
     - Search intent: "cari info tentang AI"
     - Wiki query: something from the wiki
     - Nihongo command: "/nihongo"
     - Admin command from unauthorized user: "/stats"
  3. Verifies each produces a non-empty, non-error response
  4. Verifies soul is present in each response
  5. Verifies unauthorized admin command is rejected

Run all tests: `python -m pytest tests/ -v --tb=short`
Target: 0 failures, >70% coverage on core/ and handlers/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 7 — DEPLOYMENT READINESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 7.1 — STARTUP HEALTH CHECK (core/health.py upgrade)

On bot startup, run health check for EVERY subsystem:
  ✅ Telegram API connection
  ✅ Primary LLM API (litellm ping)
  ✅ ChromaDB / mem0 (optional — warn if missing, don't fail)
  ✅ Supabase (if configured)
  ✅ Wiki directory readable
  ✅ Data directory writable
  ✅ VoiceVox (optional — warn if missing)
  ✅ DuckDuckGo (test search for "test")

Output on startup:
```
🚀 LEGION BOOT — [timestamp]
✅ Telegram: connected
✅ LLM: claude-3-5-haiku (primary)
⚠️  ChromaDB: unavailable (memory degraded)
✅ Wiki: 47 documents loaded
✅ Data: writable
⚠️  VoiceVox: not running (voice mode disabled)
✅ Search: DuckDuckGo OK
Legion ready. Degraded mode: memory, voice.
```

TASK 7.2 — GRACEFUL SHUTDOWN

Handle SIGTERM and SIGINT:
  1. Stop accepting new messages (set a flag)
  2. Finish processing in-flight messages (wait up to 10 seconds)
  3. Flush memory writes
  4. Close DB connections
  5. Log: "Legion shutting down gracefully. Processed {n} messages."
  6. Exit cleanly

TASK 7.3 — DOCKER COMPOSE PRODUCTION SETTINGS (docker-compose.yml)

Verify/add:
  - restart: unless-stopped for legion service
  - memory limit: 2g (prevent OOM)
  - healthcheck using the /health endpoint
  - log rotation: json-file driver, max-size: 50m, max-file: 3
  - environment variables sourced from .env file (not hardcoded)
  - Named volume for data/ persistence (not anonymous volume)

TASK 7.4 — ENVIRONMENT VALIDATION (.env.example + startup check)

On startup, validate ALL required env vars are present:
  REQUIRED = ["BOT_TOKEN", "OPENROUTER_API_KEY" or "ANTHROPIC_API_KEY"]
  OPTIONAL_WITH_WARNINGS = ["SUPABASE_URL", "CHROMADB_HOST", "ADMIN_USER_IDS"]

If any REQUIRED var is missing: print clear error and exit(1).
If any OPTIONAL var is missing: print warning but continue.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 8 — FINAL VERIFICATION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After all phases complete, verify EVERY item below passes:

CRITICAL (must all be TRUE):
  [ ] python -m pytest tests/ → 0 failures
  [ ] Bot starts without crashing when ChromaDB is down
  [ ] Bot starts without crashing when VoiceVox is down  
  [ ] Search query returns actual result content in reply
  [ ] Soul/character present in every LLM response
  [ ] User A's nihongo mode does not affect User B
  [ ] Admin commands rejected for non-admin users
  [ ] No hardcoded API keys in any Python file
  [ ] LLM call retries on rate limit (verify with mock)
  [ ] Message >4096 chars is split, not truncated

QUALITY (should all be TRUE):
  [ ] No bare except:pass anywhere in core/ or handlers/
  [ ] No blocking I/O inside async functions
  [ ] All external API calls have timeouts
  [ ] /stats command returns real metrics
  [ ] Startup health check shows clear status for each subsystem
  [ ] Graceful shutdown completes within 15 seconds
  [ ] Log output is structured and includes component names

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE CONSTRAINTS — DO NOT VIOLATE UNDER ANY CIRCUMSTANCE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DO NOT modify:
  - SOUL.md (Legion's identity — sacred)
  - CLAUDE.md (OpenCode instructions)
  - LEGION_MASTER.md (master config)
  - The nihongo handler isolation layer
  - Any existing passing test (only add new tests, fix broken ones)

DO NOT introduce:
  - New external dependencies without adding to requirements.txt
  - Breaking changes to any existing command interface
  - Synchronous DB calls in async handlers
  - Global mutable state (use per-user state stores only)

WHEN DONE:
  Create PRODUCTION_HARDENING_REPORT.md listing:
  1. Every bug fixed (with file + line number)
  2. Every stub completed
  3. Every test added
  4. Every security issue resolved
  5. Remaining known issues (if any) with severity rating
```
