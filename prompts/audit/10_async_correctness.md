# AUDIT 10 — Async Correctness Sweep
> Paste this entire prompt into a new OpenCode session.
> Goal: no blocking I/O in async, no missing awaits, no fire-and-forget data loss.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 10 — Async Correctness Sweep                      ║
║  Fix: every async call awaited; no blocking I/O in async funcs  ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — FIND ASYNC FUNCTIONS CALLED WITHOUT AWAIT
Search all .py files for patterns where an async function is called without await.
Common mistake: result = some_async_func()  ← missing await
The result is a coroutine object, not actual data. This is a silent bug.

For each found:
  - Verify the calling function is also async
  - Add await: result = await some_async_func()
  - If calling function is NOT async: either make it async or use asyncio.run()

STEP 2 — FIND BLOCKING I/O INSIDE ASYNC FUNCTIONS
Scan for these patterns inside async def functions:
  open() / file.read() / file.write()
    → Replace with: aiofiles.open() (add aiofiles to requirements.txt)
  requests.get() / requests.post()
    → Replace with: async with httpx.AsyncClient() as c: await c.get()
  subprocess.run() / os.system()
    → Replace with: await asyncio.create_subprocess_exec()
  time.sleep()
    → Replace with: await asyncio.sleep()

Fix every instance. Blocking I/O inside async = entire bot freezes for ALL users.

STEP 3 — AUDIT asyncio.create_task() USAGE
Find all asyncio.create_task() calls.
For each: ask "does the caller need the RESULT of this task?"
  If YES (e.g., the task fetches data the handler needs): must use await instead
  If NO (e.g., fire-and-forget logging): create_task() is OK but add error handler:
    task = asyncio.create_task(some_func())
    task.add_done_callback(lambda t: logger.error(t.exception()) if t.exception() else None)

STEP 4 — AUDIT GENERATORS AND STREAMS
Find any async generator (async for ... in ...) usage.
Verify the generator is fully consumed (iterated to completion or explicitly closed).
Unclosed async generators = resource leak.

STEP 5 — AUDIT EVENT LOOP USAGE
Search for asyncio.get_event_loop() and loop.run_until_complete().
These should not be used inside async code.
If found: replace with direct await calls.

STEP 6 — VERIFY
Run: python -m py_compile handlers/ai.py core/autonomous_router.py core/memory_engine.py
Confirm no syntax errors after fixes.
Run the bot in dry-run/test mode if available and confirm no RuntimeWarning about coroutines.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
