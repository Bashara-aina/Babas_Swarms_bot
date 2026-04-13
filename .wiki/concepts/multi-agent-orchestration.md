---
title: multi-agent-orchestration
type: concept
status: active
tags: [agents, orchestration, swarm, multi-agent, planner, worker]
created: 2026-04-13
updated: 2026-04-13
summary: Multi-agent orchestration coordinates specialized agents in structured pipelines and large-scale swarm debates, enabling Legion to tackle complex tasks beyond single-agent capability.
wikilinks:
  - [[reasoning-loop]]
  - [[skill-registry]]
  - [[self-improvement-loop]]
  - [[legion-module-map]]
  - [[legion-bot]]
confidence: high
source: implementation
---

# Multi-Agent Orchestration

## TL;DR
Multi-agent orchestration coordinates multiple specialized agents to collaborate on complex tasks. Legion uses two modes: a three-agent pipeline (Planner → Worker → Reviewer) for software development tasks, and a 9-department × 8-agent swarm (72 agents) for research and analysis tasks where diverse perspectives need to be synthesized.

## Overview

A single LLM call is sufficient for simple tasks. But complex work — writing a full application, conducting deep research, debating a contested architectural decision — benefits from multiple specialized perspectives operating in sequence or parallel. Multi-agent orchestration provides the infrastructure for theseagent collaborations: structured handoffs, shared context, result synthesis, and debate protocols.

## Context

Legion must handle tasks that require different skill domains simultaneously. A `/swarm` research task might need economics, legal, market, and technical perspectives. A coding task needs someone to plan the architecture, someone to write the code, and someone to review it. Human organizations use division of labor for good reason — multi-agent orchestration applies the same principle to LLM agents.

## Key Properties

- **Three-Agent Pipeline**: Planner decomposes tasks, Worker executes changes, Reviewer audits before commit
- **Swarm Architecture**: 9 departments × 8 specialist agents = 72 agents per swarm call, plus department leads
- **Department Synthesis**: Each department's 8 agents produce a position, then the department lead synthesizes
- **6-Persona Debate**: 6 structured debate personas run 4-round debates on contested questions
- **Structured Communication**: Agents communicate via JSON task objects, shared context memory, result callbacks
- **Context Persistence**: Agents share memory architecture across handoffs — no context loss between pipeline stages
- **Total agent count**: ~87 distinct agent personalities per swarm call

## How It Works

### Three-Agent Pipeline (for `/run`, `/think`)
1. **Planner** (`@planner`): Analyzes the request, decomposes into subtasks with dependencies, creates a task tree. Outputs a structured task list with priorities and estimated complexity.
2. **Worker** (`@worker`): Executes code changes per the task list. Has full file and bash access. Reports progress and blockers back to the planner.
3. **Reviewer** (`@reviewer`): Reviews all changes before commit. Runs tests, checks for regressions, enforces coding standards. Can request rework from the worker.

The pipeline is synchronous per stage: planner completes, then worker starts, then reviewer. Rework loops back to worker if reviewer finds issues.

### Swarm Mode (for `/swarm`)
Departments: Engineering, Product, Marketing, Sales, Research, Legal, Finance, Operations, Data. Each has 8 specialist agents covering sub-domains (e.g., Engineering has backend, frontend, DevOps, security, etc.).

Flow:
1. The question/problem is broadcast to all 72 agents simultaneously
2. Each agent produces a position from their domain expertise
3. Department leads synthesize their 8 agents' positions into a department position
4. 6 debate personas run 4-round structured debate on contested issues
5. A final synthesis report aggregates all positions and the debate outcome

Communication is via structured JSON task objects passed through a shared context store. Agents can call back to the shared memory system to read prior context or write results.

## Relationships

Multi-agent orchestration is the execution layer built on top of [[reasoning-loop]]. Each agent in the pipeline runs its own reasoning loop — Planner's decomposition is a reasoning loop, Worker's execution is instrumented with observe/refine cycles, Reviewer triggers another loop if issues are found. The three-agent pipeline directly implements the Planner-Worker-Reviewer pattern documented in the swarm architecture. [[skill-registry]] provides the capability catalog that agents draw from when executing skill-based tasks. [[self-improvement-loop]] captures outcomes: if a swarm debate produces a particularly good synthesis or a pipeline stage fails repeatedly, that learning gets stored for future iterations.

## Current Status

**Implemented.** Three-agent pipeline is defined in swarm architecture docs and partially wired in main.py. Swarm command exists with 72-agent structure. Department synthesis and debate personas are defined. Full pipeline wiring and swarm execution flow through main.py is still being instrumented (Phase 2 work). 87 distinct agent personalities are defined in prompt templates.

## See Also

- [[reasoning-loop]] — Reasoning cycles within each agent
- [[legion-module-map]] — System architecture
- [[legion-bot]] — Main project documentation
