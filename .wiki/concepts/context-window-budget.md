---
title: context-window-budget
type: concept
status: active
tags: [context, tokens, budget, optimization, llm, prompt-engineering]
created: 2026-04-13
updated: 2026-04-13
summary: Context window budget actively manages token usage across Legion's prompt layers, allocating space to system prompt, memory, wiki, and conversation context while always preserving the SOUL definition.
wikilinks:
  - [[memory-architecture]]
  - [[vector-search]]
  - [[llm-cost-routing]]
  - [[intent-routing]]
confidence: high
source: implementation
---

# Context Window Budget

## TL;DR
Context window budget is the token management system that prevents Legion's prompts from exceeding LLM context limits while always preserving critical system content (SOUL.md, character definition). It allocates a maximum of 35% of the model's context window to the system prompt, distributes that budget across layers by priority (soul → user_profile → working_memory → relevant_memory → wiki_context → search_results → personality → skill_context), and compresses lower-priority content when space runs out.

## Overview

LLMs have fixed context windows (8K to 200K tokens depending on model). Every component of Legion's system prompt — SOUL definition, personality, memory, wiki, conversation history, agent role — must fit within that window alongside the user's actual message. The budget system ensures critical content survives while less important content is compressed or dropped first.

## Context

A 200K context model sounds large, but Legion's prompt stack is dense: SOUL.md (~4000 tokens), wiki context (~8000 tokens), conversation history (~16000 tokens), memory blocks, personality layers, and agent role prompts. For a 200K model, the 35% budget rule gives ~5600 tokens for the system prompt. Without active budget management, the SOUL definition or recent conversation could be silently truncated mid-prompt, causing subtle but serious degradation.

## Key Properties

- **35% budget rule**: System prompt uses max 35% of model's context window (configurable via CONTEXT_BUDGET_RATIO)
- **Priority-ordered layers**: soul > user_profile > working_memory > relevant_memory > wiki_context > search_results > personality > skill_context
- **SOUL is never compressed**: Soul layer is always first and literally never compressed — if it exceeds budget, lower layers are dropped before it
- **Soft compression**: Content >80% of budget gets compressed to 200-token target
- **Hard compression**: Content >95% of budget gets aggressively trimmed
- **Model-specific limits**: MODEL_CONTEXT_LIMITS dict maps model names to their actual context sizes
- **Tiktoken estimation**: Token count estimated as len(text) // 4 for English-dominated text
- **Middle truncation**: When compressing long content, start and end are preserved with `[COMPRESSED]` marker in middle

## Budget Allocation by Model

For a 200K context model at 35% budget:
| Component | Max Tokens | Priority |
|-----------|------------|----------|
| System prompt total | 5600 | — |
| Soul (SOUL.md) | 4000 | Critical — never trim |
| Wiki context | 8000 | High |
| Recent conversation | 16000 | Medium |
| Working memory | 2000 | Low |

## How It Works

### Token Estimation
`estimate_tokens(text)` divides character count by 4 — a reasonable approximation for English text. This is used both for budgeting and for compression targeting.

### Layer Addition Loop
The `build_system_prompt()` function iterates through `LAYER_PRIORITY` and adds each layer if budget allows:
1. Fetch layer content via `get_layer_content()`
2. Estimate layer token count
3. If adding layer exceeds budget: try 200-token compression
4. If layer is "soul" and no sections exist yet: compress soul to 90% of budget (last resort)
5. If layer is anything else and compressed version fits: add compressed
6. Otherwise: skip this layer

### Compression Strategy
`compress_section(content, target_tokens=200)` preserves the beginning and end of content, truncating the middle. This is intentional — for most structured content (lists, narratives), the beginning (context) and end (conclusions) are more valuable than the middle.

### Model Context Limits
```python
MODEL_CONTEXT_LIMITS = {
    "default": 16000,
    "gpt-4o": 128000,
    "claude-3-5-haiku": 200000,
}
```
Budget is computed as `MODEL_CONTEXT_LIMITS[model] * CONTEXT_BUDGET_RATIO`.

## Relationships

Context window budget is closely tied to [[llm-cost-routing]] — every token in the prompt costs money (or API rate credits). Budgeting directly affects which models can be used cost-effectively: a 128K context model at 35% budget gives ~44K tokens for system prompt vs ~5.6K for a 16K model. [[memory-architecture]] is constrained by the budget: memory layers compete with wiki context and conversation history for the same finite space. [[vector-search]] retrieval results are among the "relevant_memory" layer — if too many memories are retrieved, they can crowd out other layers. [[intent-routing]] result (the IntentResult) is injected into prompts and must fit within budget.

## Current Status

**Implemented.** Budget management is functional in `core/system_prompt_builder.py`. The 35% budget ratio is enforced. Soul layer compression is prevented. Layer priority ordering is applied. Model context limits are defined for major models. Compression uses middle-truncation strategy. Budget checking runs on every `build_system_prompt()` call.

## See Also

- [[llm-cost-routing]] — Cost implications of token budgeting
- [[memory-architecture]] — Memory layers that compete for budget space
- [[vector-search]] — Retrieval results that fill relevant_memory layer
- [[intent-routing]] — Intent hint injected into prompt context
