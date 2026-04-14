---
title: Opencode Agents
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
summary: Create 5 opencode agents + wire opencode serve into bot startup
wikilinks: []
confidence: medium
source: research
---
# 2026-04-11 — OPENCODE AGENTS + AUTOSTART

## Task
Create 5 opencode agents + wire opencode serve into bot startup

## Pipeline
- Planner → decomposed 11 subtasks
- Worker → executed all tasks
- Reviewer → found 1 HIGH issue (missing model: field) → fixed
- WikiBot → documented

## Files Created/Modified

| File | Action | Lines |
|------|--------|-------|
| .opencode/agent/research-agent.md | Created | 47 |
| .opencode/agent/focused-implementer.md | Created | 51 |
| .opencode/agent/diff-analyzer.md | Created | 84 |
| .opencode/agent/paper-wiki-writer.md | Created | 58 |
| .opencode/agent/deployment-engineer.md | Created | 106 |
| main.py | Modified | +38 |

## Verification
- `ruff check --fix main.py` — 5 fixable (pre-existing import sorting)
- `python -m py_compile main.py` — PASS
- `pytest tests/` — 276 PASS, 1 warning

## Reviewer Issue Fixed
- Added `model: minimax-coding-plan/MiniMax-M2.7` to all 5 agent YAML frontmatter

## Status
COMPLETE ✅
