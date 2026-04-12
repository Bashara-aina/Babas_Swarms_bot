---
title: stability-map
domain: security-stability
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 360
---

# Stability Map

## ONE-LINE SUMMARY
Crash scenarios, recovery behavior, and gaps — what happens when things break.

## FACTS
- Bot startup: main.py on_startup() wraps all initialization in try/except with logger.warning — bot continues even if individual subsystems fail
- All proactive subsystems: wrapped in try/except with logger.warning — failures are silent
- Fallback chain exists: core/reliability/fallback_chain.py provides 4 cloud providers + local Ollama emergency fallback
- Provider health checking: core/reliability/provider_health.py check_provider_health() — circuit breaker pattern
- LLM failure: if all providers fail, returns "all providers unavailable" error to user — no silent drop
- Telegram rate limit: not explicitly handled — send_chunked() has no rate limit retry logic
- Proactive loop crash: if check_cycle throws, loop continues — "while True" with try/except wraps each iteration
- Memory store crash: memory_manager.py facade catches all store exceptions — user gets error message, not crash
- Session restart: no persistent session state beyond SQLite-backed transcript store (U1 complete)
- Bot crash: systemd service restart via supervisor — LEGION_MASTER.md documents swarm-bot.service

## LEGION BEHAVIOR RULES
1. All background loops must have try/except around the inner loop body — never let loop die silently
2. All async subsystems must start via asyncio.create_task() with error_callback — don't await directly in startup
3. On LLM failure: always return user-facing error via humanize_error_for_display() — never return raw exception
4. On Telegram rate limit: implement exponential backoff in send_chunked() — 0.3s delay is insufficient
5. On disk full (detected by ProactiveInitiator): stop all write operations, alert user immediately
6. On memory store corruption: fall back to empty store, alert user, log for review
7. All startup subsystems should log at INFO level on success, WARNING on failure — use logger, not print
8. On unhandled exception in any handler: catch in shared error handler, humanize error, send to user, log with full traceback

## EXAMPLES
Crash scenario: OpenRouter API key invalid during a request
Recovery: FallbackChain.get_next_available_provider() skips OpenRouter, selects Groq — transparently recovers — ✅

Crash scenario: Supabase client fails during proactive health check
Recovery: ProactiveScheduler._check_business_health() catches Exception, returns [] — silent — no user alert

Crash scenario: asyncio loop saturates due to blocking subprocess.run in tool
Recovery: No recovery — event loop blocks until subprocess completes — request hangs
Fix: asyncio.to_thread(subprocess.run, ...) pattern needed

Crash scenario: Telegram sends update during bot restart
Recovery: aiogram dispatches error to user gracefully, no data loss on server side

## ANTI-PATTERNS
1. Silent failures: proactive checks catch exceptions and return [] — user never knows check failed — debugging impossible
2. No circuit breaker persistence: health state is in-memory only — after restart, all providers marked healthy again regardless of prior state
3. No persistent crash log: bot.log rotates but crashes from hours ago may be lost — need structured crash logging
4. No startup health probe: on_startup() success doesn't guarantee subsystems are healthy — need post-startup verification

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Silent failures in proactive checks are a confirmed issue — this page makes them visible.
