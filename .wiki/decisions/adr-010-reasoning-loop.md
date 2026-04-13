---
title: "ADR-010: Pre-Response Reasoning Loop"
component: "core/reasoning_loop.py, llm_client/__init__.py"
date: "2026-04-12"
status: "ACCEPTED"
---
# ADR-010: Pre-Response Reasoning Loop

**Date:** 2026-04-12
**Status:** ACCEPTED
**Component:** core/reasoning_loop.py, llm_client/__init__.py

## Context

DEEP_AUDIT_2026-04-12.md identified the #1 gap: "No reasoning loops. Every user message follows: classify → build context → single LLM call → post-process → send. System is architecturally incapable of producing better answers than the underlying LLM."

The audit specifies Plan C, Step 1: for messages >20 words OR confidence <0.7, decompose question into sub-questions, check if search/memory needed, gather sources, return ReasoningContext.

## Decision

Create `core/reasoning_loop.py` with:
1. `reason_before_responding(message, intent, confidence)` → returns `ReasoningContext` or `None`
2. `decompose_question(message)` → splits into `SubQuestion[]` with `requires_external` and `requires_memory` flags
3. `gather_sources()` → calls memory + search tools for needed sources
4. `build_reasoning_prompt()` → formats context as injectable system message
5. `run_reasoning_loop_if_needed()` → convenience wrapper for llm_client wiring

Wire into `llm_client/__init__.py` `chat()` function: inject `[PRE-RESPONSE REASONING]` system message for complex messages.

## Architecture

```
Simple question (<20 words, confidence >0.8) → return None (skip)
Complex question → decompose → gather sources → inject reasoning block → LLM call
```

## Consequences

**Positive:**
- Legion now "thinks before answering" on complex tasks
- Sub-question decomposition surfaces the actual questions being asked
- Memory + search sources gathered before LLM call, not during

**Negative:**
- Adds token overhead for complex messages (reasoning block ~100-300 tokens)
- Slight latency increase for complex queries (sources gathered sequentially)
- Depends on memory + search tool availability

## Implementation Notes

- All functions are async
- All async calls wrapped in try/except (non-fatal failures)
- Logger calls on entry, exit, and failures
- Dependency injection pattern — imports inside functions for optional dependencies
- Simple questions skip reasoning entirely (zero overhead)