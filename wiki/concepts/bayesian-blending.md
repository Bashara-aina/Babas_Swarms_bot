---
title: bayesian-blending
type: concept
status: active
tags: [llm, routing, probability, cost-optimization]
created: 2026-04-13
updated: 2026-04-13
summary: Bayesian blending selects the optimal LLM model based on task complexity, cost, and confidence requirements using probabilistic routing.
wikilinks: [[concepts/llm-cost-routing.md]], [[entities/litellm.md]], [[entities/openrouter.md]]
confidence: medium
source: research
---

# Bayesian Blending

## TL;DR
Bayesian blending routes requests to different LLMs based on predicted complexity and required quality, balancing cost against capability needs.

## Model Selection Factors

| Factor | Impact |
|--------|--------|
| Task complexity | High → Sonnet, Low → Haiku |
| Latency requirement | High → Groq, Normal → OpenRouter |
| Cost budget | Low budget → prefer cheaper models |
| Quality requirement | Research → best available |

## Probability-Based Routing

```
P(use_model | task_features) = f(task_complexity, context_length, domain)
```

Model selected maximizes:
```
expected_quality - λ * cost - μ * latency
```

## Implementation

In `llm_client.py`:
- Task classification via intent router
- Complexity scoring based on message length, special tokens
- Budget constraints from `BudgetManager`

## Related Pages

- [[concepts/llm-cost-routing.md]] — Cost-aware routing
- [[entities/litellm.md]] — LLM client library
- [[entities/openrouter.md]] — Router provider
