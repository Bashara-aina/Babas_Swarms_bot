---
title: Flow Engineering System2 Mindset
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- founder-mindset
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Source: Maryam Miradi PhD, LinkedIn 2026'
wikilinks: []
confidence: medium
source: research
---
# Flow Engineering — System 2 Agent Mindset

Source: Maryam Miradi PhD, LinkedIn 2026

## The Shift
FROM: Prompt Engineering (what do I say to the LLM?)
TO: Flow Engineering (what sequence of thinking does the agent follow?)

## System 2 Principles
- Design for THINKING TIME before action (reasoning steps)
- Reliability > Speed always
- Agents should pause and verify before executing irreversible actions
- Build "reflection" steps into multi-agent workflows

## The Blueprint
```
Input → [Understand] → [Plan] → [Verify Plan] → [Execute] → [Reflect] → Output
         (System 2)     (slow)    (check risks)              (did it work?)
```

## Applied to Legion
- task_orchestrator.py should have a PLAN step before EXECUTE
- Computer agent should verify before any destructive action
- Wiki auto-ingest should have a quality reflection step
- Never let agents act on the first interpretation of ambiguous input

## Rule
"Thinking time is not wasted time. It is the difference between
an agent that completes tasks and one that completes them correctly."
