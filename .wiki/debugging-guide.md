---
title: Debugging Guide
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- debugging-guide.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Covers log analysis, crash investigation, and Telegram-level debugging for
  Legion diagnostics.
wikilinks: []
confidence: medium
source: research
---

# DEBUGGING GUIDE

## ONE-LINE SUMMARY
Covers log analysis, crash investigation, and Telegram-level debugging for Legion diagnostics.

## Log Files

| File | What It Contains |
|---|---|
| `bot.log` | All structured logs — main bot activity |
| stdout (journalctl) | Watchdog + startup logs |
| `data/.restart_requested` | Flag file for watchdog-triggered restarts |

### Log Format

```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

### Inbound/Outbound Markers

| Prefix | Meaning |
|---|---|
| `[IN]` | Telegram message received |
| `[OUT]` | Telegram message sent |
| `[BOT_RESPONSE]` | LLM response chunk sent |
| `[BOT_THOUGHT]` | Internal reasoning |

## Common Crash Investigation

### 1. Bot Not Responding

**Symptoms**: Telegram shows "Legion is typing..." but no response.

**Diagnosis**:
```bash
ps aux | grep "python.*main.py" | grep -v grep
journalctl -u legion-watchdog --no-pager -n 50
tail -100 bot.log | grep -i "restart\|crash\|error\|traceback"
```

**Common causes**: Ollama not running, API key missing, context window overflow.

### 2. All Providers Rate Limited Simultaneously

**Symptoms**: "Rate limited" for all requests even after waiting.

**Diagnosis**:
```python
from core.reliability.provider_health import get_all_provider_status
print(get_all_provider_status())
# Output: {'openrouter': 'unavailable', 'groq': 'unavailable', ...}
```

**Fix**: Wait 2+ minutes for circuit breakers to reset.

### 3. Specific Agent Failing Consistently

**Symptoms**: `/do` works but `/think` always fails.

**Diagnosis**:
```python
from core.reliability.error_recovery import get_recovery
rm = get_recovery()
print(rm.circuit_status())       # Circuit breaker states
print(rm.failure_summary(20))    # Recent failure breakdown
```

**Common cause**: That agent's model hitting consistent errors → circuit open.

### 4. Crash During Startup

**Symptoms**: Bot exits immediately on launch.

**Diagnosis**:
```bash
cd /home/newadmin/swarm-bot
python main.py 2>&1 | head -100
grep "Missing required" bot.log
```

**Common causes**: `TELEGRAM_BOT_TOKEN` not set, `ALLOWED_USER_ID` not set, port conflict.

### 5. Memory Leak / OOM

**Symptoms**: Bot slows over hours/days, eventually crashes.

**Diagnosis**:
```bash
ps aux | grep "python.*main.py" | grep -v grep
nvidia-smi
```

**Fix**: Restart via watchdog. Delete `data/.restart_requested` to trigger graceful restart.

## Telegram Debug Tips

### Enabling Verbose Logging

```bash
LOG_LEVEL=DEBUG python main.py
```

### Inspecting a Specific Chat

```bash
grep "chat=123456" bot.log | tail -50
grep "\[BOT_RESPONSE\].*chat=123456" bot.log | tail -10
```

## Error Message Analysis

### Reading Humanized Errors

When Bashara sees: "Koneksi timeout. Lagi retry dengan cara lain…" — LLM call timed out, retry with backoff was attempted.

### Reading Circuit Breaker Logs

| Log Message | Meaning |
|---|---|
| `Circuit OPENED for groq after 5 failures` | Circuit opened, no requests to Groq for 60s |
| `Circuit HALF_OPEN for groq — testing` | Testing if Groq recovered |
| `Provider 'groq' circuit open (unavailable for 87s more)` | Provider blocked, time until reset |

## Recovery Chain Debugging

### Simulate Full Recovery Chain

```python
from core.reliability.error_recovery import get_recovery

async def test_recovery():
    rm = get_recovery()
    result = await rm.execute(
        task="Your failing task here",
        agent_key="coding",
        run_fn=lambda model, task, key: some_llm_call(model, task),
    )
    print(result)

import asyncio
asyncio.run(test_recovery())
```

### Check Fallback Chain Selection

```python
from core.reliability.fallback_chain import FallbackChain
stats = FallbackChain.get_fallback_stats("coding")
print(stats)
```

## Health Check Command

```bash
cd /home/newadmin/swarm-bot
python -c "from core.health_check import run_health_check, print_health_report; hp = run_health_check(); print_health_report(hp)"
```

## Panic Button

If everything is failing:
```bash
# 1. Stop the bot gracefully
pkill -SIGTERM -f "python.*main.py"

# 2. Clear all circuit breakers
cd /home/newadmin/swarm-bot
python -c "from core.reliability.provider_health import _provider_health; _provider_health.clear(); print('Cleared')"

# 3. Restart
python core/watchdog.py
```

## Watchdog Log Interpretation

| Watchdog Log | Meaning |
|---|---|
| `👁️  Watchdog started` | Watchdog process launched |
| `Launched main.py (pid=N) restart #N` | Bot process started |
| `🔄 Restart flag detected — upgrading` | Graceful restart triggered |
| `⚠️  main.py exited (code=N). Restarting in 3s` | Crash detected, auto-restarting |
| `🚨 Restart storm detected. Manual intervention needed.` | >20 restarts/hour, watchdog paused |

## Key Files for Debugging

| File | Purpose |
|---|---|
| `core/health_check.py` | Built-in system health check |
| `core/reliability/error_recovery.py` | `circuit_status()`, `failure_summary()` |
| `core/reliability/provider_health.py` | `get_all_provider_status()` |
| `core/reliability/fallback_chain.py` | `get_fallback_stats()` |
| `core/watchdog.py` | Process-level auto-recovery |

## See Also
- `.wiki/error-patterns-catalog.md` — All error types and humanized messages
- `.wiki/circuit-breaker-design.md` — Health tracking and fallback behavior

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Debugging guide directly improves operational maintenance capabilities.