---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/raw/docs/architecture-v5.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-06T01:00:01.058307"
}
---

---
title: Architecture V5
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- docs
created: '2026-04-14'
updated: '2026-04-14'
summary: LEGIONSWARM v5 ARCHITECTURE
wikilinks: []
confidence: medium
source: research
---
# LEGIONSWARM v5 ARCHITECTURE

```text
                         LEGIONSWARM v5 ARCHITECTURE
                         ============================

TELEGRAM USER
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                   (Telegram Bot Entry)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    handlers/                                │
│  /swarm  /do  /run  /owl  /ag2  /code_exec  /predict  ...  │
└────┬──────────┬──────────┬──────────┬────────────┬──────────┘
     │          │          │          │            │
     ▼          ▼          ▼          ▼            ▼
┌─────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│ Swarm   │ │ OWL  │ │  AG2   │ │ Code   │ │  MiroFish    │
│Topologies│ │Agent │ │Pipeline│ │ Exec   │ │  Predictor   │
│(kyegomez│ │(camel│ │(ag2ai/ │ │(smol   │ │ (666ghj/     │
│/swarms) │ │-ai)  │ │ag2)    │ │agents) │ │  MiroFish)   │
└────┬────┘ └──┬───┘ └───┬────┘ └───┬────┘ └──────┬───────┘
     │         │         │          │              │
     └────┬────┴─────────┴──────────┘              │
          │                                        │
          ▼                                        │
┌─────────────────────────┐                       │
│   OpenAI Agents SDK     │◄──────────────────────┘
│  (openai/openai-agents) │   complexity score
│  Handoffs + Guardrails  │   routes task here
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                       router.py                             │
│              LiteLLM Cost Router + Fallback Chain           │
└──┬──────────┬──────────┬──────────┬────────────┬────────────┘
   │          │          │          │            │
   ▼          ▼          ▼          ▼            ▼
Cerebras    Groq       Z.AI      Gemini      OpenRouter
Qwen3-235B  Kimi-K2   GLM-4    2.0-Flash   qwen3-coder
14,400/day  1K/day    ∞/day     1K/day      1K/day
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │ ruflo bridge │
                                          │ (Claude only)│
                                          └─────────────┘
   │
   ▼
┌──────────────────────┐
│   Ollama (local)     │
│   gemma4:e4b         │
│   RTX 3060 12GB      │
│   128K ctx, 6GB VRAM │
│   ZERO rate limits   │
└──────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    core/observability.py                    │
│              AgentOps — Tracks ALL agent calls              │
│       tokens | latency | cost | error rate | daily %        │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                 core/structured_outputs.py                  │
│          Pydantic-AI — Validates ALL agent outputs          │
│       AgentResponse | SwarmResult | TaskPlan | CodeResult   │
└─────────────────────────────────────────────────────────────┘
```
