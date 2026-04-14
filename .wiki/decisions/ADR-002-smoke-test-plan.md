---
title: Adr 002 Smoke Test Plan
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: This ADR defines a smoke test strategy that divides the Legion codebase into
  10 logical buckets for parallel testing. Each bucket focuses on a distinct feature
  area and verifies basic functionality...
wikilinks: []
confidence: medium
source: research
---
This ADR defines a smoke test strategy that divides the Legion codebase into 10 logical buckets for parallel testing. Each bucket focuses on a distinct feature area and verifies basic functionality ("doesn't crash") without deep testing.

**Test Philosophy**: Smoke tests validate that modules initialize, import cleanly, and handle basic calls without exceptions. They are NOT comprehensive tests.
---


## Bucket Definitions

### Bucket 1: Telegram Handler Routes
**Category**: Message & Command Handlers  
**Files**: `handlers/*.py` (45+ router files)  
**Smoke Test**: Import each handler module, verify router registration succeeds, check dispatcher wiring

**Key Components**:
- `handlers/ai.py` — AI conversation routing
- `handlers/brain.py` — Brain/cognition handlers
- `handlers/business_handler.py` — Business logic handlers
- `handlers/communications.py` — Communication protocols
- `handlers/computer.py` — Computer control handlers
- `handlers/debate_handlers.py` — Debate system
- `handlers/dev.py` — Developer tools
- `handlers/e2e.py` — End-to-end handlers
- `handlers/enterprise.py` — Enterprise features
- `handlers/github_intel_handler.py` — GitHub integration
- `handlers/inline.py` — Inline query handlers
- `handlers/memory_commands.py` — Memory commands
- `handlers/message_handler.py` — Core message routing
- `handlers/orchestrate.py` — Orchestration handlers
- `handlers/persona_handler.py` — Persona management
- `handlers/pm.py` — Project management
- `handlers/research.py` — Research tools
- `handlers/runbook_handler.py` — Runbook execution
- `handlers/session_handler.py` — Session management
- `handlers/sessions.py` — Session handlers
- `handlers/skills.py` — Skills system
- `handlers/streaming.py` — Streaming responses
- `handlers/system.py` — System commands
- `handlers/tasks.py` — Task management
- `handlers/voice.py` — Voice processing
- `handlers/whatsapp_handler.py` — WhatsApp bridge
- `handlers/wiki_handler.py` — Wiki operations
- `handlers/wiki.py` — Wiki handlers
- `handlers/streaming.py` — Streaming

**Verify**: Each handler module loads without ImportError, router registers with dispatcher

---

### Bucket 2: Agent System (76+ Agents, 9 Departments)
**Category**: Multi-Agent Orchestration  
**Files**: `agents/**/*.py`, `core/agent_registry.py`  
**Smoke Test**: Import agent registry, verify all department agents load, check agent instantiation

**Key Components**:
- `agents/engineering/` — Software engineering agents
- `agents/design/` — Design agents
- `agents/research/` — Research agents
- `agents/marketing/` — Marketing agents
- `agents/operations/` — Operations agents
- `agents/legal_compliance/` — Legal/compliance agents
- `agents/product/` — Product agents
- `agents/creative/` — Creative agents
- `agents/vision_multimodal/` — Vision/multimodal agents
- `agents/nexus/` — Nexus orchestration agents
- `agents/voice_agent.py` — Voice processing
- `agents/research_agent.py` — Research agent
- `agents/code_agent.py` — Code generation
- `agents/owl_agent.py` — OWL complex task agent
- `agents/simulation_agent.py` — Simulation agent
- `agents/mirofish_agent.py` — Social simulation

**Verify**: All 76+ agents import without errors, registry loads from YAML

---

### Bucket 3: Core Intent & Memory Systems
**Category**: Intent Classification & Memory Management  
**Files**: `core/intent_router.py`, `core/intent_classifier.py`, `core/memory*/**`, `core/soul_engine.py`  
**Smoke Test**: Initialize intent router, verify memory tiers load, check soul engine instantiation

**Key Components**:
- `core/intent_router.py` — Intent routing logic
- `core/intent_classifier.py` — Intent classification
- `core/memory_manager.py` — Memory orchestration
- `core/memory/temporal_graph.py` — Temporal knowledge graph
- `core/memory/episodic_store.py` — Episodic memory
- `core/memory/unified_context.py` — Context aggregation
- `core/memory/user_profile.py` — User profiles
- `core/memory/consolidator.py` — Memory consolidation
- `core/memory/semantic_cache.py` — Semantic caching
- `core/soul_engine.py` — Soul/personality engine
- `core/cognition_pipeline.py` — Cognition processing
- `core/conversation_interface.py` — Conversation API

