---
title: llm-cost-routing
type: concept
status: active
tags: [llm, routing, cost, optimization, litellm]
created: 2026-04-13
updated: 2026-04-13
summary: LLM cost routing uses litellm to route requests across providers based on cost, latency, and capability requirements.
wikilinks: [[entities/litellm.md], [entities/openrouter.md], [concepts/bayesian-blending.md]]
confidence: high
source: implementation
---

# LLM Cost Routing

## TL;DR
LLM cost routing uses litellm's unified interface to route requests across multiple LLM providers, automatically falling back when rates are exceeded.

## Provider Chain

```
Primary: OpenRouter → Fallback1: Groq → Fallback2: Cerebras → Local: Ollama
```

## Cost Comparison

| Provider | Model | Cost/1K tokens | Rate Limit |
|----------|-------|----------------|------------|
| OpenRouter | claude-sonnet-4 | $3/$15 | 1000/day |
| Groq | llama-3.3-70b | $0 | 10000/day |
| Cerebras | qwen-3-32b | $0 | unlimited |
| Ollama | gemma3:12b | $0 | unlimited (local) |

## BudgetManager Integration

Every LLM call checks:
1. `BudgetManager.can_spend(task_type)` before API call
2. Daily/monthly caps tracked
3. Graceful fallback when exhausted

## Implementation

In `llm_client.py`:
- `chat(model_type, messages)` unified entry point
- Automatic retry with exponential backoff
- Model fallback chain

## Related Pages

- [[entities/litellm.md]] — LLM routing library
- [[concepts/bayesian-blending.md]] — Advanced routing
