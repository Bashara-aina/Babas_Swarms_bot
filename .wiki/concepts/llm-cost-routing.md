---
title: llm-cost-routing
type: concept
status: active
tags: [llm, routing, cost, optimization, litellm, providers]
created: 2026-04-13
updated: 2026-04-13
summary: LLM cost routing uses litellm's unified API to route requests across multiple providers (OpenRouter, Groq, Cerebras, Ollama) with automatic fallback chains, exponential backoff retry, and BudgetManager integration for daily caps.
wikilinks:
  - [[./entities/litellm]]
  - [[./entities/openrouter]]
  - [[./concepts/bayesian-blending]]
  - [[./concepts/context-window-budget]]
  - [[./concepts/intent-routing]]
confidence: high
source: implementation
---

# LLM Cost Routing

## TL;DR
LLM cost routing is Legion's system for directing LLM requests to the most cost-effective available provider among a fallback chain (OpenRouter → Groq → Cerebras → Ollama local). litellm provides a unified API across providers, with exponential backoff retry (1s → 2s → 4s), rate limit tracking, per-provider cooldown, and BudgetManager daily caps checked before every API call. The goal is maximizing capability per yen spent.

## Overview

LLM API costs vary enormously: OpenRouter's claude-sonnet-4 costs $3/$15 per 1M tokens input/output, while Groq's llama-3.3-70b is free and Cerebras' qwen-3-32b is free with unlimited requests. Legion needs to use the best model for each task while staying within daily budget constraints. The routing system handles provider selection, fallback chains, retry logic, and budget enforcement transparently.

## Context

Bashara funds Legion's API usage out of pocket. Every LLM call has a real cost. The system must:
1. Use the cheapest capable model when cost is constrained
2. Escalate to more capable (more expensive) models when the task demands it
3. Never exceed daily/monthly caps
4. Handle rate limits gracefully without user-visible failures
5. Support local Ollama to eliminate costs for appropriate tasks entirely

## Key Properties

- **litellm unified API**: Single interface across OpenRouter, Groq, Cerebras, Ollama, MiniMax, Anthropic — no provider-specific code in call paths
- **Fallback chain**: Requests try providers in order; on RateLimitError or failure, the next provider in chain is tried
- **Provider chain**: OpenRouter (primary) → Groq (free, fast) → Cerebras (free, unlimited) → Ollama (local, zero cost)
- **Exponential backoff**: 1s → 2s → 4s retry delays on transient failures
- **Rate limit tracking**: In-memory `_rate_limited` dict tracks per-model cooldown; 90-second cooldown after RateLimitError
- **BudgetManager integration**: `BudgetManager.can_spend()` checked before every LLM call in `llm_client.chat()`
- **Daily cap enforcement**: Hard stop returns "[Budget cap reached. LLM paused until midnight JST.]" when cap exceeded
- **Model-specific API bases**: Each provider has a configured API base URL in `_call_model()`
- **API key per provider**: Keys stored as env vars (OPENROUTER_API_KEY, GROQ_API_KEY, CEREBRAS_API_KEY, etc.)

## Provider Chain Details

| Provider | Model | Cost/1M tokens | Daily limit | Rate limit behavior |
|----------|-------|----------------|------------|---------------------|
| OpenRouter | claude-sonnet-4 | $3/$15 | 1000/day | Falls back on 429 |
| Groq | llama-3.3-70b | $0 | 10000/day | Free, fast fallback |
| Cerebras | qwen-3-32b | $0 | unlimited | Free, unlimited |
| Ollama | gemma3:12b | $0 | unlimited (local) | Zero cost, local GPU |

## Cost Comparison (approximate, 2026-04)

| Model | Input cost | Output cost | Context |
|-------|-----------|-------------|---------|
| claude-sonnet-4 (OpenRouter) | $3/M | $15/M | 200K |
| llama-3.3-70b (Groq) | $0 | $0 | 128K |
| qwen-3-32b (Cerebras) | $0 | $0 | 32K |
| gemma3:12b (Ollama) | $0 | $0 | 128K (local) |

## How It Works

### Budget Check (Gate)
Before every `call_llm()` or `chat()` invocation, `BudgetManager.can_spend(task_type)` is consulted. If the daily cap is exceeded, the call returns a budget-exceeded message instead of making an API request.

### Fallback Chain Resolution
`get_fallback_chain(agent_key)` returns the provider list for a given agent type. The chain is tried in order, skipping any provider in `_rate_limited` cooldown state.

### Retry Logic
On `RateLimitError`, `APIConnectionError`, or `TimeoutError`, the system retries with exponential backoff (1s, 2s, 4s). After 3 attempts on one model, it breaks to try the next model in the chain.

### Rate Limit Tracking
When a `RateLimitError` occurs, the model is marked in `_rate_limited` with timestamp. For 90 seconds, calls to that model are skipped. `_provider_remaining_cooldown()` checks all models of a provider and returns the max remaining seconds.

### BudgetManager Integration Points
- `llm_client.py` `call_llm()` — BudgetManager check before API call
- `daily_briefing.py` — BudgetManager check before generating briefing
- `composio_hub.py` — BudgetManager check before composio tool calls
- `llm_client.chat()` — hard stop if daily cap exceeded

## Relationships

LLM cost routing directly enables [[./concepts/bayesian-blending]]: the probabilistic model selection calculus requires knowing which models are available, their cost structure, and current rate limit states. [[./concepts/context-window-budget]] and cost routing share the goal of efficient resource use — context window budget maximizes what fits in a prompt, cost routing maximizes what model quality is obtained per yen. [[./concepts/intent-routing]] feeds into routing by determining which agent key is used, which maps to a specific fallback chain (e.g., "coding" → higher capability models, "general" → cheaper models). [[./entities/litellm]] is the library that powers the unified API.

## Current Status

**Implemented.** litellm is the LLM interface throughout the codebase. Provider fallback chains are defined. Exponential backoff retry is implemented. Rate limit tracking with 90-second cooldown is functional. BudgetManager integration is wired at key call sites. Ollama local fallback is configured for appropriate tasks.

## See Also

- [[./entities/litellm]] — Library powering the unified API
- [[./entities/openrouter]] — Primary provider with best model availability
- [[./concepts/bayesian-blending]] — Probabilistic model selection based on task complexity
- [[./concepts/context-window-budget]] — Token budgeting that complements cost routing
