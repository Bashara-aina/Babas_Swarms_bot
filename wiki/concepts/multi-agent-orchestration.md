---
title: multi-agent-orchestration
type: concept
status: active
tags: [agents, orchestration, swarm, multi-agent]
created: 2026-04-13
updated: 2026-04-13
summary: Multi-agent orchestration coordinates multiple specialized agents (planner, worker, reviewer) to collaborate on complex tasks through structured handoffs.
wikilinks: [[concepts/reasoning-loop.md]], [[architecture/legion-module-map.md]], [[projects/legion-bot.md]]
confidence: high
source: implementation
---

# Multi-Agent Orchestration

## TL;DR
Legion uses a three-agent pipeline (Planner → Worker → Reviewer) for complex tasks, plus a 9-department × 8-agent swarm for research tasks.

## Three-Agent Pipeline

1. **Planner** (`@planner`): Decomposes task, creates subtasks
2. **Worker** (`@worker`): Executes code changes
3. **Reviewer** (`@reviewer`): Reviews all changes before commit

## Swarm Architecture

For `/swarm` command:
- 9 departments × 8 specialist agents (72 agents)
- Department leads synthesize team positions
- 6 debate personas run 4-round structured debate
- Total: ~87 agents per swarm call

## Communication Protocol

Agents communicate via:
- Structured JSON task objects
- Shared context memory
- Result callbacks

## Related Pages

- [[projects/legion-bot.md]] — Main project
- [[architecture/legion-module-map.md]] — System architecture
