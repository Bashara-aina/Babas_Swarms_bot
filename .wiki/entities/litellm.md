---
title: LiteLLM
type: entity
status: active
tags: [llm, routing, client, proxy]
created: 2026-04-13
updated: 2026-04-13
summary: LiteLLM is the unified LLM client used by Legion to call OpenRouter, Groq, Cerebras, and local Ollama models through a single interface, with automatic retries, fallbacks, and cost tracking.
wikilinks:
  - [[./entities/openrouter]]
  - [[./concepts/llm-cost-routing]]
  - [[memory-architecture]]
confidence: high
source: implementation
project: legion
---

# LiteLLM

## TL;DR
LiteLLM is the unified LLM client used by Legion to call OpenRouter, Groq, Cerebras, and local Ollama models through a single interface, with automatic retries, fallbacks, and cost tracking. Every `chat()` call in Legion goes through `llm_client.chat()` which dispatches via litellm's `acompletion()`.

## Fallback Chain
All LLM calls use `get_fallback_chain(agent_key)` from `core/conversation_interface.py`. The chain for most agents:

```
groq/llama-3.3-70b-versatile → cerebras/qwen3-235b-a22b → ollama_chat/llama3.3:70b
```

For `architect` and `pm` agents (long context):
```
cerebras/qwen3-235b-a22b → groq/moonshotai/kimi-k2-instruct
```

For `debug` and `math` agents:
```
zai/glm-4 → groq/llama-3.3-70b-versatile
```

## Budget Enforcement
All background tasks check `BudgetManager.can_spend(task_name)` before making any API call. Budget is enforced in `llm_client/__init__.py` — if budget is exceeded, the task skips the LLM call and logs a warning.

## Retry Logic
- Rate limit errors: 3 retries with exponential backoff (2s, 4s, 8s)
- Connection errors: 3 retries
- Timeout per call: 30 seconds

## Key Functions

### `chat(agent_key, messages)` — Primary entry point
```python
# From llm_client/__init__.py
from llm_client import chat
response = await chat("default", messages)
```
All handlers use this. Never call litellm directly.

### `call_llm(model, messages, **kwargs)` — Low-level
```python
from llm_client import call_llm
response = await call_llm(
    model="groq/llama-3.3-70b-versatile",
    messages=messages,
    temperature=0.7,
    max_tokens=8192
)
```

### `chunk_output(text, max_chars=4000)` — Telegram safety
All responses longer than 4000 chars are chunked before sending to Telegram.

## Model Routing
Model routing is defined in `config/models.yaml` and `agents.py` TASK_KEYWORDS dict. Each agent key maps to a primary model and fallback chain.

## Failure Modes
- `litellm.RateLimitError`: Handled by fallback chain + 60s cooldown
- `TimeoutError`: Retried once, then error surfaced to user
- Provider returns XML instead of JSON (Groq quirk): `_parse_groq_xml_tool_call()` in `llm_client.py` recovers

## See Also
[[./entities/openrouter]] — Primary provider, unified gateway for 100+ models
[[./concepts/llm-cost-routing]] — How model selection is optimized for cost
[[memory-architecture]] — Memory system uses litellm for semantic embeddings
