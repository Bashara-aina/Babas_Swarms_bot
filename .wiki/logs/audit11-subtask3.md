---
title: Audit11 Subtask3
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
summary: Add a docstring explaining what `core/orchestration/__init__.py` does.
wikilinks: []
confidence: medium
source: research
---
# AUDIT 11 — Subtask 3: Add docstring to core/orchestration/__init__.py

## Task
Add a docstring explaining what `core/orchestration/__init__.py` does.

## Action Taken
Read all module files inside `core/orchestration/`:
- `supervisor.py` — Hierarchical Supervisor Agent; decomposes complex tasks into SubTasks, schedules them sequentially/in parallel, synthesizes results
- `swarm_patterns.py` — Swarm intelligence patterns (Voting, Critique-Refine, Debate) plus `select_pattern()` heuristics

Added the following docstring to `core/orchestration/__init__.py`:

```python
"""Orchestration layer for multi-agent collaboration in SwarmBot.

This module provides two complementary orchestration systems:

* **Supervisor** (`supervisor.py`) — Hierarchical task decomposition and execution.
  Breaks complex tasks into atomic SubTasks, schedules them sequentially or in parallel
  (up to MAX_PARALLEL=3), and synthesizes results via the mentor agent.
  Activated when tasks exceed COMPLEXITY_THRESHOLD (120 tokens) or contain
  multi-step keywords or cross-domain indicators.

* **Swarm Patterns** (`swarm_patterns.py`) — Peer-based collaboration patterns.
  - Voting: N agents solve independently → judge selects the best
  - Critique-Refine: producer generates → critic reviews → producer refines (iterative)
  - Debate: agents argue proposals → architect synthesizes consensus
  Includes `select_pattern()` heuristics to pick the right pattern for a task.

Both systems delegate actual LLM calls to the provided `run_fn` callback, keeping
this layer purely about coordination and flow control.
"""
```

## Verification
- File written: `/home/newadmin/swarm-bot/core/orchestration/__init__.py`
- No syntax errors (valid Python docstring)
- Follows import order (stdlib → local) with `from __future__ import annotations`

## Status
✅ Complete
