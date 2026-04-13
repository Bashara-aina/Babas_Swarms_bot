---
title: litellm
type: entity
status: active
tags: [llm, routing, client, proxy]
created: 2026-04-13
updated: 2026-04-13
summary: LiteLLM is the LLM client library providing unified interface to 100+ models with automatic retries, fallbacks, and cost tracking.
wikilinks:
  - [[openrouter]]
  - [[llm-cost-routing]]
confidence: high
source: implementation
---

# LiteLLM

## TL;DR
LiteLLM is the unified LLM client used by Legion to call OpenRouter, Groq, Cerebras, and local Ollama models through a single interface.

## Key Features

| Feature | Implementation |
|---------|---------------|
| Unified API | `litellm.completion()` |
| Automatic retries | 3 retries with exponential backoff |
| Fallback chain | OpenRouter → Groq → Cerebras → Ollama |
| Cost tracking | Via `BudgetManager` |

## Usage in Legion

```python
from llm_client import chat

# Simple call
response = await chat("default", messages)

# With specific model
response = await chat("researcher", messages)
```

## Configuration

In `llm_client.py`:
- Model routing per task type
- Timeout: 30 seconds
- Retry on: RateLimitError, APIConnectionError

## Related Pages

- [[openrouter]] — Primary provider
- [[llm-cost-routing]] — Routing logic
