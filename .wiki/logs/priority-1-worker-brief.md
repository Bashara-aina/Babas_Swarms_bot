---
title: Priority 1 Worker Brief
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
summary: '**File to create:** `core/reasoning_loop.py`'
wikilinks: []
confidence: medium
source: research
---
# PRIORITY 1: Pre-Response Reasoning Loop
**File to create:** `core/reasoning_loop.py`
**Auditor:** DEEP_AUDIT_2026-04-12.md Section 1 (Intelligence Depth)

## Why This Is Priority 1
The audit says: "No reasoning loops. Every user message follows: classify → build context → single LLM call → post-process → send. System is architecturally incapable of producing better answers than the underlying LLM."

Creating `core/reasoning_loop.py` is the single highest-impact change.

## What to Build
```python
# core/reasoning_loop.py

async def reason_before_responding(message: str, intent: str, confidence: float) -> Optional[ReasoningContext]:
    """
    For messages >20 words OR confidence <0.7:
    1. Decompose question into sub-questions
    2. Check if search/memory needed
    3. Gather sources
    4. Return ReasoningContext with structured input for LLM
    
    For simple questions (short, high confidence): return None (skip reasoning)
    """
```

## Spec from Audit (Plan C, Step 1)
```
async def reason_before_responding(message, intent, confidence):
    if len(message) < 20 and confidence > 0.8:
        return None  # Simple question, skip reasoning
    
    # Step 1: Decompose
    sub_questions = await decompose_question(message)
    
    # Step 2: Check sources needed
    needs_search = any(sq.requires_external for sq in sub_questions)
    needs_memory = any(sq.requires_memory for sq in sub_questions)
    
    # Step 3: Gather
    sources = await gather_sources(sub_questions, search=needs_search, memory=needs_memory)
    
    # Step 4: Build reasoning context
    return ReasoningContext(sub_questions, sources, confidence)
```

## Requirements
1. **async def** — all functions async
2. **Proper imports** — type hints, logging
3. **try/except** on all async calls — never let reasoning loop crash the bot
4. **logger calls** — log entry and exit of reasoning, any failures
5. **Dependency injection** — don't hardcode imports, accept as parameters where sensible
6. **Return `None` for simple questions** — the loop should be opt-in, not mandatory overhead

## Files to Modify
- Create: `core/reasoning_loop.py` (new)
- Modify: `llm_client/__init__.py` — wire the reasoning loop into the `chat()` function before the LLM call. The loop should run for messages >20 words or confidence <0.7.

## Verification
- After creating, call `python scripts/verify_wiring.py` — must pass
- The reasoning loop must not break any existing handler
- Write result to `.wiki/logs/priority-1-reasoning-loop-complete.md`

## Hard Rules
- Never edit SOUL.md, CLAUDE.md, LEGION_MASTER.md
- Do NOT delete any file — create new only
- Every new function must have: async def, try/except, logger calls, type hints