---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/worker_concerns567.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.512991"
}
---

# Worker Completion Report: Concerns 5, 6, 7

**Date**: 2026-04-12  
**Worker**: @worker  
**Status**: All 3 concerns completed and verified

---

## Concern 5: Daily Harvester Not Scheduled ✅ ALREADY WORKING

### Findings
- `main.py` line 633: `_start_daily_harvester()` is called in `_run_group_a_startup()`
- `DailyHarvesterScheduler.start()` creates `asyncio.create_task(self._run_loop())` 
- Scheduler correctly runs the 24h harvest loop, sleeping until 04:00 WIB before first run
- Both `HarvestPipeline` and `DailyHarvesterScheduler` import successfully

### Verification
```bash
python -c "from core.daily_harvester.scheduler import DailyHarvesterScheduler; print('OK')"
python -c "from core.daily_harvester.harvest_pipeline import HarvestPipeline; print('OK')"
```

**Conclusion**: The harvester IS correctly wired and scheduled. No changes needed.

---

## Concern 6: Growth Without Verification ✅ ALREADY ADDRESSED

### Findings
All required CI/pre-commit guards are already in place:

1. **`.pre-commit-config.yaml`** exists with:
   - `ruff` for Python linting (with auto-fix)
   - `ruff-format` for formatting
   - `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`
   - `check-added-large-files` (max 500KB)
   - `check-merge-conflict`, `debug-statements`, `detect-private-key`

2. **`.github/workflows/ci.yml`** has `verify-wiring` job that runs `python scripts/verify_wiring.py`

3. **`Makefile`** has:
   - `verify` target: runs `python scripts/verify_wiring.py`
   - `hooks` target: runs `pre-commit install`

### Verification
```bash
python scripts/verify_wiring.py  # All 7 tests PASS
make verify  # Works
make hooks   # Works
```

**Conclusion**: All CI/pre-commit guards are properly configured. No changes needed.

---

## Concern 7: Soul Integrity ✅ FIXED

### Findings
The `SwarmDebateOrchestrator` in `task_orchestrator.py` uses `self.llm_call` which is passed from `tools/swarm_wire.py::_llm_call()`. This function was calling `litellm.acompletion` directly WITHOUT injecting soul context.

**Root Cause**: `_llm_call()` built messages like:
```python
{"role": "system", "content": system},  # Only agent persona, no soul
{"role": "user",   "content": user},
```

### Fix Applied
**File**: `tools/swarm_wire.py`

Modified `_llm_call()` to inject `build_soul_context()` at the top of the system prompt:
```python
from core.soul_engine import build_soul_context

# Inject soul context into system prompt
soul_context = build_soul_context()
full_system = f"{soul_context}\n\n{system}" if soul_context else system
```

Now messages are built as:
```python
{"role": "system", "content": full_system},  # Soul + agent persona
{"role": "user",   "content": user},
```

### Other call_llm usages verified
- `llm_client/__init__.py::call_llm()` - Low-level function, takes pre-built messages (by design)
- `llm_client/__init__.py::chat()` - Injects soul via `build_soul_context()` (CORRECT)
- `legion/anti_slop/integration.py::_call_llm()` - Calls `chat()` so gets soul (CORRECT)
- `handlers/nihongo_handler.py::_call_llm()` - Local function, not the same as `llm_client.call_llm`
- `tools/mirofish/backend/...` - Different module, not related

### Verification
```bash
python -c "from core.soul_engine import get_system_prompt; print(len(get_system_prompt()))"
# Output: 5557 (soul content present)

python -c "from core.soul_engine import build_soul_context; print('Legion' in build_soul_context())"
# Output: True

# Swarm wire import works
python -c "from tools.swarm_wire import _llm_call; print('Import OK')"
# Output: Import OK
```

---

## Test Results
```
pytest tests/ -x --asyncio-mode=auto -q
================= 383 passed, 2 warnings in 121.49s =================
```

All tests pass after the fix.

---

## Summary

| Concern | Status | Action |
|---------|--------|--------|
| 5: Daily Harvester | ✅ Already Working | No changes needed |
| 6: CI/Pre-commit | ✅ Already Addressed | No changes needed |
| 7: Soul Integrity | ✅ Fixed | Injected soul into `tools/swarm_wire.py::_llm_call()` |
