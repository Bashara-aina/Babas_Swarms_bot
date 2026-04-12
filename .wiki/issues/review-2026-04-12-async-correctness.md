# Review: Async Correctness Sweep

## 1. `handlers/voice.py` — Blocking `open()` in Async Context

### ✅ Issue Confirmed

#### Line 52 — Blocking file read inside async function
```python
async def _transcribe(ogg_path: str) -> str:
    # ...
    client = openai.AsyncOpenAI(api_key=openai_key)
    with open(ogg_path, "rb") as f:           # ← LINE 52: BLOCKING I/O
        result = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="id",
        )
```
**Problem:** `open()` is synchronous/blocking. Inside an `async` function, this blocks the event loop.

**Fix:** Use `aiofiles.open()` or wrap in `asyncio.to_thread()`:
```python
import aiofiles
async with aiofiles.open(ogg_path, "rb") as f:
    result = await client.audio.transcriptions.create(...)
```

#### Line 68 — Same blocking pattern in Groq fallback
```python
async with httpx.AsyncClient(timeout=30) as client:
    with open(ogg_path, "rb") as f:           # ← LINE 68: BLOCKING I/O
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            ...
        )
```

---

## 2. `asyncio.create_task` Without Error Handlers — Systemic Pattern

### ✅ Issue Confirmed

**Total `asyncio.create_task` calls found:** 68  
**With `add_done_callback` error handling:** 2 (only `artifact.py:41` and `overnight_handler.py:130`)  
**Without error handlers:** 66

### Files with Unprotected `asyncio.create_task` Calls:

| File | Line(s) | Notes |
|------|---------|-------|
| `main.py` | 555, 676, 708, 725, 746, 782, 824, 833, 846, 863, 919, 931 | 12 calls |
| `llm_client/__init__.py` | 1325, 1409, 1416, 1430, 1438, 1586 | 6 calls |
| `handlers/nihongo_handler.py` | 266 | 1 call |
| `bridges/discord_bridge.py` | 12 | 1 call |
| `handlers/ai.py` | 112, 294, 661 | 3 calls |
| `handlers/shared.py` | 299, 364 | 2 calls |
| `core/conversation_interface.py` | 140, 169, 184, 195 | 4 calls |
| `core/agent.py` | 76 | 1 call |
| `legion/anti_slop/monitor.py` | 138 | 1 call |
| `core/wiki_scheduler.py` | 66 | 1 call |
| `handlers/computer.py` | 512 | 1 call |
| `tools/overnight.py` | 267, 319, 380, 419 | 4 calls |
| `tools/proactive_monitors.py` | 80 | 1 call |
| `tools/n8n_bridge.py` | 59 | 1 call |
| `tools/open_memory.py` | 138 | 1 call |
| `task_orchestrator.py` | 190 | 1 call |
| `handlers/github_intel_handler.py` | 67 | 1 call |
| `handlers/pm.py` | 35, 123, 154, 175 | 4 calls |
| `handlers/research.py` | 34, 98, 222, 266, 293 | 5 calls |
| `handlers/brain.py` | 29 | 1 call |
| `handlers/dev.py` | 54, 92, 199 | 3 calls |
| `handlers/ecc_compat.py` | 403 | 1 call |
| `core/utils/loading_manager.py` | 90 | 1 call |
| `core/tmp_cleanup.py` | 8 | 1 call |
| `core/ruflo_manager.py` | 83 | 1 call |
| `core/proactive/scheduler.py` | 57 | 1 call |
| `core/health.py` | 7 | 1 call |
| `core/daily_harvester/scheduler.py` | 47 | 1 call |
| `tools/scheduler.py` | 161 | 1 call |
| `handlers/overnight_handler.py` | 119 | 1 call (has handler, line 130) |
| `handlers/artifact.py` | 40 | 1 call (has handler, line 41) |

### Correct Pattern (Reference Implementation)

**`handlers/artifact.py:40-41`** — Proper error handling:
```python
task = asyncio.create_task(_expire_artifact(artifact_id))
task.add_done_callback(lambda t: logger.error(t.exception()) if t.exception() else None)
```

**`handlers/overnight_handler.py:129-133`** — Proper error handling:
```python
_bg_task = asyncio.create_task(
    run_overnight_job(...),
    name=f"overnight-{job_id}"
)
_bg_task.add_done_callback(
    lambda t: logger.error("overnight job crashed: %s", t.exception())
    if not t.cancelled() and t.exception() else None
)
```

### Risk Assessment

- **Severity:** High — Unhandled exceptions in detached tasks are silently swallowed
- **Impact:** Background jobs can fail silently (wiki ingest, proactive monitors, overnight jobs, etc.)
- **Detection:** Failures only visible via missing logs; no alerting on most tasks

---

## Summary

### ✅ Passed
- Codebase uses `async/await` throughout for I/O operations
- `aiogram` handlers properly async

### ⚠️ Warnings
- 66 `asyncio.create_task` calls lack `add_done_callback` error handlers
- Risk of silent failures in background tasks

### ❌ Blockers

| Issue | File | Lines | Fix Required |
|-------|------|-------|--------------|
| Blocking `open()` | `handlers/voice.py` | 52, 68 | Replace with `aiofiles.open()` or wrap in `asyncio.to_thread()` |
| Missing error handlers | All files in table above | 66 calls | Add `add_done_callback` to all `asyncio.create_task()` calls |

---

*Review generated: 2026-04-12*
