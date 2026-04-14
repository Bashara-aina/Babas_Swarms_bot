---
title: Adr 002 Async Error Handling
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Decider:** @planner'
wikilinks: []
confidence: medium
source: research
---
# ADR-002: Async Task Error Handling Policy

**Date:** 2026-04-12  
**Status:** PROPOSED  
**Decider:** @planner  
**Reviewer:** @reviewer

## Context
Found 116+ `asyncio.create_task()` calls throughout the codebase. Many have no exception handling — if the task raises, the exception is lost and the failure is silent.

## Decision
All `asyncio.create_task()` calls must follow one of these patterns:

### Pattern 1: Explicit await with try/except (preferred for critical tasks)
```python
task = asyncio.create_task(coro())
try:
    result = await task
except Exception as e:
    logger.error("Task failed: %s", e)
```

### Pattern 2: Done callback for fire-and-forget
```python
async def _safe_task(coro):
    try:
        await coro
    except Exception as e:
        logger.error("Silent task failed: %s", e)

asyncio.create_task(_safe_task(coro))
```

### Pattern 3: Shield for critical tasks
```python
asyncio.create_task(asyncio.shield(critical_coro()))
```

## Scope
- **Critical tasks** (memory writes, conversation persistence): Must use Pattern 1
- **Non-critical background tasks** (analytics, wikibot): Must use Pattern 2
- **User-facing tasks** (agent loops): Must use Pattern 1 with timeout

## Files Requiring Changes
1. `handlers/nihongo_handler.py:266` — VocabTracker.track_from_response
2. `llm_client/__init__.py:1231,1315,1322,1336,1344,1492` — multiple fire-and-forget
3. `main.py:361,474,506,523,532,541,577,619,628,641,658,714,726` — startup tasks

## Consequences
**Pros:**
- No silent failures
- Errors visible in logs
- Easier debugging

**Cons:**
- More verbose code
- Possible performance overhead from exception wrapping

## Enforcement
Add ruff rule to flag bare `asyncio.create_task()` without exception handling.
