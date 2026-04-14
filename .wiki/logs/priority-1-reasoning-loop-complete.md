---
title: Priority 1 Reasoning Loop Complete
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
summary: '**Completed:** 2026-04-12'
wikilinks: []
confidence: medium
source: research
---
# PRIORITY 1: Pre-Response Reasoning Loop — COMPLETE

**Completed:** 2026-04-12
**File created:** `core/reasoning_loop.py`
**File modified:** `llm_client/__init__.py` (wired reasoning loop)
**Verification:** `python scripts/verify_wiring.py` → PASS

## What Was Done

### 1. Created `core/reasoning_loop.py`
A new module implementing the pre-response reasoning loop from the DEEP_AUDIT:

- `reason_before_responding(message, intent, confidence)` — main entry point
  - Returns `None` for simple questions (skip reasoning overhead)
  - For messages >20 words OR confidence <0.7: decompose → gather sources → return ReasoningContext
- `decompose_question(message)` — splits complex messages into SubQuestions
  - Handles multi-part questions (numbered, first/then)
  - Handles multiple question marks
  - Detects complexity based on word count + keywords
- `_needs_external_knowledge(text)` — heuristic for web search need
- `_needs_memory(text)` — heuristic for memory retrieval need
- `gather_sources(sub_questions, search, memory)` — gathers from memory + search tools
- `build_reasoning_prompt(context)` — formats context as a system message block
- `run_reasoning_loop_if_needed(message, intent, confidence)` — convenience wrapper for llm_client wiring

### 2. Wired into `llm_client/__init__.py`
Added reasoning loop invocation in `chat()` function:
- Line 1203-1222: Pre-response reasoning block
- Runs for messages >20 words OR confidence <0.7
- Injects `[PRE-RESPONSE REASONING]` system message with sub-questions + sources
- All wrapped in try/except — failures are non-fatal

### 3. Verification
`python scripts/verify_wiring.py` → ALL PASS (7/7 tests)

## Key Decisions

### ADR-010: Pre-Response Reasoning Loop Architecture
**Decision:** Implement reasoning as an injectable system message block rather than modifying the core LLM call path
**Rationale:** Minimal invasion — doesn't change the message construction flow, just adds one more system message before user input
**Consequences:** Reasoning output adds tokens to every complex response; can be disabled by not calling `run_reasoning_loop_if_needed`

## Remaining Work
- None for this priority
- Next: Priority 2 — Unify Memory to 2 Tiers