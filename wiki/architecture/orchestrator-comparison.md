---
title: orchestrator-comparison
type: architecture
status: active
tags: [orchestration, agents, comparison, swarm]
created: 2026-04-13
updated: 2026-04-13
summary: Legion uses multiple orchestration patterns: simple intent routing, three-agent pipeline, and 87-agent swarm debate.
wikilinks: [[concepts/multi-agent-orchestration.md], [concepts/intent-routing.md]]
confidence: medium
source: research
---

# Orchestrator Comparison

## TL;DR
Three orchestration patterns at different complexity levels: fast intent routing, three-agent pipeline, and full swarm debate.

## Pattern Comparison

| Pattern | Agents | Latency | Use Case |
|---------|--------|---------|----------|
| Intent Routing | 1 | <100ms | Simple commands |
| Three-Agent Pipeline | 3 | 30-120s | Code tasks |
| Swarm Debate | 87 | 60-120s | Complex research |

## Pattern 1: Intent Routing

```
User → [Router] → [Handler] → [Response]
```

- Fastest, lowest cost
- For: commands, simple queries
- Agents involved: 1 (router)

## Pattern 2: Three-Agent Pipeline

```
Task → [Planner] → [Worker] → [Reviewer] → Response
```

- Balances quality and speed
- For: code tasks, analysis
- Agents: 3 (planner, worker, reviewer)

## Pattern 3: Swarm Debate

```
Topic → [9 Depts × 8 Agents] → [6 Debate Personas] → Verdict
```

- Highest quality, highest cost
- For: complex decisions, research
- Agents: ~87 per call

## When to Use Each

| Task | Pattern |
|------|---------|
| "Hello" | Intent routing |
| "/research X" | Three-agent |
| Strategic decision | Swarm |

## Related Pages

- [[concepts/multi-agent-orchestration.md]] — Detailed orchestration
- [[concepts/intent-routing.md]] — Simple routing
