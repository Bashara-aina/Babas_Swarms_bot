---
title: Cross Repo Patterns
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
summary: This document captures shared patterns and conventions found across the SwarmBot
  ecosystem.
wikilinks: []
confidence: medium
source: research
---

# Cross-Repository Patterns

## Overview
This document captures shared patterns and conventions found across the SwarmBot ecosystem.

---

## Environment Variable Patterns

### Supabase Pattern
```python
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
```
Found in:
- `tools/business_ops.py`
- `tools/rumahlabuh_crew.py`
- `core/proactive/scheduler.py`

### API Key Pattern
```python
api_key = os.getenv("PROVIDER_API_KEY", "")
```
Found in 20+ tools ( Tavily, Google Places, OpenWeather, SerpAPI, Firecrawl, etc.)

### Feature Flag Pattern
```python
if os.getenv("FEATURE_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
    # enable feature
```
Examples:
- `LEGION_WIKI_AUTO_INGEST=1` — Wiki auto-ingest
- `LEGION_WIKI_ENABLED=1` — Wiki system
- `SCREENPIPE_ENABLED=0` — Activity monitoring
- `LEGION_UNIFIED_CONTEXT_ENABLED=1` — Context aggregation

### User ID Pattern
```python
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
```
Used for single-user access control across handlers.

---

## Authentication Approaches

### Telegram Bot
- `TELEGRAM_BOT_TOKEN` — Bot token from @BotFather

### LLM Providers (litellm)
- `OPENROUTER_API_KEY`
- `MINIMAX_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `CEREBRAS_API_KEY`
- `ZAI_API_KEY`

### Database
- Supabase: `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` or `SUPABASE_ANON_KEY`

### External Services
- `GITHUB_TOKEN` — GitHub API
- `AGENTOPS_API_KEY` — AgentOps monitoring
- `VERCEL_TOKEN` — Vercel deployments

---

## Error Handling Patterns

### Specific Try/Except
```python
try:
    result = await some_async_call()
except SpecificException as exc:
    logger.warning(f"Failed: {exc}")
    return fallback_value
```

### Never Bare Except
```python
# CORRECT
try:
    ...
except ValueError as exc:
    ...

# INCORRECT (not found in codebase)
try:
    ...
except:
    ...
```

---

## Async Patterns

### All I/O Async
```python
async def function():
    await asyncio.sleep()  # CORRECT
    # NOT time.sleep()  # WRONG - blocking
```

### asyncio.run for Tests
```python
# CORRECT in tests
asyncio.run(coroutine())

# INCORRECT (found in old tests, now fixed)
# Using pytest-asyncio mode: auto
```

---

## Configuration Patterns

### YAML-Based Config
- `config/models.yaml` — Model registry
- `config/departments.yaml` — Agent definitions (76+ agents)
- `config/routing_keywords.yaml` — Intent routing keywords
- `config/personality.yaml` — Personality wrapper, debate personas

### Constants as Environment Variables
```python
PROACTIVE_INTERVAL_MINUTES = int(os.getenv("PROACTIVE_INTERVAL_MINUTES", "30"))
DAILY_BRIEFING_HOUR = int(os.getenv("DAILY_BRIEFING_HOUR", "8"))
BUSINESS_ALERT_THRESHOLD = int(os.getenv("BUSINESS_ALERT_THRESHOLD", "5"))
```

---

## Common Tech Stack

| Layer | Technology |
|-------|------------|
| Bot Framework | aiogram 3.4+ |
| LLM Routing | litellm 1.57+ |
| Database | Supabase |
| Local Vision | Ollama + gemma4:e4b |
| RAG | RAGFlow, ChromaDB |
| Activity | Screenpipe |
| Multi-agent | CrewAI |

---

## Shared Directory Structure
```
swarm-bot/
├── agents/          # Agent registry
├── core/            # Orchestration, routing, memory
├── handlers/        # Telegram command handlers
├── tools/           # Tool modules
├── config/          # YAML configs
├── swarms_bot/      # Enterprise layer
├── .wiki/           # Knowledge base
└── tests/           # pytest-asyncio
```

---

## Domain References
- **cekwajar.id**: Payroll tax calculator (source not found)
- **rumahlabuh.com**: Villa booking system (Supabase + CrewAI)
- **Thesis**: Academic research (context in wisdom/ domains)

---
*Extracted: 2026-04-11 by @worker*
