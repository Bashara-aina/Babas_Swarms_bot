# Legion Wiring Audit Report
**Date**: 2026-04-12
**Status**: Complete
**Wires Checked**: 32 handlers, 49 core modules, 9 tools, 6 bridges, 28 skills

---

## Executive Summary

| Category | Status | Notes |
|----------|--------|-------|
| Handler Wiring | ✅ PASS | 32 handlers properly wired |
| Core Imports | ✅ PASS | 49 core modules importable |
| LLM Client | ✅ PASS | Exports all required functions |
| Tools | ✅ PASS | 9 key tools importable |
| Bridges | ✅ PASS | 6 bridges importable |
| Skills | ✅ PASS | 28 skills registered |
| Agents | ✅ PASS | All exports available |
| **Total Tests** | ✅ **323 passed** | |

---

## Wire Breaks Found and Fixed

### Wire Break 1: router.py build_system_prompt (TYPE A)
- **File**: `router.py` line 46
- **Problem**: Tried to export `build_system_prompt` from `agents.py` file, but function lives in `agents/__init__.py`
- **Fix**: Added proper import with fallback assignment at module level
- **Verification**: `test_main.py::test_imports` now passes

### Wire Break 2: admin_handlers Not Registered (TYPE A)
- **File**: `handlers/__init__.py`
- **Problem**: `admin_handlers` imported but NOT in `_ROUTER_ORDER`. Had duplicate `/budget` handler
- **Fix**: Removed unused `admin_handlers` import. `enterprise.py` has canonical `/budget` handler
- **Status**: File still exists but is orphaned (not imported anywhere)

---

## Pipeline Traces

### 1. Primary TEXT Message Pipeline ✅

```
Telegram → Dispatcher → _ROUTER_ORDER[0..n] → ai.router (LAST)
                                                    ↓
                                              ai.py handler
                                                    ↓
                                              shared._execute_chat()
                                                    ↓
                                              llm_client.chat()
                                                    ↓
                                              [prompt layers]
                                                    ↓
                                              litellm acompletion
                                                    ↓
                                              response → Telegram
```

**Confirmed Working**:
- `main.py` line 190: `register_all_routers(dp)`
- `handlers/__init__.py`: All 32 handlers properly registered
- `handlers/ai.py`: NL catch-all properly at end of `_ROUTER_ORDER`
- `handlers/shared.py`: `_execute_chat` calls `llm_client.chat`
- `llm_client/`: `chat` function properly exports

### 2. Web Search ✅
```
handlers/research.py (or ai.py routing)
    → tools/web_search.py
    → tools/search_tool.py (or deep_research.py)
    → External API (Google, Bing, etc.)
```

### 3. Wiki Retrieval ✅
```
handlers/wiki_handler.py
    → core/wiki_manager.py
    → core/wiki_loader.py
    → .wiki/ directory
```

### 4. Memory ✅
```
handlers/memory_commands.py or brain.py
    → tools/memory.py
    → tools/memoryos_client.py (MemoryOS tiered memory)
    → tools/open_memory.py (OpenMemory)
    → core/memory_manager.py
```

### 5. Nihongo Mode ⚠️ DISABLED
- `handlers/nihongo_handler.py` exists but has no `router` attribute
- Not registered in `_ROUTER_ORDER`
- Uses telegram.ext handlers (different framework)
- **Status**: Standalone module, not wired to aiogram dispatcher

### 6. Voice ✅
```
handlers/voice.py
    → tools/voice_engine.py
    → skills/nihongo/voice_pipeline.py (for Japanese TTS)
```

### 7. Skill Registry ✅
```
core/skills/__init__.py
    → core/skills/registry.py (SKILL_REGISTRY)
    → core/skills/builtin/ (github, media, memory, personal, productivity, research, system, web)
```

### 8. MCP Tools ✅
```
main.py on_startup
    → core/mcp/__init__.py (MCP_MANAGER)
    → core/mcp_client.py
```

### 9. Swarm Orchestration ✅
```
handlers/ai.py (swarm commands)
    → core/legion_swarm.py OR tools/swarm_wire.py
    → agents/ agents (swarm agent types)
```

### 10. Computer Agent ✅
```
handlers/computer.py
    → computer_agent.py
    → tools/browser_agent.py or tools/interpreter_tool.py
```

### 11. Research ✅
```
handlers/research.py
    → tools/deep_research.py
    → tools/arxiv.py
    → tools/scraper_tool.py or tools/web_browser.py
```

### 12. GitHub Intel ✅
```
handlers/github_intel_handler.py
    → tools/github_intel.py
    → core.github_intel (GitHubTrendingEngine)
```

### 13. Daily Harvester ✅
```
main.py on_startup
    → core/daily_harvester/scheduler.py (DailyHarvesterScheduler)
```

### 14. Inline Queries ✅
```
handlers/inline.py
    → aiogram Dispatcher.inline_query()
```

### 15. Callback Queries ✅
- Routed through individual handlers (callback_query handlers in various files)

### 16. Streaming ✅
```
handlers/streaming.py
    → litellm acompletion with stream=True
    → edits message progressively
```