**Verify**: Intent router initializes, memory stores load, soul engine starts

---

### Bucket 4: Swarm Bot Enterprise Layer
**Category**: Enterprise Orchestration, Routing & Security  
**Files**: `swarms_bot/**/*.py`  
**Smoke Test**: Initialize all enterprise components, verify routing and security modules load

**Key Components**:
- `swarms_bot/orchestrator/chief_of_staff.py` — Chief of staff orchestrator
- `swarms_bot/orchestrator/dag_executor.py` — DAG execution
- `swarms_bot/orchestrator/dag_planner.py` — DAG planning
- `swarms_bot/orchestrator/registry.py` — Agent registry
- `swarms_bot/orchestrator/agent_base.py` — Base agent class
- `swarms_bot/orchestrator/nested_agents.py` — Nested agent support
- `swarms_bot/routing/cost_router.py` — Cost-based routing
- `swarms_bot/routing/budget_manager.py` — Budget management
- `swarms_bot/sessions/session_manager.py` — Session management
- `swarms_bot/security/guard.py` — Security guard
- `swarms_bot/security/rate_limiter.py` — Rate limiting
- `swarms_bot/audit/audit_logger.py` — Audit logging
- `swarms_bot/evaluation/evaluator.py` — Agent evaluation
- `swarms_bot/observability/logging_config.py` — Observability config
- `swarms_bot/observability/cost_metrics.py` — Cost metrics

**Verify**: All enterprise components initialize, chief_of_staff wires correctly

---

### Bucket 5: External Integrations & Tools
**Category**: Third-party Tools & External Services  
**Files**: `tools/**/*.py` (excluding mirofish/)  
**Smoke Test**: Import each tool module, verify client initialization doesn't crash

**Key Components**:
- `tools/browser_agent.py` — Browser automation
- `tools/email_client.py` — Email operations
- `tools/github_intel.py` — GitHub intelligence
- `tools/n8n_bridge.py` — n8n automation
- `tools/voice_engine.py` — Voice processing
- `tools/composio_client.py` — Composio integration
- `tools/memoryos_client.py` — MemoryOS client
- `tools/supabase_client.py` — Supabase backend
- `tools/scraper_tool.py` — Web scraping
- `tools/search_tool.py` — Search functionality
- `tools/rag_tool.py` — RAG operations
- `tools/runbook_engine.py` — Runbook execution
- `tools/skill_loader.py` — Skill loading
- `tools/web_browser.py` — Web browser control
- `tools/open_memory.py` — OpenMemory integration
- `tools/mneme_session.py` — Session management
- `tools/proactive_monitors.py` — Proactive monitoring
- `tools/deep_research.py` — Deep research
- `tools/recallmax.py` — Recall optimization

**Verify**: All tool modules import, clients initialize with mock configs

---

### Bucket 6: LLM Client & Model Routing
**Category**: LLM Integration & Model Selection  
**Files**: `llm_client.py`, `llm_client/**`, `core/model_router.py`, `core/reliability/**`  
**Smoke Test**: Initialize LLM client, verify model router loads, check fallback chain

**Key Components**:
- `llm_client.py` — Main LLM client (litellm wrapper)
- `llm_client/__init__.py` — Client exports
- `core/model_router.py` — Model selection router
- `core/reliability/fallback_chain.py` — Fallback handling
- `core/reliability/provider_health.py` — Provider health checks
- `core/reliability/error_recovery.py` — Error recovery
- `core/reliability/request_throttle.py` — Request throttling
- `core/model_config.py` — Model configuration
- `core/opencode_bridge.py` — OpenCode integration
- `core/interpreter_bridge.py` — Interpreter bridge

**Verify**: LLM client initializes, model router loads configs, fallback chain builds

---

### Bucket 7: Proactive Systems & Schedulers
**Category**: Background Jobs & Proactive Execution  
**Files**: `core/proactive/**`, `core/daily_harvester/**`, `tools/scheduler.py`, `tools/briefing.py`  
**Smoke Test**: Initialize schedulers, verify proactive engine loads, check harvester pipeline

