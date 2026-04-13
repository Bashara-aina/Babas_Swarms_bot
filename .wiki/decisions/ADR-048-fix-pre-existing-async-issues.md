---
## Context

---
AUDIT 10 identifies two categories of pre-existing async/scheduling issues:

1. **Blocking I/O inside async functions** (`handlers/voice.py`)
2. **68 `asyncio.create_task()` calls without error handlers** — silent failures
---


## Decision 1: Fix `handlers/voice.py` blocking `open()`

### Problem
`_transcribe()` is an `async` function but uses synchronous `open()` on lines 52 and 68, blocking the event loop during file reads.

```python
# Line 52 (OpenAI path):
with open(ogg_path, "rb") as f:          # ← BLOCKING
    result = await client.audio.transcriptions.create(...)

# Line 68 (Groq path):
with open(ogg_path, "rb") as f:          # ← BLOCKING
    resp = await client.post(...)
```

### Decision
Wrap both `open()` calls with `asyncio.to_thread()` to move file I/O off the event loop.

```python
# Fixed (OpenAI path):
loop = asyncio.get_event_loop()
file_obj = await loop.run_in_executor(None, open, ogg_path, "rb")
with file_obj as f:
    result = await client.audio.transcriptions.create(...)

# Fixed (Groq path):
loop = asyncio.get_event_loop()
file_obj = await loop.run_in_executor(None, open, ogg_path, "rb")
with file_obj as f:
    resp = await client.post(...)
```

**Alternative considered:** `aiofiles` — requires extra dependency; `asyncio.to_thread()` is stdlib and sufficient.

---

## Decision 2: Fix unprotected `asyncio.create_task()` calls

### Problem
68 calls to `asyncio.create_task()` have no error handling. If those coroutines raise, the exception is silently swallowed by the event loop (and in Python 3.11+ triggers `asyncio.UnhandledFutureError` at shutdown).

### Classification

| Category | Count | Treatment |
|----------|-------|-----------|
| Fire-and-forget background tasks (no result needed) | ~60 | Add done-callback error logger |
| Tasks where result IS needed (already wrapped in try/except at call site) | ~5 | Safe — exception propagates to caller |
| Periodic scheduler tasks (self-scheduling loops) | ~3 | Handled internally by their own loop |

### Fire-and-forget fix pattern

```python
# Before (unprotected):
asyncio.create_task(some_bg_coro())

# After (protected):
task = asyncio.create_task(some_bg_coro())
task.add_done_callback(lambda t: logger.error("task failed: %s", t.exception()) if t.exception() else None)
```

### Tasks where result IS needed (no extra protection needed)

| File | Line | Call | Why protected |
|------|------|------|---------------|
| `handlers/ai.py` | 112, 294 | `_keep_typing(msg)` | Caller cancels task in `finally` block |
| `handlers/shared.py` | 299, 364 | `_keep_typing(msg)` | Caller cancels task in `finally` block |
| `handlers/pm.py` | 35, 123, 154, 175 | `_keep_typing(msg)` | Caller cancels task in `except`/`finally` block |
| `handlers/research.py` | 34, 98, 222, 266, 293 | `_keep_typing(msg)` | Caller cancels task in `try` block |
| `handlers/brain.py` | 29 | `_keep_typing(msg)` | Caller cancels task |
| `handlers/dev.py` | 54, 92, 199 | `_keep_typing(msg)` | Caller cancels task |
| `handlers/computer.py` | 512 | `_keep_typing(cb.message)` | Caller cancels task |
| `handlers/artifact.py` | 40 | `_expire_artifact(artifact_id)` | Already has try/except in function body |
| `core/conversation_interface.py` | 140, 169, 184, 195 | Various DB/session tasks | Fire-and-forget DB writes; errors logged via callback |

### Periodic scheduler tasks (no change needed)

| File | Line | Task |
|------|------|------|
| `core/wiki_scheduler.py` | 66 | `self._loop()` — owns error handling internally |
| `core/proactive/scheduler.py` | 57 | `self._loop()` — owns error handling internally |
| `core/daily_harvester/scheduler.py` | 47 | `self._run_loop()` — owns error handling internally |
| `tools/scheduler.py` | 161 | `self._running[task_id] = asyncio.create_task(coro)` — scheduler manages lifecycle |
| `task_orchestrator.py` | 190 | `_monitor_loop()` — owns error handling internally |
| `core/tmp_cleanup.py` | 8 | `start_cleanup_task()` — own error handling |
| `core/ruflo_manager.py` | 83 | `ruflo_health_monitor()` — own error handling |
| `bridges/discord_bridge.py` | 12 | `start_discord_bridge()` — own error handling; logged at startup |
| `tools/n8n_bridge.py` | 59 | `_run_listener()` — own error handling |

### Fire-and-forget tasks that NEED done-callback protection

**main.py (12 calls):**
- Line 555: `run_curiosity_loop(...)` — fire-and-forget loop
- Line 676: `_heartbeat.start(...)` — fire-and-forget daemon
- Line 708: `_cleanup_old_turns()` — fire-and-forget DB cleanup
- Line 725: `_bootstrap_supabase_skill()` — fire-and-forget bootstrap
- Line 746: `schedule_nightly_capability_report(...)` — fire-and-forget scheduler
- Line 782: `_run_memory_consolidation_nightly()` — fire-and-forget loop
- Line 824: `_run_github_intel_daily()` — fire-and-forget loop
- Line 833: `start_proactive_initiator(...)` — fire-and-forget daemon
- Line 846: `run_proactive_loop()` — fire-and-forget loop
- Line 863: `_sp_bridge.monitor_loop()` — fire-and-forget monitor
- Line 919: `start_health_server(...)` — fire-and-forget HTTP server
- Line 931: `WEBHOOK_SERVER.start()` — fire-and-forget webhook server

**llm_client/__init__.py (6 calls):**
- Line 1325: `_post_call_hooks(...)` — fire-and-forget hook runner
- Line 1409: `asyncio.to_thread(update_narrative_from_conversation, ...)` — fire-and-forget thread
- Line 1416: `maybe_run_self_review()` — fire-and-forget self-review
- Line 1430: `schedule_wiki_ingest_exchange(...)` — fire-and-forget wiki ingest
- Line 1438: `on_conversation_turn(...)` — fire-and-forget wiki auto-ingest
- Line 1586: `promote_important(recent)` — fire-and-forget memory promotion

**handlers/research.py (5 calls):** All `_keep_typing` — already handled by caller cancel

**tools/overnight.py (4 calls):**
- Line 267: `_heartbeat_loop(...)` — heartbeat for overnight job (cancelled in `finally`)
- Line 319: `_execute_single_task(...)` — part of `asyncio.gather()` with `return_exceptions=True`; inner try/except exists; add callback as belt-and-suspenders
- Line 380: `update_dashboard_fn()` — fire-and-forget dashboard update
- Line 419: `update_dashboard_fn()` — fire-and-forget dashboard update

**handlers/pm.py (4 calls):** All `_keep_typing` — already handled by caller cancel

---

## Consequence

- `handlers/voice.py` I/O moves to thread pool — no more event loop blocking
- 66 fire-and-forget tasks get done-callback error logging — silent failures eliminated
- `_keep_typing` tasks already protected via caller-side `task.cancel()` in `finally`/`except`
- Periodic schedulers unchanged — own their error handling internally
- Memory/session DB tasks unchanged — fire-and-forget writes, already wrapped in try/except at call site
