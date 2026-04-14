---
title: Error Patterns Catalog
type: concept
status: deprecated
tags:
- /
- home
- newadmin
- swarm-bot
- error-patterns-catalog.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Catalogs every error pattern Legion encounters with humanized Indonesian
  messages and automated recovery actions.
wikilinks: []
confidence: medium
source: research
---

# ERROR PATTERNS CATALOG

## ONE-LINE SUMMARY
Catalogs every error pattern Legion encounters with humanized Indonesian messages and automated recovery actions.

## Error Categories

### 1. Authentication / API Key Errors
**Patterns**: `401`, `403`, `api key`, `auth`, `unauthorized`
**Providers**: Groq, Cerebras, Gemini, OpenRouter, Z.AI/GLM-4
**Cause**: Expired key, wrong key in `.env`, or provider auth outage.
**Humanized**: "GROQ lagi ada masalah sama auth..." / "Cerebras API lagi error auth..." / Generic fallback
**Source**: `core/error_humanizer.py:41-53`
**Recovery**: Circuit breaker retries; if auth persists, routes to next provider.

### 2. Rate Limiting
**Patterns**: `rate limit`, `429`, `too many requests`, `quota`
**Cause**: Exceeded provider's requests-per-minute or tokens-per-minute quota.
**Humanized**: "Rate limited — bentar dulu ya, coba lagi dalam 1-2 menit…"
**Source**: `core/error_humanizer.py:56-57`
**Recovery**: Circuit breaker opens for 120s; `FallbackChain` routes away.

### 3. Timeout Errors
**Patterns**: `timeout`, `timed out`, `deadline`, `took too long`
**Cause**: LLM response exceeded latency; network hiccup; model overloaded.
**Humanized**: "Koneksi timeout. Lagi retry dengan cara lain…"
**Source**: `core/error_humanizer.py:59-61`
**Recovery**: 3 retries with exponential backoff (2s→4s→8s, max 16s); fallback to alt model→agent→simplified prompt.

### 4. Model Not Available
**Patterns**: `model not found`, `model not available`, `404`
**Cause**: Model ID typo, deprecated model, or provider removed model.
**Humanized**: "Model yang dipake lagi unavailable. Lagi switch ke model lain…"
**Source**: `core/error_humanizer.py:63-65`
**Recovery**: `FallbackChain` selects next healthy provider.

### 5. Bad Request / Malformed
**Patterns**: `bad request`, `invalid request`, `400`, `malformed`
**Cause**: Request exceeds context window, wrong parameter format, API schema changed.
**Humanized**: "Request terlalu panjang — lagi coba singkatin context…" / "Request lagi malformed. Lagi retry…"
**Source**: `core/error_humanizer.py:67-71`

### 6. Network / Connectivity
**Patterns**: `connection`, `network`, `connectivity`, `dns`, `refused`, `unreachable`
**Humanized**: "Koneksi lagi hiccup. Lagi retry…"
**Source**: `core/error_humanizer.py:73-75`
**Recovery**: Retry with backoff; circuit breaker opens if persistent.

### 7. Permission / Access Denied
**Patterns**: `permission denied`, `access denied`, `403`
**Humanized**: Shell: "Permission denied — mau coba sudo atau bypass?" / Generic: "🔒 <b>Permission Denied</b> — I don't have access to that resource."
**Source**: `core/error_humanizer.py:78-80`, `core/utils/error_formatter.py:35-38`

### 8. Memory / Resource Exhaustion
**Patterns**: `memory`, `oom`, `out of memory`, `cuda oom`, `gpu memory`
**Humanized**: "GPU lagi kehabisan memory..." / "RAM hampir penuh. Lagi cleanup..."
**Source**: `core/error_humanizer.py:88-92`

### 9. File / Path Errors
**Patterns**: `no such file`, `not found`, `is a directory`, `permission denied` (file context)
**Humanized**: "File tidak ditemukan atau permission error. Check path-nya ya…"
**Source**: `core/error_humanizer.py:94-96`

### 10. Execution / Shell Errors
**Patterns**: `killed`, `signal`, `disk full`, `space`, `command not found`
**Humanized**: "Process kebunuh..." / "Disk hampir penuh..." / "Command tidak ketemu..."
**Source**: `core/error_humanizer.py:81-86`

### 11. Empty / Null Responses
**Patterns**: `""`, `"None"`, `"null"`, empty string after API call
**Humanized**: "Lagi dapat response kosong — retry dulu ya…"
**Source**: `core/error_humanizer.py:98-100`

## Error Recovery Hierarchy

`ErrorRecoveryManager.execute()` strategy chain:
```
1. Primary model + retry with backoff (up to 3 retries, 2→4→8s)
   ↓ (if circuit open or all retries fail)
2. Fallback model (same agent family, different provider)
   ↓ (if fails)
3. Alternative agent (coding↔debug, math→coding, architect↔mentor)
   ↓ (if fails AND task > 200 chars)
4. Simplified prompt (first 200 chars + "[Simplified for recovery]")
   ↓ (if all fail)
5. Human-readable partial error to user
```
**Source**: `core/reliability/error_recovery.py:195-288`

## Circuit Breaker States

Per-agent `CircuitBreaker` in `error_recovery.py`:

| State | Meaning | Behavior |
|-------|---------|----------|
| `CLOSED` | Normal | Calls allowed through |
| `OPEN` | Failing fast | Calls rejected after 5 consecutive failures |
| `HALF_OPEN` | Testing | One call allowed to test recovery |

**Transitions**: CLOSED→OPEN (5 failures) → OPEN→HALF_OPEN (60s) → HALF_OPEN→CLOSED (success) or →OPEN (failure)

## Provider Health States

Per-provider tracking in `provider_health.py`:

| Status | Meaning | Behavior |
|--------|---------|----------|
| `healthy` | Available | Full use |
| `degraded` | Rate-limited but cooldown expired | Usable with caution |
| `unavailable` | Circuit open (120s block) | Blocked, routed away |

**Cooldown timeline**: Rate limit hit → 120s blocked → 60s degraded → healthy

## Message Send Failure Recovery

`handlers/shared.py:send_chunked()` triple fallback:
```
1. Try: msg.answer(text, parse_mode="HTML", reply_markup=markup)
   ↓ (Exception)
2. Try: msg.answer(html_mod.escape(text), parse_mode="HTML", reply_markup=markup)
   ↓ (Exception)
3. Try: msg.answer(text, reply_markup=markup)  # Plain, no HTML
```

## Anti-Patterns

1. **Bare `except`**: Forbidden — always catch specific exceptions
2. **`time.sleep()`**: Forbidden — use `await asyncio.sleep()` for async code
3. **Exposing raw exceptions to Telegram**: All errors pass through `humanize_error()` first
4. **Silent failures**: `except Exception: pass` — all catches must log at minimum

## Key Files

| File | Role |
|------|------|
| `core/error_humanizer.py` | Exception → human Indonesian message |
| `core/reliability/error_recovery.py` | Circuit breaker + retry + fallback chain |
| `core/reliability/provider_health.py` | Per-provider rate limit tracking |
| `core/reliability/fallback_chain.py` | Multi-provider selection |
| `core/utils/error_formatter.py` | Telegram HTML error formatting + recovery buttons |

## See Also
- `.wiki/circuit-breaker-design.md` — Health tracking and fallback behavior details
- `.wiki/debugging-guide.md` — Log analysis and crash investigation

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Error catalog directly improves Legion's ability to recover from failures.