**Key Components**:
- `core/proactive_engine.py` — Proactive execution engine
- `core/proactive/scheduler.py` — Task scheduler
- `core/proactive/curiosity_engine.py` — Curiosity-driven actions
- `core/proactive/proactive_initiator.py` — Proactive initiation
- `core/daily_harvester/harvest_pipeline.py` — Daily harvesting
- `core/daily_harvester/source_strategy.py` — Source strategies
- `core/daily_harvester/topic_budget.py` — Topic budgeting
- `core/wiki_scheduler.py` — Wiki quality scheduler
- `tools/scheduler.py` — Task scheduler
- `tools/briefing.py` — Daily briefing
- `tools/proactive_initiator.py` — Proactive starter
- `tools/proactive_monitors.py` — Monitoring agents

**Verify**: Schedulers initialize, proactive engine starts, harvester pipeline loads

---

### Bucket 8: Humanization & Personality Engine
**Category**: Personality, Emotion & Humanization  
**Files**: `core/personality/**`, `core/character/**`, `core/humanizer.py`, `tools/emotion_modulator.py`  
**Smoke Test**: Initialize personality system, verify emotion engine loads, check humanization layer

**Key Components**:
- `core/personality/personality.py` — Personality traits
- `core/personality/emotion_engine.py` — Emotion processing
- `core/character/persona.py` — Persona definition
- `core/character/enforcer.py` — Character enforcement
- `core/character/disagreement_protocol.py` — Disagreement handling
- `core/humanizer.py` — Humanization layer
- `core/soul_engine.py` — Soul engine
- `tools/emotion_modulator.py` — Emotion modulation
- `tools/letta_personality.py` — Letta personality integration
- `core/reflection/reflection_engine.py` — Reflection engine

**Verify**: Personality loads, emotion engine initializes, humanizer layer activates

---

### Bucket 9: Computer Control & Desktop Agent
**Category**: Desktop Control & Computer Use  
**Files**: `computer_agent/**`, `core/tools/computer_control.py`, `core/tools/playwright_agent.py`, `core/tools/vscode_bridge.py`  
**Smoke Test**: Initialize computer agent, verify control modules load, check playwright setup

**Key Components**:
- `computer_agent/__init__.py` — Computer agent main
- `computer_agent/computer.py` — Computer control
- `core/tools/computer_control.py` — Desktop control
- `core/tools/playwright_agent.py` — Playwright browser agent
- `core/tools/vscode_bridge.py` — VSCode integration
- `bridges/screenpipe_bridge.py` — Screenpipe monitoring

**Verify**: Computer agent initializes, control modules load, display detection works

---

### Bucket 10: Persistence & Data Layer
**Category**: Storage, Databases & Data Operations  
**Files**: `tools/memory.py`, `tools/persistence.py`, `core/memory/memory_manager.py`, `core/memory/tiers.py`  
**Smoke Test**: Initialize database connections, verify storage backends load, check session persistence

**Key Components**:
- `tools/memory.py` — Memory operations
- `tools/persistence.py` — Persistence layer
- `core/memory/memory_manager.py` — Memory management
- `core/memory/tiers.py` — Memory tier system
- `core/memory/episodic_store.py` — Episodic storage
- `core/memory/consolidator.py` — Memory consolidation
- `core/relationship_memory.py` — Relationship memory
- `core/knowledge_manager.py` — Knowledge management
- `core/episodic_narrative.py` — Narrative memory

**Verify**: Database initializes, memory stores load, session persistence works

---

## Test Execution

Each bucket should run independently with:

```bash
# Per bucket smoke test pattern
cd /home/newadmin/swarm-bot
python -c "import <bucket_module>; print('<bucket>: OK')"
```

**Success Criteria**: All 10 buckets complete without ImportError or RuntimeError on initialization.

---

## Parallelization Strategy

| Bucket | Subagent | Focus Area |
|--------|----------|------------|
| 1 | worker-1 | Handler routes (45+ files) |
| 2 | worker-2 | Agent system (76+ agents) |
| 3 | worker-3 | Core intent & memory |
| 4 | worker-4 | Swarm bot enterprise |
| 5 | worker-5 | External tools/integrations |
| 6 | worker-6 | LLM client & routing |
| 7 | worker-7 | Proactive & schedulers |
| 8 | worker-8 | Humanization & personality |
| 9 | worker-9 | Computer control |
| 10 | worker-10 | Persistence & data layer |

---

## References

- Existing tests: `tests/` directory
- Agent registry: `core/agent_registry.py`
- Main entry: `main.py`
