---
date: "2026-04-12"
task: "Decompose async correctness audit into atomic subtasks"
status: "PLANNED"
---
# AUDIT 10 — Async Correctness Sweep

## Subtasks

### Subtask 1: Missing `await` on async function calls
**Search patterns:**
- `rg "async def" handlers/ core/` to find async functions
- `rg "\b\w+\(.*\)\s*$" handlers/ai.py core/autonomous_router.py core/memory_engine.py` (function calls at end of line without await)
- Look for patterns: `some_async_func(` followed by newline without `await`

**Fix:** Add `await` before any async function call that was found without it
**Files:** handlers/ai.py, core/autonomous_router.py, core/memory_engine.py, all handlers/, all core/

---

### Subtask 2: Blocking I/O inside async functions
**Search patterns:**
- `time\.sleep` → replace with `await asyncio.sleep()`
- `\bopen\(` inside async functions → replace with `aiofiles.open()`
- `requests\.get|requests\.post|requests\.put|requests\.request` → replace with `aiohttp`
- `subprocess\.run|subprocess\.Popen` → replace with `asyncio.create_subprocess_exec/shell`
- `\.read\(\)|\.write\(` on file objects inside async → aiofiles

**Fix:** Replace blocking calls with async alternatives
**Files:** All .py files in handlers/ and core/

---

### Subtask 3: `asyncio.create_task()` without result handling
**Search patterns:**
- `rg "asyncio\.create_task"` — find all create_task calls
- Check if result is stored/awaited
- Look for fire-and-forget patterns with no exception handling (ADR-002)

**Fix:** 
- If result needed: add `result = await task` with try/except
- If fire-and-forget: wrap with `_safe_task()` pattern from ADR-002
- If shielded: verify `asyncio.shield()` used for critical tasks
**Files:** All .py files (found in 116+ locations per ADR-002)

---

### Subtask 4: Async generators and streams not closed
**Search patterns:**
- `rg "async def.*yield" handlers/ core/` — find async generators
- `rg "\.aclose\(\)" handlers/ core/` — verify async generators are closed
- `rg "async for.*in.*\(" handlers/ core/` — check async iteration
- Look for `AsyncIterator`, `AsyncGenerator`, `Stream` types

**Fix:** Add `async with` context manager or explicit `.aclose()` for async generators/streams
**Files:** handlers/streaming.py, core/memory_engine.py, core/agent.py, core/swarm.py

---

### Subtask 5: Event loop misuse
**Search patterns:**
- `rg "asyncio\.get_event_loop\(\)" handlers/ core/` — avoid inside async functions
- `rg "loop\.run_until_complete" handlers/ core/` — never call in async context
- `rg "loop\.run_in_executor" handlers/ core/` — check if truly needed
- `rg "asyncio\.new_event_loop\(\)" handlers/ core/` — verify proper cleanup

**Fix:**
- Inside async functions: use `asyncio.get_running_loop()` instead
- Remove any `run_until_complete` inside async code
- Ensure `new_event_loop()` pairs with `loop.close()` in finally block
**Files:** handlers/ai.py, handlers/voice.py, handlers/computer.py, core/memory_engine.py, core/swarm.py, core/agent.py

---

### Subtask 6: Verify fixes compile
**Command:** `python -m py_compile <fixed_file.py>` on each modified file
**Command:** `python -c "import <module>"` for each modified module
**Command:** `pytest tests/ -x --asyncio-mode=auto -q` to run test suite
**Files:** All files that were modified

---

## Review
**Assigned to:** @reviewer
**Scope:** All fixes from subtasks 1-5

## Notes
- DO NOT modify: SOUL.md, CLAUDE.md, LEGION_MASTER.md
- Per ADR-002, all create_task calls must follow Pattern 1, 2, or 3
- Async I/O alternatives: aiofiles, aiohttp, asyncio.subprocess
