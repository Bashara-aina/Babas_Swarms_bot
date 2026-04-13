---
title: context-window-budget
type: concept
status: active
tags: [context, tokens, budget, optimization]
created: 2026-04-13
updated: 2026-04-13
summary: Context window budget manages token usage to prevent exceeding LLM context limits while preserving important system instructions and recent conversation.
wikilinks: [[concepts/memory-architecture.md], [concepts/llm-cost-routing.md]]
confidence: high
source: implementation
---

# Context Window Budget

## TL;DR
Context window budget actively manages token usage by trimming old conversation turns while always preserving system prompt and critical context.

## Budget Allocation

For a 200K context model:

| Component | Max Tokens | Priority |
|-----------|------------|----------|
| System prompt (SOUL.md) | 4000 | Critical (never trim) |
| Wiki context | 8000 | High |
| Recent conversation | 16000 | Medium |
| Working memory | 2000 | Low |

## Trimming Strategy

1. **Soft trim**: Remove oldest user/assistant turns when >80% full
2. **Hard trim**: Aggressive trim keeping last N turns when >95% full
3. **Never trim**: System prompt, character definition

## Implementation

In `core/system_prompt_builder.py`:
- `estimate_tokens(text)` using tiktoken or approximation
- `trim_conversation(history, max_tokens)` to prune
- Always keep first message (system) intact

## Related Pages

- [[concepts/memory-architecture.md]] — Memory layers
- [[concepts/llm-cost-routing.md]] — Cost considerations
