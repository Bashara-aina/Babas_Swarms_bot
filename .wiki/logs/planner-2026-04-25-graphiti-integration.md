---
title: Planner 2026 04 25 Graphiti Integration
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: Graphiti Integration — Temporal Knowledge Graph Memory Layer
Date: 2026-04-25
Type: FEATURE
Context gathered:
- docker-compose.yml: existing services (redis, chromadb, n8n, livekit, screenpipe, jaeger) with healthcheck patterns
- requirements.txt: graphiti-core==0.28.2 already present (v7 dependency); neo4j driver missing
- .env: no Neo4j vars; existing pattern uses UPPER_SNAKE for all service configs
- main.py: async startup pattern with `_run_group_a_startup()` parallel gather + individual try/except; shutdown uses `on_shutdown()` with step numbering
- memory_engine.py: async MemoryEngine with @asynccontextmanager for SQLite; lazy singleton `_engine_instance`
- long_term_memory.py: async semantic search with graceful degradation; `LongTermMemory` class with `.search()` and `.store()`
- joint_memory.py: async `joint_save()` / `joint_search()` using asyncio.Lock + JSON files
- legion_memory_facade.py: async `LegionMemoryFacade` with `contextual_snapshot()` method; lazy singleton
- episodic_narrative.py: sync `build_narrative_context()` and `update_narrative_from_conversation()` using JSON file
- autonomous_router.py: class `AutonomousRouter` with `analyze_async()` — keyword + LLM fallback; no async memory calls
- intent_router.py: class `IntentRouter` with `route()` → async `classify_intent()`; no memory calls
- mcp_client.py: async `MCPClient` with `call_tool()`, `list_tools()`; stdio MCP pattern
- task_orchestrator.py: async chain execution + SwarmDebateOrchestrator; no memory persistence

Key patterns confirmed:
- ALL existing memory modules use @asynccontextmanager for SQLite, asyncio.Lock for concurrent writes
- Graceful degradation via try/except with fallback returns already established
- No graphiti or neo4j in codebase yet
- graphiti-core already in requirements.txt (v0.28.2) — only need to add neo4j driver
- GROUP_ID = "babas_swarms" for all agents (from constraints)
- Truncate episode content to 2000 chars (from constraints)

Risk assessment:
- Neo4j docker service addition is safe (additive, no existing service conflicts)
- Adding env vars to .env is safe (no overwriting of existing vars)
- graphiti_client.py creation is greenfield (no existing file)
- All wiring is additive — existing functionality preserved via try/except wrapping
- Main.py startup/shutdown hooks are well-understood pattern

Approach:
1. Contract batch 1 (5): Infrastructure (docker-compose, env, requirements, client, test)
2. Contract batch 2 (5): Memory module wiring (memory_engine, long_term_memory, joint_memory, legion_memory_facade, episodic_narrative)
3. Contract batch 3 (4): Bridge wiring (autonomous_router, intent_router, task_orchestrator, mcp_client)
4. Contract batch 4 (2): Lifecycle (main.py startup/shutdown) + final validation

Total: 16 contracts across 4 batches.