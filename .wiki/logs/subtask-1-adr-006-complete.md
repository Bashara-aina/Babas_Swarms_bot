---
title: Subtask 1 Adr 006 Complete
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Status**: ✅ Completed'
wikilinks: []
confidence: medium
source: research
---
# Subtask 1: ADR-006 Wiki Quality Gate - COMPLETE

**Date**: 2026-04-11
**Status**: ✅ Completed

## Summary

Created ADR-006 documenting the wiki quality gate system architecture:

- **fast_gate**: Heuristic checks (<5ms) for length, path traversal, spam patterns
- **deep_gate**: LLM-based scoring (0.0-1.0) on clarity/actionability/factuality/wikic-value
- **evaluate_before_write()**: Core evaluation function returning PASS/REJECT/NEEDS_IMPROVEMENT
- **Quarantine dir**: `.wiki/_quarantine/`
- **Daily scan**: Auto-quarantine score <0.3 at 1 AM JST
- **Weekly deep LLM eval**: Sunday 2 AM JST
- **Bot commands**: `/wiki_audit`, `/wiki_flush`, `/wiki_restore`, `/wiki_scan`, `/wiki_stats`

## Output

- File: `/home/newadmin/swarm-bot/.wiki/decisions/ADR-006-wiki-quality-gate.md`
- Lines: 101

## Verification

✅ File created at correct path
✅ All required content sections included
✅ ADR number 006, date 2026-04-11
