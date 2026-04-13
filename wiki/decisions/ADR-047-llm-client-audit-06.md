---
title: Adr 047 Llm Client Audit 06
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-047 — LLM Client Layer Audit 06

**Date:** 2026-04-12  
**Type:** Architecture — LLM Interface Standardization  
**Status:** Accepted

---

## Context

AUDIT 06 identified that the LLM client layer lacks a canonical `call_llm()` function with the signature:

```python
async def call_llm(
    messages: list[dict],
    model: str = None,
    tools: list = None,
    stream: bool = False,
    **kwargs
) -> str | dict
```

The codebase has:
- `llm_client.py` — root-level backwards-compatibility shim (already correctly re-exporting from `llm_client/`)
- `llm_client/__init__.py` — 1729-line package with all real logic
- 107 files importing from `llm_client`
- Internal `_call_model()` returning raw litellm response objects
- `agent_loop()` handling tool_calls in a full agentic loop
- No `call_llm()` public function at all

---

## Decision

1. **Create a new `call_llm()` public function** in `llm_client/__init__.py` that:
   - Accepts `messages`, `model`, `tools`, `stream`, and `**kwargs`
   - Uses `get_fallback_chain()` to build the model chain
   - Iterates through the chain on rate limits/errors
   - Returns plain string for normal responses
   - Returns `{"type": "tool_call", "name": ..., "args": ...}` dict when LLM emits tool_calls
   - Never returns raw litellm response objects

2. **Export `call_llm` from both `llm_client/__init__.py` and `llm_client.py`** shim

3. **Keep existing functions** (`chat()`, `agent_loop()`, `_call_model()`, `wiki_raw_completion()`) unchanged — they serve different purposes

4. **Use existing infrastructure** for fallback:
   - `get_fallback_chain()` from `core/conversation_interface.py`
   - `_is_rate_limited()` / `_mark_rate_limited()` for rate limit handling
   - `_call_model()` internal retry logic

---

## Consequences

**Positive:**
- Single canonical LLM call interface for simple tasks
- Tool calls properly surfaced as dicts for callers that need them
- Consistent fallback behavior via established chain system

**Risks:**
- `call_llm()` overlaps somewhat with `chat()` — different use cases but potential confusion
- Need to ensure the new function is exported correctly for all 107 importers

**Mitigation:**
- `call_llm()` is for single-turn, tool-aware calls
- `chat()` is for the full Legion personality/humanization pipeline
- Clear docstrings differentiate purpose

---

## Files Changed

- `llm_client/__init__.py` — add `call_llm()` function
- `llm_client.py` — add `call_llm` to re-exports and `__all__`
