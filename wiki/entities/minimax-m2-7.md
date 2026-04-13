---
title: minimax-m2-7
type: entity
status: active
tags: [llm, model, provider, multimodal, coding]
created: 2026-04-13
updated: 2026-04-13
summary: MiniMax M2.7 is Legion's primary LLM model for coding and reasoning tasks, offering 100 TPS throughput and achieving 56% on SWE-Pro benchmarks at $0.30 input/$1.20 output per million tokens.
wikilinks: [[entities/litellm.md], [entities/openrouter.md], [concepts/llm-cost-routing.md]]
confidence: high
source: implementation
---

# MiniMax M2.7

## TL;DR
MiniMax M2.7 is Legion's primary coding and reasoning model, delivering 100 tokens per second throughput with competitive pricing at $0.30 per million input tokens and $1.20 per million output tokens. The model achieves 56% on the SWE-Pro benchmark, making it suitable for production coding tasks.

## Performance Specifications

| Metric | Value | Notes |
|--------|-------|-------|
| Throughput | 100 TPS | Tokens per second |
| SWE-Pro Benchmark | 56% | Software engineering professional benchmark |
| Input Cost | $0.30 / 1M tokens | Competitive with Groq free tier |
| Output Cost | $1.20 / 1M tokens | Moderate for extended generation |
| Context Window | 16,384 tokens | Standard for coding tasks |
| Max Tokens | 16,384 | Matches context window |

## Model Configuration

```yaml
# From config/models.yaml
minimax-m2-7:
  provider: minimax
  model_id: "minimax-coding-plan/MiniMax-M2.7"
  context_window: 16384
  max_tokens: 16384
  temperature_conversation: 0.7
  temperature_code: 0.1
  strengths: [coding, reasoning, conversation, general]
```

## Capabilities

| Capability | Status | Quality |
|------------|--------|---------|
| Text generation | ✅ | High |
| Vision/Image analysis | ✅ | High (MiniMax multimodal) |
| Text-to-Speech | ✅ | Via Kokoro-ONNX |
| Image generation | ✅ | Via /imagine command |
| Coding tasks | ✅ | Primary use case |
| Reasoning | ✅ | Strong |
| Function calling | ✅ | Supported |

## Legion Integration

Legion uses MiniMax M2.7 as the primary model for most tasks:

```python
# Via llm_client.chat() with model selection
response = await chat("general", messages)  # Uses minimax-m2-7 by default

# Direct model specification
response = await chat(model="minimax-m2-7", messages=messages)
```

### Routing Context

From `config/models.yaml`, the complexity tier routing places MiniMax M2.7 in both `lightweight` and `midweight` tiers, giving it broad applicability:

```yaml
complexity_tiers:
  lightweight:
    - minimax      # Primary
    - cerebras
    - groq
    - ollama
  midweight:
    - minimax      # Primary
    - zai
    - gemini
    - cerebras
```

## Comparison with Alternatives

| Model | Provider | Cost | Strengths |
|-------|----------|------|-----------|
| minimax-m2-7 | MiniMax | $0.30/$1.20 | Coding, 100 TPS |
| qwen3-235b | Cerebras | Free | Reasoning, speed |
| kimi-k2 | Groq | Free | Deep reasoning, 200K context |
| llama3-70b | Ollama | Free | Local, privacy |

## API Integration

```python
# Via litellm (configured in llm_client/)
# Environment: MINIMAX_API_KEY in .env
# Endpoint: https://api.minimax.io/v1

from llm_client import chat
result = await chat("coding", [{"role": "user", "content": "Write a FastAPI endpoint"}])
```

## Related Pages

- [[entities/litellm.md]] — LiteLLM client that routes to MiniMax
- [[entities/openrouter.md]] — Alternative routing provider
- [[concepts/llm-cost-routing.md]] — Cost optimization strategy
