---
title: Worker Pm Callbacks 2026 04 12
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Task:** Add error handlers to asyncio.create_task() calls in handlers/pm.py'
wikilinks: []
confidence: medium
source: research
---
# Worker Log: handlers/pm.py — done-callback error handlers

**Date:** 2026-04-12  
**Task:** Add error handlers to asyncio.create_task() calls in handlers/pm.py  
**Target lines:** 35, 123, 154, 175 (original)

## Changes Made

1. **Added logging import** (line 4):
   ```python
   import logging
   ```

2. **Added logger instance** (after router definition):
   ```python
   logger = logging.getLogger(__name__)
   ```

3. **Wrapped 4 asyncio.create_task() calls** with done-callback error handlers:
   - Line 36 (cmd_task_from)
   - Line 126 (cmd_post)
   - Line 159 (cmd_brand_check)
   - Line 181 (cmd_email)

   Pattern applied:
   ```python
   typing_task = asyncio.create_task(_keep_typing(msg))
   typing_task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
   ```

## Verification

- `python -m py_compile handlers/pm.py` — ✅ Passed
- `pytest tests/ -x --asyncio-mode=auto -q` — ✅ All 373 tests passed

## Notes

- These are fire-and-forget "keep typing" tasks used to maintain user engagement during LLM calls
- If the typing task raises an exception, it is now logged instead of silently swallowed
- Consistent with existing pattern in handlers/artifact.py line 41
