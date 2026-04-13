---
title: openrouter
type: entity
status: active
tags: [llm, routing, provider, api]
created: 2026-04-13
updated: 2026-04-13
summary: OpenRouter is a unified LLM API gateway that provides access to 100+ models with consistent pricing and rate limiting.
wikilinks:
  - [[litellm]]
  - [[llm-cost-routing]]
confidence: high
source: implementation
---

# OpenRouter

## TL;DR
OpenRouter is Legion's primary LLM gateway, providing unified access to Claude, GPT, Gemini, and other models through a single API.

## Key Models Available

| Model | Context | Cost | Best For |
|-------|---------|------|----------|
| claude-sonnet-4-5 | 200K | $3/$15 | Complex reasoning |
| gpt-4o | 128K | $5/$15 | General purpose |
| gemini-2.0-flash | 1M | Free | Fast tasks |

## Integration

```python
# Via litellm
response = litellm.completion(
    model="openrouter/anthropic/claude-sonnet-4-5",
    messages=messages
)
```

## Rate Limits

- Default: 1000 requests/day
- Per-model limits vary
- Automatic fallback to Groq/Cerebras when exceeded

## Related Pages

- [[litellm]] — LLM client using OpenRouter
- [[llm-cost-routing]] — Routing strategy
