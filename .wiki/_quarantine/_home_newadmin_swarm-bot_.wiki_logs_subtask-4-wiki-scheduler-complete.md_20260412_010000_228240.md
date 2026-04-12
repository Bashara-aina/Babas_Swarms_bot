---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/subtask-4-wiki-scheduler-complete.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.228298"
}
---

# Subtask 4: Wiki Scheduler — COMPLETE

**Date:** 2026-04-11  
**Worker:** @worker  
**Status:** ✅ Done

## Created File

`/home/newadmin/swarm-bot/core/wiki_scheduler.py`

## Implementation Summary

### WikiQualityScheduler Class

A background asyncio scheduler for wiki quality enforcement with two scheduled tasks:

| Task | Schedule | Description |
|------|----------|-------------|
| Daily fast scan | 1 AM JST | Heuristic scan via `fast_gate`, quarantine pages <0.3 score |
| Weekly deep scan | Sunday 2 AM JST | Full LLM evaluation via `deep_gate`, writes `_quality_report.md` |

### Key Constants

- `DAILY_HOUR = 1` (1 AM JST = UTC-9: 1 AM = 10:00 UTC)
- `WEEKLY_DAY = 6` (Sunday in Python weekday())
- `DEEP_SCAN_HOUR = 2` (2 AM JST for weekly deep scan)
- `LOW_QUALITY_THRESHOLD = 0.3` (quarantine below this score)
- `LLM_CALL_DELAY = 1.0` (rate limit: 1s between deep_gate calls)

### Class API

```python
class WikiQualityScheduler:
    def __init__(self, notify_cb: Callable[[str], Coroutine] | None = None, telegram_chat_id: int | None = None)
    def start() -> None   # Start background asyncio task
    def stop() -> None    # Stop background task
```

### Internal Methods

- `_loop()` — Main scheduler loop, calculates next run time, sleeps until scheduled
- `_run_scheduled_tasks(now)` — Dispatches daily/weekly scans based on current time
- `_daily_scan()` — Fast heuristic scan, quarantines low-quality content
- `_weekly_deep_scan()` — Full LLM evaluation with rate limiting, writes quality report
- `_walk_wiki_pages()` — Walks `.wiki/**/*.md`, skips `_quarantine`, `_archive`, `index.md`
- `_build_quality_report(results)` — Generates markdown table report sorted by score bands
- `_write_quality_report(report)` — Writes report to `.wiki/_quality_report.md`

### Verification

```bash
$ python -c "from core.wiki_scheduler import WikiQualityScheduler; print('import ok')"
import ok
```

### JST Timezone Handling

Uses `pytz.timezone("Asia/Tokyo")` consistent with existing codebase patterns (see `core/proactive/scheduler.py`, `core/soul_engine.py`).

## Notes

- Uses `asyncio.sleep()` for all delays (never `time.sleep()`)
- Uses `asyncio.to_thread()` for file I/O operations
- Rate limits LLM calls with 1.0s delay between `deep_gate` invocations
- Grace period of 30s on startup before first scheduling decision
- Re-checks every minute for precise timing
- Existing pre-existing test failure in `test_agent_registry.py` (unrelated to this task)
