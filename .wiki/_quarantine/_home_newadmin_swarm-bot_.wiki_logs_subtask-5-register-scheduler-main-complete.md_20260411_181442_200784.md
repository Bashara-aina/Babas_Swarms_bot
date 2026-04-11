---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/subtask-5-register-scheduler-main-complete.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.200812"
}
---

# Subtask 5: Register WikiQualityScheduler in main.py Startup

**Date:** 2026-04-11  
**Status:** ✅ Complete

## Changes Made

### 1. Added import (line ~61)
```python
from core.wiki_scheduler import WikiQualityScheduler
```

### 2. Added global handle (after imports)
```python
_wiki_scheduler: WikiQualityScheduler | None = None
```

### 3. Added startup function + gather call
Inserted `_start_wiki_quality_scheduler()` into `asyncio.gather` inside `_run_group_a_startup()`:

```python
async def _start_wiki_quality_scheduler() -> None:
    global _wiki_scheduler
    try:
        async def _wiki_notify(text: str) -> None:
            await bot.send_message(ALLOWED_USER_ID, text[:4000])

        _wiki_scheduler = WikiQualityScheduler(_wiki_notify, ALLOWED_USER_ID)
        _wiki_scheduler.start()
        logger.info("WikiQualityScheduler started")
    except Exception as e:
        logger.warning("WikiQualityScheduler init failed (non-fatal): %s", e)
```

## Verification
```
python -c "import main; print('main.py loads ok')"
→ main.py loads ok
```

## Notes
- Non-fatal: wrapped in try/except — startup continues if scheduler init fails
- Follows same pattern as `_start_proactive_scheduler()` and other Group A startup tasks
- Notification callback uses same `[:4000]` truncation pattern as other notify functions in the file
