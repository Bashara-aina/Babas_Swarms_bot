---
title: Circuit Breaker Design
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- circuit-breaker-design.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Two independent circuit breaker systems (provider-level and agent-level)
  prevent retry storms and cascading failures across Legion's multi-provider LLM routing.
wikilinks: []
confidence: medium
source: research
---

# CIRCUIT BREAKER DESIGN

## ONE-LINE SUMMARY
Two independent circuit breaker systems (provider-level and agent-level) prevent retry storms and cascading failures across Legion's multi-provider LLM routing.

## Overview

Legion has two independent circuit breaker systems:
1. **Provider-level** (`provider_health.py`) — per-API-provider rate limit tracking
2. **Agent-level** (`error_recovery.py`) — per-agent/consecutive-failure tracking

Both work together: provider circuit open → agent circuit records failure → agent circuit may open.

## Provider-Level Circuit Breaker

**File**: `core/reliability/provider_health.py`

**Purpose**: Prevent cascading failures when a specific API provider hits rate limits.

### State Machine

```
HEALTHY → (rate limit hit) → BLOCKED (120s) → (timer expires) → DEGRADED (60s) → HEALTHY
```

### Configuration

| Constant | Value | Meaning |
|---|---|---|
| `_CIRCUIT_OPEN_DURATION` | 120s | Block provider for 2 min after rate limit |
| `_RATE_LIMIT_COOLDOWN` | 60s | Additional degraded period before recovery |

### Functions

```python
record_rate_limit(provider: str)
check_provider_health(provider: str)
get_healthy_provider(preferred, fallback)
reset_provider_health(provider: str)
get_all_provider_status()
```

### Integration with FallbackChain

`FallbackChain.get_next_available_provider()` calls `check_provider_health()` for each provider, skipping unavailable ones.

## Agent-Level Circuit Breaker

**File**: `core/reliability/error_recovery.py`

**Purpose**: Prevent retry storms against a failing agent/model combination.

### CircuitBreaker Class

```python
@dataclass
class CircuitBreaker:
    name: str
    failure_count: int = 0
    last_failure: float = 0.0
    state: CircuitState = CLOSED
```

### State Transitions

| Current | Event | Next | Action |
|---|---|---|---|
| CLOSED | 5 consecutive failures | OPEN | Log warning |
| OPEN | 60s elapsed | HALF_OPEN | Allow 1 test call |
| HALF_OPEN | Test succeeds | CLOSED | Reset counter |
| HALF_OPEN | Test fails | OPEN | Reset timer |

### Configuration

| Constant | Value | Meaning |
|---|---|---|
| `FAILURE_THRESHOLD` | 5 | Open after 5 consecutive failures |
| `RESET_TIMEOUT` | 60s | Wait before testing recovery |

## Fallback Chain Design

**File**: `core/reliability/fallback_chain.py`

### Provider Chains by Task Type

| Task | P1 | P2 | P3 | Emergency |
|---|---|---|---|---|
| coding | minimax-coding-plan/MiniMax-M2.7 | minimax-coding-plan/MiniMax-Text-01 | ollama_chat/llama3.3:70b | ollama_chat/gemma4:e4b |
| chat | minimax-coding-plan/MiniMax-Text-01 | minimax-coding-plan/MiniMax-M2.7 | ollama_chat/gemma4:e4b | ollama_chat/gemma4:e4b |
| analysis | minimax-coding-plan/MiniMax-M2.7 | minimax-coding-plan/MiniMax-Text-01 | ollama_chat/llama3.3:70b | ollama_chat/gemma4:e4b |

### Emergency Local Fallback

`ollama_chat/gemma4:e4b` is last resort when all 4 cloud providers are circuit-open. RTX 3060 (12GB VRAM) can run it. `qwen3.5:35b` is excluded — needs ~23GB, will OOM.

## Recovery Strategy Chain

`ErrorRecoveryManager.execute()` orchestrates 5-level recovery:

```
Level 1: Primary Model + Retry (3 retries with backoff 2s/4s/8s)
  ↓ (fail)
Level 2: Fallback Model (same agent, different provider)
  ↓ (fail)
Level 3: Alternative Agent (coding↔debug, math→coding, architect↔mentor)
  ↓ (fail, only if task > 200 chars)
Level 4: Simplified Prompt (200 chars + "[Simplified for recovery]")
  ↓ (all fail)
Level 5: Human Escalation (formatted partial error with guidance)
```

## Watchdog Auto-Recovery

**File**: `core/watchdog.py`

`Watchdog` wraps `main.py` as a subprocess for zero-downtime restarts:
- Launch main.py as subprocess
- Every 1s: check `data/.restart_requested` flag → graceful restart (SIGTERM → re-launch)
- Every 1s: check if main.py process died → wait 3s → re-launch (max 20 restarts/hour)
- On crash/restart → send Telegram message to admin

**Restart throttling**: Max 20 restarts/hour. Beyond that, manual intervention required.

## Key Files

| File | Purpose |
|---|---|
| `core/reliability/provider_health.py` | Provider-level rate limit circuit breaker |
| `core/reliability/error_recovery.py` | Agent-level circuit breaker + 5-level recovery |
| `core/reliability/fallback_chain.py` | Multi-provider fallback chain selection |
| `core/watchdog.py` | Process-level auto-recovery |

## See Also
- `.wiki/error-patterns-catalog.md` — All error types and their humanized messages
- `.wiki/debugging-guide.md` — Log analysis and crash investigation

## DEBATE RECORD
Advocate: 9 | Skeptic: 5 | Judge: WRITE 9
Judge note: Circuit breaker design is foundational to Legion's reliability architecture.