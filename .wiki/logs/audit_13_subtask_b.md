---
title: Audit 13 Subtask B
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
summary: '**Status:** ✅ COMPLETE'
wikilinks: []
confidence: medium
source: research
---
# AUDIT 13 — SUBTASK B: Explicit PLANNED flags in stub files

**Date:** 2026-04-12  
**Worker:** @worker  
**Status:** ✅ COMPLETE

## Summary

Added explicit `FEATURE_*_ENABLED = False  # Planned: v2.0` flags to 5 files, plus graceful user messages where the features are triggered.

## Files Modified

### 1. `core/daily_harvester/topic_budget.py`
- Added flag: `FEATURE_GIT_LOG_ANALYSIS_ENABLED = False  # Planned: v2.0` (line 15)
- Added user message in `_get_git_commit_count()`: logs "Git log analysis feature is planned for v2.0 — not yet available."

### 2. `core/daily_harvester/harvest_pipeline.py`
- Added flag: `FEATURE_BRIEFING_CONSOLIDATION_ENABLED = False  # Planned: v2.0` (line 16)
- Added user message in `_generate_report()`: logs "Briefing consolidation feature is planned for v2.0 — not yet available."

### 3. `core/daily_harvester/source_strategy.py`
- Added flag: `FEATURE_WEB_SEARCH_ENABLED = False  # Planned: v2.0` (line 13)
- Added user message in `search_sources()`: logs "Web search feature is planned for v2.0 — not yet available."

### 4. `core/daily_harvester/topic_evolution.py`
- Added flag: `FEATURE_TOPIC_WEIGHTS_ENABLED = False  # Planned: v2.0` (line 10)
- Added user message in `detect_new_topic()`: logs "Topic weights feature is planned for v2.0 — not yet available."

### 5. `main.py` (around line 551)
- Added flag: `FEATURE_BRIEFING_CONSOLIDATION_ENABLED = False  # Planned: v2.0`
- Added user message: logs "Briefing consolidation is planned for v2.0 — not yet available."

## Tests
- Ran: `pytest tests/ -x --asyncio-mode=auto -q`
- Result: **373 passed, 2 warnings** — all passing