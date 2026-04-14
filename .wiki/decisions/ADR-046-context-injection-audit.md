---
title: Adr 046 Context Injection Audit
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Type:** Audit / Bug Fix'
wikilinks: []
confidence: medium
source: research
---
# ADR-046: Context Injection Audit — Ensure All Context Sources in LLM Calls

**Date:** 2026-04-12
**Status:** Active
**Type:** Audit / Bug Fix

## Context

LEGION AUDIT 04 is a systematic audit to verify that before every `litellm.acompletion()` call, the following context sources are ALL present in the `messages[]` array:

1. **Soul** (system) — from `core/soul_engine.py`
2. **Memory** (system) — from `core/memory_engine.py` 
3. **Wiki** (system) — from `core/wiki_bridge.py`
4. **Conversation history** — user/assistant messages
5. **Search results** (system) — from `tools/web_search.py`

## Problem Statement

Based on prior audits (ADR-045), web search results were not being properly injected into LLM context. A broader audit is needed to verify ALL context sources are properly injected.

## Audit Scope

### Files to Audit
- `llm_client/__init__.py` — Main LLM client with 36+ call sites
- `core/memory_engine.py` — read_memory(), write_memory()
- `core/soul_engine.py` — get_system_prompt(), read_soul()
- `core/wiki_bridge.py` — retrieve()
- `core/system_prompt_builder.py` — message assembly
- `tools/web_search.py` — DuckDuckGo search

### Context Injection Requirements

| Context | Source | Injection Point | Mandatory? |
|---------|--------|-----------------|------------|
| Soul | soul_engine.py | FIRST system message | YES — never conditional |
| Memory | memory_engine.py | SECOND system message | YES — every LLM call |
| Wiki | wiki_bridge.py | THIRD system message | YES — every message |
| Search | web_search.py | System message on search | Only when search fires |

## DO NOT Modify
- SOUL.md
- CLAUDE.md
- LEGION_MASTER.md

## Verification

After audit, add debug logging at LLM call site:
```python
logger.debug(f"messages count={len(messages)}, roles={[m['role'] for m in messages]}")
```

Final verification checklist:
- [ ] soul (system) is FIRST message
- [ ] memory (system) is present
- [ ] wiki (system) is present
- [ ] conversation messages present
- [ ] search results (system) present when search fired
