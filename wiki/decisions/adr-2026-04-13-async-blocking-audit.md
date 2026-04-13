---
title: ADR — Async/Blocking I/O Audit — Loop 3
type: decision
status: active
tags: [legion, async, blocking-io, audit]
created: 2026-04-13
updated: 2026-04-13
summary: "Loop 3 audit found no blocking I/O bugs in active code paths. core/tools/computer_control.py has time.sleep() but it's in a sync function wrapped via run_in_executor() — correct architecture. The main bot uses computer_agent/ package, not core/tools/computer_control.py."
wikilinks:
  - [[architecture/legion-module-map]]
confidence: high
source: loop-3-audit
project: legion
---

## Decision

No blocking I/O bugs were found in active code paths.

## Details

### core/tools/computer_control.py — SYNC ONLY, run via executor

This module contains sync-only functions with blocking calls:
- `time.sleep()` in `_rate_limit_screenshot()` (line 64)
- `requests.post()` in `analyze_screen_sync()` (line 456)

**Architecture**: These sync functions are wrapped in `run_in_executor()` by their async callers:
- `analyze_screen()` async wrapper uses `loop.run_in_executor(None, _get_controller().analyze_screen_sync, ...)`
- This means blocking calls run in a thread pool, NOT in the event loop

**Conclusion**: Correct architecture, no event-loop blocking.

### core/tools/computer_control.py — NOT the active computer control path

The bot's `/screen` command uses `computer_agent.take_screenshot()` (from `computer_agent/display.py`), NOT `core/tools/computer_control.py`.

`core/tools/computer_control.py` is legacy code:
- Referenced only in `tests/test_computer_control.py`
- Has a migration script `scripts/fix_imports.py` suggesting it was moved to `core.tools.computer_control`
- No active handler imports from this module

### Blocking patterns NOT found in active async code

Searched for: `time.sleep`, `requests.get`, `requests.post`, `subprocess.` (without asyncio)

Active async handlers (`handlers/`, `core/`) use:
- `asyncio.create_task()` for fire-and-forget
- `asyncio.wait_for()` with timeout for subprocess
- `run_in_executor()` for sync computer control functions
- `asyncio.to_thread()` for duckduckgo search (in source_strategy.py)

## Conclusion

The codebase is clean for async violations in active paths. No fixes needed.

## Files Checked
- handlers/computer.py — async handlers, correctly use computer_agent package
- computer_agent/display.py — async take_screenshot()
- core/tools/computer_control.py — sync only, executor-wrapped
- llm_client/ — async LLM calls via litellm
- core/proactive/ — async background tasks

## Recommendation

Consider removing `core/tools/computer_control.py` as dead code in a future cleanup, since the active path is `computer_agent/`.
