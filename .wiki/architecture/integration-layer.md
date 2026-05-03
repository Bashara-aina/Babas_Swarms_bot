---
title: "Integration Layer Architecture"
created: 2026-05-03
tags: [architecture, integration, tools]
wikilinks: []
---

# Integration Layer Architecture

> ⚠️ STUB — Full content pending. Created 2026-05-03 by audit v2.

## Core Integrations

All integrations live in `core/integrations/` and `tools/`.

### Memory
- `SwarmBotMemoryManager` — facade for all memory tiers
- `graphiti_integration.py` — temporal knowledge graph
- `mem0_client.py` — vector semantic storage

### Orchestration
- `langgraph_integration.py` — multi-agent task graphs
- `crewai_integration.py` — crew-based agents
- `prefect_integration.py` — workflow pipelines

### Observability
- Phoenix tracer + OpenTelemetry for LLM tracing
- Token usage tracking

## See Also

- `AGENTS.md` — Key Imports section for full import list
- `.wiki/operations/observability.md` — observability details
