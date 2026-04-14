---
title: Planner Start 4
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
summary: Remove redundant local import of `classify_intent_fast` in `llm_client/__init__.py`
  line 982.
wikilinks: []
confidence: medium
source: research
---
# Planner Log: Cleanup Redundant Import Task

## Date: 2026-04-12

## Task
Remove redundant local import of `classify_intent_fast` in `llm_client/__init__.py` line 982.

## Analysis
- **File**: `llm_client/__init__.py`
- **Redundant import line**: 982 — `from core.intent_router import classify_intent_fast`
- **Already imported at**: line 44 (module scope)
- **Context**: Inside function `generate_response`, try block for intent classification

## Decision
ADR-060 written to `.wiki/decisions/ADR-060-cleanup-redundant-import.md`

## Subtasks
1. Remove line 982 (the redundant import statement only)
2. Verify surrounding try block remains syntactically valid
3. Run linter to confirm no issues

## Status
**In Progress** — awaiting worker execution
