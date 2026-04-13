---
title: adr-2026-04-12-multi-agent-pipeline
type: decision
status: accepted
tags: [multi-agent, pipeline, planner, worker, reviewer]
created: 2026-04-12
updated: 2026-04-12
summary: Three-agent pipeline (Planner → Worker → Reviewer) adopted as standard for complex tasks.
wikilinks:
  - [[./concepts/multi-agent-orchestration]]
  - [[legion-bot]]
confidence: high
source: decision
---

# ADR: Three-Agent Pipeline

**Date**: 2026-04-12  
**Status**: ACCEPTED

## Context

Complex tasks need structured approach. Single-agent has limitations:
- Tendency to rush to solution
- Limited self-correction
- No independent review

## Decision

Adopt three-agent pipeline:

```
Task → [PLANNER] → Subtasks
              ↓
        [WORKER] → Implementation
              ↓
         [REVIEWER] → Review
              ↓
         Report → User
```

## Agent Roles

| Agent | Responsibility |
|-------|---------------|
| Planner | Decompose task, create subtasks |
| Worker | Execute changes, write code |
| Reviewer | Verify quality, flag issues |

## Consequences

### Positive
- Independent verification
- Better task decomposition
- Clearer accountability

### Negative
- Higher latency (3x LLM calls)
- Higher cost

## Related Pages

- [[./concepts/multi-agent-orchestration]] — Details
- [[legion-bot]] — Project context
