---
title: OpenRouter
type: entity
status: active
tags: [llm, routing, provider, api]
created: 2026-04-13
updated: 2026-04-13
summary: OpenRouter is Legion's primary LLM gateway providing unified access to 100+ models via a single API at https://openrouter.ai/api/v1, with $0 cost for specified free-tier models.
wikilinks:
  - [[./entities/litellm]]
  - [[./concepts/llm-cost-routing]]
  - [[./entities/opencode]]
confidence: high
source: implementation
project: legion
---

# OpenRouter

## TL;DR
OpenRouter is Legion's primary LLM gateway, providing unified API access to Claude, GPT, Gemini, and 100+ other models through `https://openrouter.ai/api/v1`. Key advantage: free-tier models (devstral, gemini-2.0-flash) with no cost for development use.

## Provider Config (config/models.yaml)
```yaml
providers:
  openrouter:
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
    daily_limit: 1000          # requests per day
    daily_limit_warning: 0.8   # alert at 80% capacity
```

## Key Free-Tier Models
| Model | Model ID | Context | Cost | Best For |
|-------|---------|---------|------|----------|
| devstral | `openrouter/qwen/qwen3-coder:free` | 131K | $0 | Code generation |
| gemini-2.0-flash | `gemini/gemini-2.0-flash` | 1M | $0 | Fast teaching, bulk tasks |

## Rate Limits
- Default: 1000 requests/day across all models
- Per-model limits vary by provider underlying the route
- When exceeded: `litellm.RateLimitError` → fallback to Groq/Cerebras
- Warning threshold: 80% daily capacity

## Integration via LiteLLM
```python
# Via litellm — standard call
response = await litellm.acompletion(
    model="openrouter/anthropic/claude-sonnet-4-5",
    messages=messages,
    api_key=os.getenv("OPENROUTER_API_KEY")
)
```
Legion never calls OpenRouter directly — all calls go through `llm_client.chat()` which uses litellm as the abstraction layer.

## Compared to Direct Provider APIs
- OpenRouter adds ~50-100ms latency per request (proxy overhead)
- Benefit: single API key for 100+ models, unified billing
- For high-volume tasks (debug, math), Cerebras/Groq are faster and cheaper

## See Also
[[./entities/litellm]] — LLM client that wraps OpenRouter calls
[[./concepts/llm-cost-routing]] — Model selection strategy including OpenRouter free tiers
[[./entities/opencode]] — Code agent using OpenRouter devstral for free coding tasks