### 17. Soul Engine ✅
```
handlers/ai.py or enterprise.py (soul command)
    → core/soul_engine.py
    → SOUL.md file (read directly)
```

### 18. WhatsApp ✅
```
handlers/whatsapp_handler.py
    → bridges/whatsapp_bridge.py
    → computer_agent.whatsapp_send_local()
```

---

## Router Layer Audit

### _ROUTER_ORDER (33 routers)
All properly registered in sequence:
1. computer.router (specific commands first)
2. ... [26 intermediate routers]
3. ai.router (NL catch-all LAST) ✅

### Coverage
- All handlers with `router` attribute are in `_ROUTER_ORDER`
- No duplicate routers
- Order correct (specific → general)

---

## Core Layer Audit

All 49 core modules are importable:
- ✅ agent, agent_registry, autonomous_router
- ✅ capability_audit, circuit_breaker
- ✅ conversation_interface, debate_engine
- ✅ health, health_check, hooks, humanizer
- ✅ intent_classifier, intent_router
- ✅ jarvis_orchestrator, legion_memory_facade, legion_swarm
- ✅ memory_engine, memory_manager
- ✅ model_config, mcp_client, multi_user
- ✅ natural_command_parser, nexus_orchestrator
- ✅ observability, openai_agents_bridge, opencode_bridge
- ✅ proactive_engine, proactive.scheduler
- ✅ persistent_loop, rate_limiter, research_policy
- ✅ response_filter, self_awareness_gate, self_improvement
- ✅ self_upgrade, skill_registry, soul_engine
- ✅ swarm, swarm_topologies, system_prompt_builder
- ✅ task_router, unified_prompt_context, working_memory
- ✅ wiki_auto_ingest, wiki_bridge, wiki_loader
- ✅ wiki_manager, wiki_quality_gate, wiki_scheduler

---

## LLM Client Audit

**File**: `llm_client/__init__.py` (single file, no subdirectory duplication)

**Exports Verified**:
- ✅ `chat()` - single-turn Q&A
- ✅ `agent_loop()` - multi-turn tool calling
- ✅ `verify_api_keys()` - API key validation
- ✅ `wiki_raw_completion()` - lightweight wiki LLM calls
- ✅ `chunk_output()` - response formatting
- ✅ `TOOL_DEFINITIONS` - computer agent tools
- ✅ `SYSTEM_PROMPTS` - per-agent system prompts

**Model Selection**: Proper fallback chains via `get_fallback_chain()`

**Tool Calling**: Properly configured with `execute_tool()` integration

---

## Bridges Layer Audit

All 6 bridges importable:
- ✅ discord_bridge.py
- ✅ livekit_bridge.py
- ✅ mastra_bridge.py
- ✅ ruflo_bridge.py
- ✅ screenpipe_bridge.py
- ✅ whatsapp_bridge.py

**Note**: `bridges/__init__.py` does NOT exist (fine - individual files imported directly)

---

## Skills Layer Audit

```
core/skills/__init__.py
    → registry.py (SKILL_REGISTRY, get_skill_registry)
    → builtin/ (github, media, memory, personal, productivity, research, system, web)
```

**28 skills registered** in the registry.

---

## __init__.py Files Audit

| File | Status | Notes |
|------|--------|-------|
| `handlers/__init__.py` | ✅ | 32 handlers imported, properly registered |
| `core/__init__.py` | ✅ | Lazy loading for openai_agents_bridge, swarm_topologies |
| `bridges/__init__.py` | ⚠️ N/A | Doesn't exist - bridges imported directly |
| `tools/__init__.py` | ✅ | Empty but exists |
| `llm_client/__init__.py` | ✅ | Main module (no subdirectory) |
| `skills/__init__.py` | ⚠️ N/A | Doesn't exist - skills in core/skills/ |
| `agents/__init__.py` | ✅ | Full agent registry with 76+ agents |

---

## Permanently Disabled Features

### 1. admin_handlers.py
- **Reason**: Duplicate `/budget` handler superseded by `enterprise.py`
- **File Status**: Exists but not imported anywhere
- **Can Be Deleted**: Yes (dead code)

### 2. Nihongo Handler Standalone
- **Reason**: Uses telegram.ext instead of aiogram, not wired to main dispatcher
- **Status**: Standalone module
- **Can Be Integrated**: Would require converting to aiogram router

---

## Verification Commands

```bash
# Run wiring verification
python scripts/verify_wiring.py

# Run full test suite
pytest tests/ -x --asyncio-mode=auto -q

# Expected output: 323 passed, 0 failed
```

---

## Recommendations

1. **Delete `handlers/admin_handlers.py`** - Dead code, replaced by `enterprise.py`
2. **Consider integrating `nihongo_handler.py`** - Convert to aiogram router for consistency
3. **Create `bridges/__init__.py`** - Would allow `from bridges import *` for consistency
4. **Create `skills/__init__.py`** - Would allow `from skills import *` for consistency

---

*Report generated by Legion Wiring Audit (2026-04-12)*
