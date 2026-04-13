---
# LEGION AUDIT 04 — Context Injection (Search / Wiki / Memory / Soul)
**Date:** 2026-04-12
**Status:** In Progress
**Goal:** Ensure search results, wiki, memory, and soul are ALL in LLM context before every call

---

## Overview

This audit verifies that ALL context sources (soul, memory, wiki, search) are properly injected into the `messages[]` list before every `litellm.acompletion()` call.

## Context Sources Priority Order (MUST appear in messages[] as SYSTEM messages)
1. **Soul** — `core/soul_engine.py` → FIRST system message, NEVER conditional
2. **Memory** — `core/memory_engine.py` → SECOND system message, called BEFORE every LLM call
3. **Wiki** — `core/wiki_bridge.py` → THIRD system message, retrieved for EVERY message
4. **Conversation** — user messages and LLM responses
5. **Search** — `tools/web_search.py` → injected as SYSTEM message when search fires

## Files to Audit

| File | Purpose |
|------|---------|
| `llm_client/__init__.py` | Main LLM call site — 36+ litellm.acompletion calls |
| `core/memory_engine.py` | read_memory(user_id), write_memory() |
| `core/soul_engine.py` | get_system_prompt(), read_soul() |
| `core/wiki_bridge.py` | retrieve() function |
| `core/system_prompt_builder.py` | Assembles messages[] for LLM |
| `tools/web_search.py` | DuckDuckGo search execution |

## Audit Steps

- [ ] STEP 1: Find all LLM call sites, document messages[] state
- [ ] STEP 2: Web search injection verification
- [ ] STEP 3: Wiki injection verification  
- [ ] STEP 4: Memory injection verification
- [ ] STEP 5: Soul injection verification
- [ ] STEP 6: Final verification with debug logging

## DO NOT Modify
- SOUL.md, CLAUDE.md, LEGION_MASTER.md

---

## Subtask Assignment

See decomposed tasks assigned to @worker and @reviewer below.
