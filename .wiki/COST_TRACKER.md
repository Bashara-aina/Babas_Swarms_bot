---
title: COST TRACKER
type: reference
status: active
tags: [cost, llm, routing, budget, tracking]
created: 2026-04-21
updated: 2026-04-21
summary: LLM cost tracking across all providers and surfaces — budget allocation and usage patterns
confidence: high
source: implementation
project: legion
---

# COST TRACKER — LLM Budget Management

> Tracks token usage and cost across MiniMax, OpenRouter, Groq, Cerebras, and Ollama.

## Provider Configuration

### MiniMax (Primary)
- **Base URL**: `https://api.minimax.chat/v1`
- **Model**: `MiniMax-Text-01` (reasoning), `MiniMax-M2.7` (coding)
- **Pricing**: Check `https://api.minimax.io/pricing` for current rates
- **Routing priority**: HIGH (100 TPS throughput, 100K context)

### OpenRouter (Fallback)
- **Base URL**: `https://openrouter.ai/api/v1`
- **Models**: 100+ available via unified API
- **Routing priority**: MEDIUM (fallback when MiniMax unavailable)

### Groq (Fast fallback)
- **Base URL**: `https://api.groq.com/openai/v1`
- **Models**: `llama-3.3-70b`, `qwen-qwq-32b`
- **Routing priority**: LOW (ultra-fast but rate-limited)

### Cerebras (Fast inference)
- **Base URL**: `https://api.cerebras.ai/v1`
- **Models**: `llama-3.3-70b`
- **Routing priority**: LOW

### Ollama (Local)
- **Endpoint**: `http://localhost:11434/api`
- **Models**: `gemma3:12b`, `qwen3.5:35b`, `exaone-deep:32b`, `phi4`, `llama3.3:70b`
- **Routing priority**: LOW (local, no API cost)

## Cost Routing Strategy

### Tier 1: Local Ollama
- Simple queries, drafts, brainstorming
- Zero API cost

### Tier 2: MiniMax M2.7
- Coding, complex reasoning, code review
- $0.001/1K tokens (verify current rate)

### Tier 3: OpenRouter (Premium models)
- Tasks requiring specific models (Claude, GPT-4, Gemini)
- Pay-per-model pricing

## Budget Alerts

| Threshold | Action |
|-----------|--------|
| 50% daily budget | Log warning |
| 80% daily budget | Alert via Telegram |
| 100% daily budget | Switch to Ollama-only mode |

## Usage Tracking

```python
# Track cost per session
from llm_client import LLMClient
client = LLMClient()
session_cost = client.get_session_cost()
print(f"Session cost: ${session_cost:.4f}")
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `MINIMAX_API_KEY` | MiniMax API authentication |
| `OPENROUTER_API_KEY` | OpenRouter fallback |
| `GROQ_API_KEY` | Groq fallback |
| `CEREBRAS_API_KEY` | Cerebras fallback |
| `OLLAMA_BASE_URL` | Local Ollama endpoint |
| `ROUTING_MODEL` | Default routing model |

## Known Cost Issues (from audit 2026-04-14)

### Budget Bypass
- **Issue**: 88% budget bypass rate (partially fixed)
- **Root cause**: Budget limits not enforced in `llm_client.py`
- **Fix**: Add hard budget limits with Ollama fallback

### Token Counting
- **Issue**: Inaccurate token tracking in MiniMax client
- **Fix**: Use `tiktoken` for accurate counting before API calls

## TODO: Integration
- [ ] Wire `get_session_cost()` to Telegram admin handler
- [ ] Add daily/weekly/monthly cost reports to `.wiki/`
- [ ] Implement budget alerts in `core/budget_guard.py`
