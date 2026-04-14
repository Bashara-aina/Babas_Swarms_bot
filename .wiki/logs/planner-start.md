---
title: Planner Start
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
summary: '**Task**: Fix `NameError: name ''get_relationship_context'' is not defined`'
wikilinks: []
confidence: medium
source: research
---
# Planner Log: get_relationship_context Bugfix
**Date**: 2026-04-12  
**Task**: Fix `NameError: name 'get_relationship_context' is not defined`

## Investigation Summary

| Item | Value |
|------|-------|
| Error | `NameError: name 'get_relationship_context' is not defined` |
| Source file | `llm_client/__init__.py` line 1114 |
| Function defined | `core/relationship_memory.py` line 164 |
| Root cause | Missing import in `llm_client/__init__.py` |

---

## Subtasks

| # | Description | Assigned |
|---|-------------|----------|
| 1 | Add `from core.relationship_memory import get_relationship_context` to `llm_client/__init__.py` import block | @worker |
| 2 | Run `pytest tests/ -x --asyncio-mode=auto -q` to verify fix | @worker |
| 3 | Review diff of `llm_client/__init__.py` | @reviewer |

---

## ADR
Written to: `.wiki/decisions/ADR-057-bugfix-get-relationship-context.md`

---

## Status
**STARTED** — awaiting @worker to execute subtasks.
