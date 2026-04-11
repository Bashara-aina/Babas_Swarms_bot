# Subtask 6: Wiki Handler Commands - COMPLETE

**Date:** 2026-04-11
**Task:** Create wiki audit command handlers

## Files Created

### `/home/newadmin/swarm-bot/handlers/wiki.py`
New file with 5 Command handlers:
- `/wiki_audit` - Full quality report (runs weekly deep evaluation, sends report)
- `/wiki_flush` - Empty quarantine (delete all quarantined files permanently)
- `/wiki_restore` - Restore from quarantine (moves back, re-evaluates quality)
- `/wiki_scan` - On-demand quick scan NOW (fast heuristic only)
- `/wiki_stats` - Quality statistics (page count, avg score by directory)

**Pattern:** aiogram 3.x Router with `is_allowed()` auth check from `handlers.shared`

## Files Modified

### `/home/newadmin/swarm-bot/handlers/__init__.py`
- Added `from handlers.wiki import router as wiki_router` (line 46)
- Added `wiki_router` to `_ROUTER_ORDER` before `ai.router` (line 80)

### `/home/newadmin/swarm-bot/main.py`
- Added 5 BotCommand entries for wiki commands (lines 745-749):
  - `wiki_audit` - Wiki quality status + quarantine
  - `wiki_scan` - Run full wiki deep evaluation
  - `wiki_stats` - Wiki quality by directory
  - `wiki_flush` - Delete quarantined wiki files
  - `wiki_restore` - Restore quarantined files

## Verification
```bash
cd /home/newadmin/swarm-bot && python -c "from handlers.wiki import router; print(f'wiki_handler imported successfully, type: {type(router).__name__}')"
# Output: wiki_handler imported successfully, type: Router
```

```bash
cd /home/newadmin/swarm-bot && python -c "from handlers import wiki_router, _ROUTER_ORDER; print(f'wiki_router position: {len(_ROUTER_ORDER) - _ROUTER_ORDER[::-1].index(wiki_router) - 1} of {len(_ROUTER_ORDER)}')"
# Output: wiki_router position: 29 of 31 (before ai.router at position 30)
```

## Dependencies Used
- `core.wiki_scheduler.WikiQualityScheduler` - for `_weekly_deep_scan()`
- `core.wiki_quality_gate.fast_gate` - for heuristic scanning
- `core.wiki_quality_gate.flush_quarantine` - for emptying quarantine
- `core.wiki_quality_gate.restore_from_quarantine` - for restoring
- `handlers.shared.is_allowed` - auth check helper
