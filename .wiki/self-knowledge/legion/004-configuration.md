---
title: Configuration
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- self-knowledge
created: '2026-04-14'
updated: '2026-04-14'
summary: '| Provider | Base URL | API Key Env | Daily Limit |'
wikilinks: []
confidence: medium
source: research
---

# SwarmBot Configuration: Models, Costs, Rate Limits

## From `config/models.yaml`

### Provider Configuration

| Provider | Base URL | API Key Env | Daily Limit |
|----------|----------|-------------|-------------|
| openrouter | https://openrouter.ai/api/v1 | OPENROUTER_API_KEY | 1000 |
| cerebras | https://api.cerebras.ai/v1 | CEREBRAS_API_KEY | 14400 |
| zai | https://open.bigmodel.cn/api/paas/v4 | ZAI_API_KEY | unlimited |
| groq | https://api.groq.com/openai/v1 | GROQ_API_KEY | 1000 |
| gemini | https://generativelanguage.googleapis.com/v1beta | GEMINI_API_KEY | 1000 |
| minimax | https://api.minimax.io/v1 | MINIMAX_API_KEY | unlimited |
| anthropic | https://api.minimax.io/anthropic | ANTHROPIC_API_KEY | unlimited |
| ollama | http://localhost:11434 | (none - local) | unlimited |

### Model Registry

| Model Key | Provider | Context Window | Strengths |
|-----------|----------|----------------|-----------|
| devstral | openrouter | 131072 | coding, multi-file, swe-bench |
| qwen3-235b | cerebras | 131072 | reasoning, speed, general |
| glm-4 | zai | 128000 | debug, math, reasoning |
| kimi-k2 | groq | 200000 | deep-reasoning, analysis, long-context |
| gemini-3.1-pro | gemini | 1000000 | teaching, general, long-context |
| gemma4-local | ollama | 131072 | vision, local, privacy, function-calling |
| llama3-70b | ollama | 32768 | general, local, fallback |
| minimax-m2-7 | minimax | 16384 | coding, reasoning, conversation, general |
| anthropic-claude | anthropic | 200000 | reasoning, coding, analysis |

### Complexity Tier Provider Order

**Lightweight:**
1. minimax
2. cerebras
3. groq
4. ollama

**Midweight:**
1. minimax
2. zai
3. gemini
4. cerebras
5. groq

**Heavyweight:**
1. minimax
2. openrouter
3. gemini
4. zai
5. cerebras
6. ollama

## From `config/departments.yaml`

### Agent Model Assignments (sample)

| Agent | Department | Primary Model | Fallbacks |
|-------|------------|---------------|-----------|
| senior_python_dev | engineering | minimax-m2-7 | qwen3-235b, llama3-70b |
| frontend_react_dev | engineering | qwen3-235b | devstral, llama3-70b |
| backend_fastapi_dev | engineering | glm-4 | qwen3-235b, devstral |
| rust_systems_dev | engineering | kimi-k2 | devstral, llama3-70b |
| smart_contract_auditor | engineering | gemini-3.1-pro | glm-4, qwen3-235b |
| security_pentester | engineering | devstral | gemini-3.1-pro, glm-4 |
| cuda_optimizer | engineering | glm-4 | qwen3-235b, kimi-k2 |
| debugging_specialist | engineering | glm-4 | qwen3-235b, devstral |

### 9 Departments
1. engineering — 12 agents
2. design — UI/UX, creative
3. research — Web scraping, papers
4. marketing — Content, social
5. operations — Devops, deployment
6. product — Planning, roadmap
7. legal_compliance — Policy, compliance
8. creative — Writing, brainstorming
9. vision_multimodal — Image, OCR

## Rate Limit Thresholds
- Default warning threshold: 80% of daily limit
- Business alert threshold: 5 errors
- Proactive interval: 30 minutes
- Daily briefing: 8 AM local

## Cost Strategy
- All listed models cost $0.0 per 1M tokens (free tier)
- MiniMax is the only paid model
- RTX 3060 handles local vision (gemma4:e4b, 6GB VRAM)

---
*Extracted: 2026-04-11 by @worker*
