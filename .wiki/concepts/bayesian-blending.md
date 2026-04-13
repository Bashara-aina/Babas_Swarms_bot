---
title: bayesian-blending
type: concept
status: active
tags: [llm, routing, probability, cost-optimization, bayesian, model-selection]
created: 2026-04-13
updated: 2026-04-13
summary: Bayesian blending selects the optimal LLM model for each task by computing expected quality minus cost and latency weighted by task requirements — using probabilistic routing to balance capability against budget constraints.
wikilinks:
  - [[llm-cost-routing]]
  - [[intent-routing]]
  - [[litellm]]
  - [[openrouter]]
  - [[context-window-budget]]
confidence: medium
source: research
---

# Bayesian Blending

## TL;DR
Bayesian blending is a probabilistic model selection framework where the choice of which LLM to use for a given task is modeled as a decision problem: maximize `expected_quality - λ * cost - μ * latency`, where λ and μ are weighting parameters derived from task requirements and current budget state. Unlike hard-routed fallback chains, Bayesian blending computes a soft selection probability across all available models based on predicted task complexity and required quality.

## Overview

Traditional routing uses deterministic fallback chains (try A, if fails try B, if fails try C). This is robust but ignores the reality that different tasks have different quality requirements. A casual "halo" message doesn't need claude-sonnet-4; "analisa architecture decision for this API design" probably does. Bayesian blending computes the optimal model for each task dynamically rather than using a fixed chain.

## Context

Legion runs on a limited budget funded by Bashara out of pocket. Every API call has a cost. The system needs to be intelligent about when to spend premium credits on a capable model versus using a free model for simple tasks. Bayesian blending provides a principled framework for this decision — not just "use this chain" but "given the current budget state, task complexity, and quality requirement, which model maximizes expected utility?"

## Key Properties

- **Probabilistic model**: Selection is `P(use_model | task_features) = f(task_complexity, context_length, domain, budget_state)`
- **Utility maximization**: Model selected maximizes `expected_quality - λ * cost - μ * latency`
- **Task complexity scoring**: Based on message length, presence of technical terms, intent category, estimated tool use needs
- **Budget-aware weighting**: λ (cost weight) increases as daily budget is consumed; μ (latency weight) increases for time-sensitive tasks
- **Soft selection, not hard routing**: Returns probability distribution over models, not a single deterministic choice
- **Can compose with fallback chains**: Output of Bayesian blender can seed litellm's fallback chain selection
- **Intent routing integration**: Intent classification provides task complexity signals to the Bayesian model

## The Mathematical Framework

For a given task with features `x`, the model selection computes:

```
P(model | x) ∝ P(x | model) * P(model)
```

Where:
- `P(model)` — prior probability of using this model (based on cost, availability)
- `P(x | model)` — likelihood of task features given this model (complexity fit)

The expected utility of selecting model m for task x:

```
U(m|x) = quality(m,x) - λ * cost(m) - μ * latency(m)
```

Where λ and μ are Lagrange multipliers for cost and latency constraints given current budget and task urgency.

## Task Complexity Factors

| Factor | Signal | High Complexity Indicator |
|--------|--------|---------------------------|
| Message length | >50 words | Multi-paragraph technical description |
| Technical terms | Code/math/domain jargon | "architecture", "optimization", "decomposition" |
| Intent category | research, code_generation, analysis | Multi-step reasoning required |
| Estimated tool use | Mentions files, APIs, external services | Multiple tool calls needed |
| Context length | >1000 chars in conversation history | Deep prior context required |
| Time sensitivity | Explicit deadline or urgency markers | "urgent", "asap", "before meeting" |

## Cost-Aware Weighting

As the daily budget is consumed, λ (cost weight) increases:

```
λ_effective = λ_base * (1 + budget_consumed_ratio ^ 2)
```

At 0% budget consumed: λ = λ_base (normal cost sensitivity)
At 50% budget consumed: λ = 1.25 * λ_base
At 90% budget consumed: λ = 1.81 * λ_base

This progressively biases selection toward free/cheap models as the budget depletes.

## Relationships

Bayesian blending is an extension of [[llm-cost-routing]] — it replaces the deterministic fallback chain with a probabilistic decision function. The framework requires knowing [[openrouter]] model availability and [[litellm]] cost structures to compute expected utilities. [[intent-routing]] provides the task complexity signals (intent category, estimated tool use) that feed into the Bayesian model's likelihood function. [[context-window-budget]] and Bayesian blending share the theme of efficient resource use — context budget maximizes what fits in the prompt, Bayesian blending maximizes what quality is obtained per yen.

## Current Status

**Research/conceptual.** The probabilistic framework is defined and documented. Actual implementation of Bayesian selection as a runtime decision layer is not yet wired into `llm_client.py`. The fallback chain in [[llm-cost-routing]] currently uses deterministic priority ordering. Implementing Bayesian blending would require: (1) task complexity scoring function, (2) per-model quality/cost/latency estimates, (3) budget-aware λ weight adjustment, (4) integration point in `llm_client.chat()` before fallback chain selection.

## See Also

- [[llm-cost-routing]] — Current deterministic fallback chain implementation
- [[intent-routing]] — Task complexity signals from intent classification
- [[litellm]] — Library whose fallback mechanism could be replaced by Bayesian selection
- [[openrouter]] — Provider with model cost and availability data
- [[context-window-budget]] — Token budget management complementary to cost routing
