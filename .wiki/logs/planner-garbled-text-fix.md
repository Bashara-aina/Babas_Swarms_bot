---
title: Planner Garbled Text Fix
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
summary: '**Task**: Fix Telegram bot response containing garbled Russian text and
  gibberish'
wikilinks: []
confidence: medium
source: research
---
# Planner Log: Garbled Text Fix (Matsuya/Toyosu Restaurant Response)
**Date**: 2026-04-12  
**Task**: Fix Telegram bot response containing garbled Russian text and gibberish  
**Status**: ✅ Planned → Assigned to @worker

## Problem

Bot responded with garbled text ("конкрет", "памяти", "nexeny") when user asked about eating karage at Matsuya restaurant in Toyosu area.

## Root Cause Identified

Missing imports in `llm_client/__init__.py` caused context builders to fail silently:
- Lines 1113-1118 reference 4 context getters
- 3 of 4 were not properly imported (NameError silently caught)
- LLM received malformed/empty context → hallucinated garbled text

## Investigation Summary

| Check | Result |
|-------|--------|
| ADR-057 (get_relationship_context) | ✅ Already fixed |
| ADR-058 (missing imports) | ✅ Already fixed |
| ADR-059 (_cif scope bug) | ✅ Already fixed |
| ADR-060 (redundant import) | ✅ Already fixed |
| Encoding in episodic_narrative.py | ⚠️ Line 32: `read_text()` without encoding |

## Subtasks Assigned to @worker

### Subtask 1: Fix encoding in episodic_narrative.py
- **File**: `core/episodic_narrative.py` line 32
- **Change**: `NARRATIVE_PATH.read_text()` → `NARRATIVE_PATH.read_text(encoding="utf-8")`

### Subtask 2: Verify all imports in llm_client/__init__.py
- **Files**: `llm_client/__init__.py` lines 39-44
- **Action**: Confirm all 4 context getters are imported

### Subtask 3: Run tests
- **Command**: `pytest tests/ -x --asyncio-mode=auto -q`

## Review → @reviewer
**ADR**: `.wiki/decisions/ADR-090-garbled-text-context-injection.md`

---

*Planned: 2026-04-12 | Executing: @worker | Review: @reviewer*
