# Legion Concerns Fixed — 2026-04-12

## Summary

| # | Concern | Status | Key Fix Applied |
|---|---------|--------|-----------------|
| 1 | Dual llm_client | ✅ Verified | `llm_client.py` root is intentional shim, `llm_client/` is canonical |
| 2 | Dual agents | ✅ Verified | `agents.py` root is intentional shim, `agents/` is canonical |
| 3 | Swarm handler stub | ✅ Fixed | Created `core/swarm_args.py`, updated `handlers/ai.py` import |
| 4 | Search injection bug | ✅ Fixed | `cmd_search()` now synthesizes results via `llm_client.chat()` |
| 5 | Daily harvester unscheduled | ✅ Verified | Already wired in `main.py` line 633 |
| 6 | Growth without verification | ✅ Verified | CI, pre-commit, Makefile guards already present |
| 7 | Soul integrity | ✅ Fixed | `tools/swarm_wire.py` now injects `build_soul_context()` |

## Final Gate

```bash
python scripts/verify_wiring.py && python -m pytest tests/ -x --asyncio-mode=auto -q
```

**Result**:
- Wiring: 7/7 PASS ✅
- Tests: 383 passed, 1 warning ✅

## Legion status: 🟢 Wide AND Deep
