---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/llm-routing-map.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.036746"
}
---

---
title: LLM Routing Map
domain: llm-routing
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 700
---

# LLM ROUTING MAP

## ONE-LINE SUMMARY
22 legacy agents with explicit model assignments; MiniMax-M2.7 is the universal fallback (not primary), local Ollama gemma4:e4b for vision/computer only.

## PRIMARY MODELS PER AGENT (from agent_registry.py _LEGACY_AGENT_MODELS)
| Agent | Primary Model | Type |
|-------|---------------|------|
| vision | ollama_chat/gemma4:e4b | local vision (9.6GB VRAM) |
| coding | groq/llama-3.3-70b-versatile | cloud text |
| debug | zai/glm-4 | cloud CoT |
| math | zai/glm-4 | cloud CoT |
| architect | cerebras/qwen3-235b-a22b | cloud reasoning |
| analyst | groq/moonshotai/kimi-k2-instruct | cloud analysis |
| computer | groq/llama-3.3-70b-versatile | cloud text |
| **general** | **ollama_chat/gemma4:e4b** | **local vision (CRITICAL: not a text model!)** |
| researcher | groq/moonshotai/kimi-k2-instruct | cloud research |
| marketer | groq/llama-3.3-70b-versatile | cloud text |
| devops | groq/llama-3.3-70b-versatile | cloud text |
| pm | cerebras/qwen3-235b-a22b | cloud reasoning |
| humanizer | groq/llama-3.3-70b-versatile | cloud text |
| reviewer | groq/llama-3.3-70b-versatile | cloud text |
| think | cerebras/qwen-3-32b | cloud reasoning |
| owl | groq/moonshotai/kimi-k2-instruct | cloud research |
| ag2_researcher | groq/moonshotai/kimi-k2-instruct | cloud research |
| ag2_critic | zai/glm-4 | cloud CoT |
| ag2_synthesizer | cerebras/qwen3-235b-a22b | cloud reasoning |
| code_exec | openrouter/qwen/qwen3-coder:free | free cloud |
| predictor | cerebras/qwen3-235b-a22b | cloud reasoning |
| claude_orchestrator | openrouter/anthropic/claude-opus-4 | premium |
| debate | cerebras/qwen3-235b-a22b | cloud reasoning |

## CRITICAL CORRECTION
**"general" agent is NOT MiniMax M2.7.** The primary model for "general" is `ollama_chat/gemma4:e4b` (local vision model). MiniMax-M2.7 is the **fallback**, not the primary.

This is intentional: `ollama_chat/gemma4:e4b` runs locally on RTX 3060 VRAM with no API cost. MiniMax-M2.7 is the first fallback in the chain when the local model is unavailable.

## FALLBACK CHAIN STRATEGY
Every agent follows this strategy (from LEGACY_FALLBACK_CHAIN):
1. **Primary** — agent's dedicated model (see table above)
2. **Fallback 1** — `minimax/MiniMax-M2.7` (universal fallback)
3. **Fallback 2** — `gemini/gemini-2.0-flash-exp:free` (free tier)
4. **Fallback 3** — `groq/llama-3.3-70b-versatile` (free tier)
5. **Fallback 4** — varies by agent (openrouter/deepseek-r1:free, openrouter/qwen3-coder:free, etc.)

Exception: `vision` and `computer` agents use `ollama_chat/gemma4:e4b` as primary (local screen reading), with MiniMax-M2.7 as first fallback since MiniMax cannot process images.

## COST ESTIMATES
| Model | Cost per 1M tokens | Notes |
|-------|-------------------|-------|
| ollama_chat/gemma4:e4b | ~GPU memory only | Local, no API cost |
| groq/llama-3.3-70b | ~$0 (free tier), then $0.20 | Free tier available |
| groq/moonshotai/kimi-k2 | ~$0 (free tier) | Free tier available |
| gemini/gemini-2.0-flash-exp | ~$0 (free tier) | Free tier available |
| openrouter/qwen/qwen3-coder | ~$0 (free tier) | Free tier available |
| openrouter/deepseek/deepseek-r1 | ~$0 (free tier) | Free tier available |
| cerebras/qwen3-235b | ~$0.60 | Pay-per-token, expensive |
| cerebras/qwen-3-32b | ~$0.60 | Pay-per-token, expensive |
| zai/glm-4 | check zai.ai | Cloud CoT model |
| minimax/MiniMax-M2.7 | check minimax.ai | Primary cloud fallback |
| openrouter/anthropic/claude-opus-4 | premium | Most expensive option |

## ROUTING LOGIC
1. Task keywords → `detect_agent()` — keyword-based agent detection
2. Agent key → `get_model()` — returns primary model from `_LEGACY_AGENT_MODELS`
3. Fallback chain → `get_fallback_chain()` — returns full chain from `LEGACY_FALLBACK_CHAIN`
4. Budget check → `llm_client.chat()` — verifies budget before any LLM call
5. On failure → try next model in fallback chain

## TASK EXAMPLES
| Task | Agent | Primary Model | Fallback Chain |
|------|-------|---------------|----------------|
| "write me code" | coding | groq/llama-3.3-70b | minimax → gemini → groq |
| "debug this error" | debug | zai/glm-4 | minimax → gemini → groq → deepseek-r1 |
| "analyze this data" | analyst | groq/moonshotai/kimi-k2 | minimax → gemini → groq |
| "what's your opinion" | debate | cerebras/qwen3-235b | minimax → gemini → groq |
| "describe this image" | vision | ollama_chat/gemma4:e4b | minimax |

## HARDWARE CONSTRAINTS
RTX 3060 (12GB VRAM) can run:
- `ollama_chat/gemma4:e4b` (9.6GB VRAM) — vision/computer only
- Cannot run llama3.3:70b or qwen3.5:35b — too much VRAM

## ANTI-PATTERNS
- Calling ollama for text tasks (only use for vision/computer screen reading)
- Using cerebras for simple tasks (expensive, pay-per-token)
- Skipping budget check before LLM calls
- Hardcoding a single model without fallback chain
