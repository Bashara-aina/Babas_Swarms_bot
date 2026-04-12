# ADR-047: Async Correctness Audit — AUDIT 10

**Date:** 2026-04-12
**Status:** PROPOSED
**Decider:** @planner
**Reviewer:** @reviewer

## Context
Previous ADR-002 established async task error handling policy for `asyncio.create_task()`. This audit extends that work to cover all async correctness categories.

## Decision

### Category 1: Missing `await` on async calls
**Pattern to find:**
```python
async def foo():
    result = some_async_func()  # BUG: missing await
```
**Fix:** Add `await`: `result = await some_async_func()`

### Category 2: Blocking I/O in async functions
| Blocking Call | Async Replacement |
|---------------|-------------------|
| `time.sleep()` | `await asyncio.sleep()` |
| `open()` | `aiofiles.open()` |
| `requests.get/post` | `aiohttp.ClientSession.get/post` |
| `subprocess.run()` | `asyncio.create_subprocess_exec()` |
| `os.listdir()` | `asyncio.get_running_loop().run_in_executor()` |

### Category 3: `asyncio.create_task()` result handling (per ADR-002)
- **Critical tasks:** Must `await` result with try/except
- **Fire-and-forget:** Must wrap in `_safe_task()` with error logging
- **Shielded:** Use `asyncio.shield()` for cancellation-resistant tasks

### Category 4: Async generators/streams
```python
# WRONG
async def gen():
    yield 1
    # never closed

# RIGHT
async def gen():
    try:
        yield 1
    finally:
        pass  # or use async with
```
Must verify all `async generator`/`AsyncIterator` usages have `.aclose()` or `async with`.

### Category 5: Event loop misuse
- **NEVER** `asyncio.get_event_loop()` inside async function → use `asyncio.get_running_loop()`
- **NEVER** `loop.run_until_complete()` inside async context
- `asyncio.new_event_loop()` must be paired with `loop.close()` in `finally`

## Scope
Files: `handlers/*.py`, `core/*.py`
Priority: `handlers/ai.py`, `core/autonomous_router.py`, `core/memory_engine.py`

## Consequences
- Fixes all silent async bugs
- Replaces blocking I/O with async alternatives
- Ensures no resource leaks from unclosed async generators
