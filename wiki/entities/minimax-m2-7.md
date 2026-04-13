---
title: minimax-m2-7
type: entity
status: active
tags: [llm, model, provider, multimodal]
created: 2026-04-13
updated: 2026-04-13
summary: MiniMax M2.7 is the primary LLM model used by Legion for vision and generation tasks, accessed via MiniMax API.
wikilinks: [[entities/litellm.md], [concepts/llm-cost-routing.md]]
confidence: high
source: implementation
---

# MiniMax M2.7

## TL;DR
MiniMax M2.7 is Legion's primary vision model for image analysis and generation, accessed via the MiniMax API.

## Capabilities

| Capability | Status |
|------------|--------|
| Text generation | ✅ |
| Vision/Image analysis | ✅ Primary |
| Text-to-Speech | ✅ |
| Image generation | ✅ (via /imagine) |

## API Integration

```python
# Via llm_client.chat("vision", messages)
# Or direct: MiniMax API with API key from .env
```

## Configuration

- Model ID: `MiniMax-v2.7`
- API endpoint: `https://api.minimax.chat`
- Rate limit: Configured per .env

## Related Pages

- [[entities/litellm.md]] — LLM client
- [[concepts/llm-cost-routing.md]] — Cost routing
