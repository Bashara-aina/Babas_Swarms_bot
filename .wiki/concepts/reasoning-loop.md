---
title: reasoning-loop
type: concept
status: active
tags: [reasoning, llm, planning, agent, chain-of-thought]
created: 2026-04-13
updated: 2026-04-13
summary: The reasoning loop enables Legion to plan, execute, observe, and refine approach iteratively before committing to a final response, activated by complex or high-stakes tasks.
wikilinks:
  - [[intent-routing]]
  - [[multi-agent-orchestration]]
  - [[self-improvement-loop]]
confidence: high
source: implementation
---

# Reasoning Loop

## TL;DR
The reasoning loop is an internal cycle where Legion thinks through complex requests step-by-step before responding: parse the request, plan subtasks, execute tools/APIs, observe results, refine the approach, then respond. It activates for research queries, code generation, multi-step analysis, and architecture decisions — and can loop multiple times if the first attempt doesn't resolve the problem.

## Overview

Not every message needs deep thinking. A casual "ok" or "thanks" gets a short reply. But "explain the tradeoffs between Supabase Auth and Clerk" or "write a Python script to rename all files in a folder" requires reasoning that goes beyond a single LLM call. The reasoning loop exists precisely for those cases: it structures thinking into discrete phases so the LLM can course-correct before presenting a final answer.

## Context

Legion must sometimes handle tasks where the first approach fails or where the problem space is unclear. A user asks "cek gpu status" — that's a single tool call. But "analisa thesis progress" might need multiple tool calls (read log files, parse nvidia-smi, check dates, synthesize findings) in a sequence that can't be predicted in advance. The reasoning loop allows iterative refinement rather than a single shot.

## Key Properties

- **Phase-gated execution**: Parse → Plan → Execute → Observe → Refine → Respond
- **Iterative loops**: Can cycle back through refine/execute/observe multiple times until resolution
- **Tool-augmented**: Reasoning can invoke tools mid-loop (not just at execute phase)
- **Intent-triggered**: Activated by specific intent categories (research, code, analysis, deep_reasoning)
- **Timeout protection**: Entire loop wrapped in asyncio.wait_for to prevent infinite loops
- **Context-carrying**: Each iteration accumulates observations, building toward a final synthesis
- **Supports multi-agent**: Planner → Worker → Reviewer pipeline uses reasoning loop at each handoff

## How It Works

### Activation
Intent routing marks certain intents as needing deep reasoning: `WEB_RESEARCH`, `CODE_GENERATION`, `DATA_ANALYSIS`, `DEEP_REASONING`, `SELF_UPGRADE`. When these intents are detected, the handler layer passes control to the reasoning loop instead of a simple respond-and-done path.

### Parse Phase
The request is broken down into its components: what is the user asking for, what constraints exist (time, budget, format), what prior context is available from memory, and what tools or knowledge sources are needed.

### Plan Phase
A step-by-step plan is constructed. For code generation: identify files to modify, define the function signature, plan error handling. For research: identify information sources, define the synthesis structure, set completeness criteria.

### Execute Phase
Tools are called, APIs are invoked, files are read or written. Results are collected but not yet presented to the user.

### Observe Phase
Executed results are evaluated: did the tool call succeed, is the data in the expected format, does the partial result suggest the plan was correct?

### Refine Phase
If observe reveals problems (tool failed, data unexpected, approach wrong), the plan is adjusted and execute runs again. This is the critical differentiator from single-shot responses.

### Respond Phase
Final synthesized response is sent to the user. If the loop iterated multiple times, a summary of what was tried and what worked is included.

## Relationships

The reasoning loop is the mechanism that makes [[multi-agent-orchestration]] possible. The three-agent pipeline (Planner → Worker → Reviewer) uses the reasoning loop at each handoff: Planner's decomposition is a reasoning loop output, Worker's execution is instrumented with observe/refine cycles, Reviewer's assessment triggers another loop if issues are found. [[self-improvement-loop]] feeds outcomes back into future reasoning iterations — failed approaches are recorded so the refine phase can avoid them next time. [[intent-routing]] is the trigger source: intent classification determines whether the reasoning loop activates at all.

## Current Status

**Implemented.** Basic reasoning loop structure exists in the intent router and agent handlers. Iterative refinement is used in `/research` and `/think` commands. The three-agent pipeline with reason-loop handoffs is defined in architecture docs. Refine-phase loop-back is implemented for research tasks. Further instrumentation of tool-augmented reasoning loops across all agent types is ongoing (Phase 2).

## See Also

- [[intent-routing]] — Triggers that activate the reasoning loop
- [[multi-agent-orchestration]] — Three-agent pipeline using reasoning loops
- [[self-improvement-loop]] — Learning from loop outcomes
