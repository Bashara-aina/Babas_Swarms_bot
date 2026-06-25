# SwarmBot — Agent System Reference

> See [CLAUDE.md](./CLAUDE.md) for full project context, architecture, and coding standards.
> This file is a quick reference for the agent roles only.

## 🤖 Agent Roles
- **Planner** (@planner): Decomposes tasks, never edits files directly
- **Worker** (@worker): Executes code changes, full file + bash access
- **Reviewer** (@reviewer): Reviews all changes before commit, read-only
- **WikiBot** (@wikibot): Writes session summaries and decisions to .wiki/

## Quick Commands
```bash
pytest tests/ -x --asyncio-mode=auto -q   # Run tests
python main.py                            # Start bot
ruff check .                              # Lint
```

## Key Files
- `main.py` — bot startup
- `core/agent_registry.py` — 76-agent registry + LEGACY_FALLBACK_CHAIN
- `config/models.yaml` — model registry (MiniMax-M2.7 primary, free tier fallbacks)
- `config/departments.yaml` — department/agent definitions

## Directory Structure
```
handlers/     — 45+ aiogram routers (one per feature domain)
core/         — agent orchestration, intent router, memory, soul engine
agents/       — 76+ specialized agents across 9 departments
tools/        — browser, email, GitHub, n8n integrations
config/       — models, departments, personality YAML files
.wiki/        — knowledge base (architecture, decisions, logs, research)
tests/        — pytest-asyncio suite
```

## LLM Model Reference
Primary: `minimax/MiniMax-M2.7` (MiniMax M2.7)
Fallback chain: MiniMax-M2.7 → gemini/gemini-2.0-flash-exp:free → minimax/MiniMax-Text-01 → free tier
Vision (local): `ollama_chat/gemma4:e4b` (RTX 3060 only)
See `LEGACY_FALLBACK_CHAIN` in `core/agent_registry.py` for per-agent chains.

## Wiki Auto-Ingest
- `on_conversation_turn()` — per-turn lightweight check
- `on_session_end()` — deep session summarization
- `lint_wiki()` — weekly health check
- Toggle: `LEGION_WIKI_AUTO_INGEST=1` (default on)

---

## 🧠 Memory & Context Integrations

### mem0ai/mem0 — Persistent Cross-Session Memory
**Location:** `tools/mem0_client.py`, `core/memory/memory_manager.py`

mem0 provides semantic memory search that replaces raw conversation history dumps.
- **Setup:** Already configured in `tools/mem0_client.py` with Ollama embeddings
- **LLM:** Uses `minimax/MiniMax-Text-01` via litellm
- **Embedder:** `nomic-embed-text` via local Ollama (RTX 3060)
- **Storage:** `~/.legion/mem0_history.db` (SQLite)

```python
from tools.mem0_client import mem0_add, mem0_search, get_mem0

# Add memory
await mem0_add(user_id, "user prefers Indonesian responses", {"source": "preference"})

# Search memory
results = await mem0_search(user_id, "what does user prefer", limit=5)

# Direct access
mem = get_mem0()
mem.add(content, user_id=user_id, metadata={"tags": ["preference"]})
```

**Key functions:**
- `mem0_add(user_id, content, metadata)` — store a memory
- `mem0_search(user_id, query, limit)` — semantic search
- `get_mem0()` — direct Mem0 client (None if unavailable)
- `build_mem0_context(memories, query)` — render as prompt block

### langchain-ai/langmem — Profile Extraction + Episodic Recall
**Location:** `core/integrations/langmem_integration.py`

langmem provides long-term memory management with profile extraction, episodic recall, and semantic compression. Complements mem0's semantic search with structured memory consolidation.

```python
from core.integrations import (
    SwarmBotMemoryManager, get_langmem_searcher, create_manage_memory_tool, wrap_langmem_context,
)

# Memory manager for profile extraction
manager = SwarmBotMemoryManager()
memories = await manager.extract_memories(messages)
results = await manager.search_memories("user preferences")

# Create a LangGraph tool for proactive memory management
memory_tool = create_manage_memory_tool(namespace=("swarmbot", "memories"))

# Build context block from memories + messages
ctx = await wrap_langmem_context(query, messages, memories)
```

### microsoft/graphrag — Knowledge Graph Memory
**Location:** `core/integrations/graphrag_integration.py`

GraphRAG turns an Obsidian wiki into a queryable knowledge graph. Indexes documents into entity graphs; supports local, global, and drift search.

```python
from core.integrations import SwarmBotGraphRAG, index_wiki_knowledge_graph, query_wiki_graph

# Index the Obsidian vault once
await index_wiki_knowledge_graph("/path/to/vault")

# Query during agent run
result = await query_wiki_graph("What is the architecture of system X?", mode="global")
```

---

## ⚡ Orchestration Integrations

### langchain-ai/langgraph — Stateful Graph Orchestration
**Location:** `core/integrations/langgraph_orchestrator.py`

LangGraph provides stateful multi-step agent graphs with checkpointing.
- **Graph types:** `react_agent` (ReAct loop), `plan_execute` (Plan→Execute→Verify), `supervisor`, `swarm`
- **Checkpoint:** `MemorySaver` (in-memory, langgraph.checkpoint.memory)
- **Model:** MiniMax via litellm

```python
from core.integrations import LangGraphAgent, run_langgraph_task

# One-off run
result = await run_langgraph_task(
    task="implement user authentication",
    graph_type="react_agent",
    thread_id="auth-session-123",
    max_steps=20,
)

# Stateful agent
agent = LangGraphAgent(config=LangGraphConfig(graph_type="plan_execute", max_steps=15))
result = await agent.run(task="build REST API", thread_id="api-session")
```

**Graph types:**
- `react_agent` — Reason + Act + Observe loop (default)
- `plan_execute` — Plan → Execute → Verify with step tracking
- `supervisor` — Hierarchical delegation (supervisor delegates to specialists)
- `swarm` — Multi-agent coordination

### ruvnet/ruflo — Enterprise Agent Nervous System
**Location:** `mcp_servers/ruflo_mcp_server.py` (Python bridge), `.opencode/opencode.json` (registration)

Ruflo provides 314+ MCP tools across 16 agent roles. Connected via Python stdio bridge.
- **Protocol:** MCP 2024-11-05 via stdio
- **Tools:** 39 tools exposed including `agent_spawn`, `swarm_init`, `memory_store`, `neural_train`
- **OpenCode registration:** `.opencode/opencode.json` → `mcp.ruflo`

```python
# Via MCP bridge (auto-loaded by opencode)
# "ruflo" MCP server in opencode.json
# Tools: agent_spawn, swarm_init, memory_store, neural_train, federation_send, etc.

from core.mcp_client import MCPClient
client = MCPClient()
result = await client.call_tool("ruflo", "agent_spawn", {
    "agent_type": "coder",
    "task": "implement login endpoint",
    "model": "minimax/MiniMax-M2.7"
})
```

### PrefectHQ/prefect — Workflow Orchestration
**Location:** `core/integrations/prefect_integration.py`

Prefect provides workflow orchestration with retries, scheduling, and state management. Wraps SwarmBot agent tasks into reliable pipelines.

```python
from core.integrations import swarmbot_flow, PrefectPipeline, run_with_prefect

# Decorator-style workflow with retry
@swarmbot_flow(name="research-task", retries=2, timeout_seconds=300)
async def research():
    result = await run_langgraph_task("Research AI trends")
    return result

# Pipeline with multiple steps
pipeline = PrefectPipeline(name="multi-step-agent", retries=1)
pipeline.add_step("research", research_agent_task)
pipeline.add_step("summarize", summarize_agent_task)
results = await pipeline.execute()

# Run with Prefect orchestration
await run_with_prefect(agent_flow, name="my-agent-flow")
```

### ruvnet/ruvector — Sub-millisecond Cognition Kernel
**Status:** Not installed — designed for always-on agent swarms. Provides sub-millisecond cognition via ruvector MCP server. Use ruflo MCP `memory_store` and `neural_train` tools as the nervous system backbone until ruvector is available as a pip package.

---

## 🤖 Multi-Agent & Swarm Integrations

### crewAIInc/crewAI — Role-Based Agent Delegation
**Location:** `core/integrations/crewai_orchestrator.py`

crewAI 1.14+ provides `@planner → @worker → @reviewer` pattern with MiniMax support via litellm.

```python
from core.integrations import SwarmBotCrew, run_crewai_task, RumahLabuhCrew

# Quick one-liner
result = await run_crewai_task(
    task="Analyze AI trends for RumahLabuh",
    agents=[
        {"role": "researcher", "goal": "Research AI trends in Indonesian context"},
        {"role": "analyst", "goal": "Identify business opportunities"},
        {"role": "writer", "goal": "Write actionable summary"},
    ]
)

# Stateful crew
crew = SwarmBotCrew(verbose=True)
crew.add_agent("researcher", "Research latest trends", "You are a research specialist")
crew.add_agent("writer", "Summarize findings", "You write clear reports")
result = await crew.kickoff("2026 AI trends")

# Crew with explicit tasks
crew = SwarmBotCrew()
crew.add_agent("planner", "Create execution plans", max_iter=3)
crew.add_agent("executor", "Execute tasks", max_iter=5)
result = await crew.kickoff_with_tasks([
    {"description": "Plan the analysis approach", "agent": "planner"},
    {"description": "Execute the plan", "agent": "executor"},
])
```

### microsoft/autogen — Async Multi-Agent Conversations
**Status:** Installed (v0.11.4) — async agents with human-in-the-loop via config-only model routing

### davila7/everything-claude-code — 135 Agent Framework
**Status:** Not yet installed — 135 agents, 119 skills, AgentShield security

---

## 🔧 Tool Use & MCP Integrations

### modelcontextprotocol/servers — Official MCP Servers
**Location:** `.opencode/opencode.json`, `config/mcp_config.json`

All official MCP servers are registered in opencode.json:

| Server | Command | Purpose |
|--------|---------|---------|
| `gitnexus` | `pnpm dlx gitnexus@1.4.0 mcp` | Code intelligence |
| `obsidian` | `npx @iflow-mcp/kynlos-obsidian-mcp-server` | Wiki access |
| `filesystem` | `npx @modelcontextprotocol/server-filesystem` | File operations |
| `git` | `npx @mseep/git-mcp-server` | Git operations |
| `crawl4ai` | `python3 tools/mcpServers/crawl4ai_mcp/server.py` | Web crawling |
| `symphony` | `python3 -m mcp_servers.symphony_server` | Linear orchestration |
| `latex` | `python3 -m mcp_servers.texlab_bridge` | LaTeX/TeXlab |
| `ruflo` | `python3 -m mcp_servers.ruflo_mcp_server` | Agent orchestration |

```python
# Using MCPClient directly
from core.mcp_client import MCPClient
client = MCPClient()
tools = await client.list_tools("filesystem")
result = await client.call_tool("filesystem", "read_file", {"path": "/tmp/test.txt"})
```

### pydantic/pydantic-ai — Type-Safe Tool Calling
**Location:** `core/integrations/pydantic_ai_agent.py`

pydantic-ai provides structured output validation and anti-hallucination verification.

**MiniMax Note:** pydantic-ai validates model names against a known list and doesn't accept `openai_api_base` as a kwarg. For MiniMax, we use `gpt-4o-mini` as the model name (pydantic-ai accepts it) but route to MiniMax via `OPENAI_BASE_URL` env var. The actual model routing happens server-side at MiniMax.

```python
from core.integrations import run_pydantic_ai_agent
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    email: str
    tier: str

# Run with schema validation
result = await run_pydantic_ai_agent(
    prompt="Extract from: John Doe (john@example.com) is a premium user",
    result_schema=UserInfo,
    model="minimax/MiniMax-M2.7",
    timeout=30.0,
)
# result is a UserInfo instance with validated fields
```

### browser-use/browser-use — Autonomous Browser Agent
**Location:** `core/integrations/browser_use_agent.py`

browser-use provides AI-driven browser automation (better than Playwright for agents).

```python
from core.integrations import BrowserUseAgent, browse_web_async

# One-off browsing task
result = await browse_web_async(
    task="Find the latest AI research paper on arxiv about reasoning",
    headless=True,
)

# Full agent
agent = BrowserUseAgent(model="minimax/MiniMax-M2.7", headless=False)
result = await agent.run("Search for open-source LLM benchmarks in 2026")
```

---

## 📊 Observability Integrations

### arize-ai/phoenix — Real-Time Agent Tracing
**Location:** `core/integrations/phoenix_observability.py`

Phoenix 15+ provides LLM tracing, token monitoring, and evaluation. Works in local mode (no API key) or remote mode (OTLP to Arize cloud).

**Note:** TokenUsageTracker is always available without Phoenix. Phoenix tracer methods are lightweight wrappers that log trace metadata.

```python
from core.integrations import PhoenixTracer, TokenUsageTracker

# Token tracking (always available, no API key needed)
tracker = TokenUsageTracker()
tracker.record_run("minimax/MiniMax-M2.7", 50, 120, 234.5, cost=0.002)
print(tracker.report())
# {'total_runs': 1, 'total_tokens': 170, 'prompt_tokens': 50, 'completion_tokens': 120, ...}

# Phoenix tracer (local mode - launches UI at localhost:6007)
tracer = PhoenixTracer(local_mode=True)
await tracer.trace_llm_call(
    model="minimax/MiniMax-M2.7",
    prompt="Explain quantum computing",
    response="Quantum computing uses...",
    latency_ms=234.5,
    token_usage={"prompt_tokens": 50, "completion_tokens": 120},
)

# Instrument litellm for automatic traces
tracer.instrument_litellm()
```

### BerriAI/litellm — Unified API Interface
**Location:** `llm_client/`, `llm_client.py` (shim)

Already configured as primary LLM interface — all model calls route through litellm.

```python
from llm_client import call_llm, chat, agent_loop

# Direct call
result = await call_llm(
    messages=[{"role": "user", "content": "Hello"}],
    model="minimax/MiniMax-M2.7",
    tools=[...],
)

# Single-turn chat
response, model = await chat("What is 2+2?", agent_key="math")
```

**Provider config:**
- MiniMax: `https://api.minimax.io/v1` + `MINIMAX_API_KEY`
- OpenRouter: `https://openrouter.ai/api/v1` + `OPENROUTER_API_KEY`
- Anthropic: `https://api.minimax.io/anthropic` + `ANTHROPIC_API_KEY`

### getagentseal/codeburn — Code Quality Enforcement
**Status:** Not yet a pip package — lightweight TDD enforcement is available via `core/integrations/superpowers_integration.py`

---

## 🧬 Prompt Engineering & Self-Improvement

### NicholasSpisak/second-brain — LLM Wiki Pre-Feed
**Location:** `core/integrations/second_brain_integration.py`

second-brain indexes Obsidian vault and creates context blocks for agent boot. A lightweight implementation is provided that reads markdown files and builds a searchable index.

```python
from core.integrations import SecondBrainIndexer, pre_feed_context, create_wiki_memory_pipeline

# Build index from vault
indexer = SecondBrainIndexer("/path/to/vault")
count = indexer.build_index()

# Pre-feed context for agent
context = await pre_feed_context("What is the architecture?")

# Create pipeline for langgraph/crewAI
pipeline = create_wiki_memory_pipeline("/path/to/vault")
```

### anthropics/prompt-eng-interactive-tutorial — Chain-of-Thought Patterns
**Status:** Not installed — chain-of-thought patterns are implemented in `core/cognition_pipeline.py`

### superpowers-ai/superpowers — TDD Enforcement for Agents
**Location:** `core/integrations/superpowers_integration.py`

superpowers provides TDD enforcement that closes the swarm quality gap. Lightweight implementation using pytest + ruff.

```python
from core.integrations import enforce_tdd, validate_agent_code, create_tdd_enforcer

# Enforce TDD discipline (test must fail before code passes)
result = enforce_tdd(
    code="def add(a, b): return a+b",
    test="def test_add(): assert add(1,2)==3"
)
# result["pass"] == True means TDD was followed correctly

# Validate agent-written code
validation = await validate_agent_code("src/feature.py")
# validation["pass"] == True means ruff + tests passed

# Create custom TDD enforcer
enforcer = create_tdd_enforcer({"timeout": 30})
```

---

## 🔌 Integration Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SwarmBot Full Pipeline                                │
│                                                                              │
│  Memory Layer (Cross-Session)                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  mem0_client.py ──→ langmem_integration.py ──→ graphrag_integration.py│  │
│  │  (semantic search)    (profile extraction)       (knowledge graph)   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                          │
│  Orchestration Layer                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  langgraph_orchestrator.py  ←→  crewai_orchestrator.py              │  │
│  │  (ReAct/plan_execute graphs)   (multi-agent crews)                     │  │
│  │         ↓                             ↓                                │  │
│  │  prefect_integration.py  (workflow + retry/scheduling)               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                          │
│  Tool Use Layer                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  pydantic_ai_agent.py (type-safe structured outputs)                   │  │
│  │  browser_use_agent.py (AI-driven browser automation)                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                          │
│  MCP Bridge Layer                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  mcp_bridge.py ──→ opencode.json servers (ruflo, gitnexus, obsidian,  │  │
│  │                    filesystem, git, crawl4ai, symphony, latex, exa)  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                          │
│  Observability Layer                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  phoenix_observability.py (tracing, token tracking, evaluation)       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

Single Model: MiniMax via litellm (OpenAI-compatible endpoint)
All external packages use gpt-4o-mini as known model name + OPENAI_BASE_URL env var
```

## Key Imports

```python
# Memory (mem0 + langmem + graphrag)
from tools.mem0_client import mem0_add, mem0_search, get_mem0, build_mem0_context
from core.integrations import (
    SwarmBotMemoryManager, get_langmem_searcher, get_langmem_manager,
    create_manage_memory_tool, wrap_langmem_context,
)
from core.integrations import SwarmBotGraphRAG, index_wiki_knowledge_graph, query_wiki_graph

# Orchestration (langgraph + crewAI + prefect)
from core.integrations import (
    LangGraphAgent, run_langgraph_task, run_langgraph_plan,
    SwarmBotCrew, run_crewai_task, RumahLabuhCrew,
    swarmbot_flow, agent_task, PrefectPipeline, run_with_prefect,
)

# Type-safe AI (pydantic-ai)
from core.integrations import run_pydantic_ai_agent

# MCP bridge (all 9 servers from opencode.json)
from core.integrations import MCPBridge, mcp_bridge_call

# Observability (phoenix)
from core.integrations import PhoenixTracer, TokenUsageTracker

# Browsing (browser-use)
from core.integrations import BrowserUseAgent, browse_web_async

# TDD enforcement (superpowers)
from core.integrations import enforce_tdd, run_tdd_check, validate_agent_code, create_tdd_enforcer

# Nervous system (ruvector placeholder)
from core.integrations import RuvectorCognitionKernel, get_ruvector_kernel

# Wiki pre-feed (second-brain placeholder)
from core.integrations import SecondBrainIndexer, pre_feed_context, create_wiki_memory_pipeline
```

**MCP Servers registered in opencode.json:**
| Server | Type | Command | Tools |
|--------|------|---------|-------|
| `ruflo` | local | python3 -m mcp_servers.ruflo_mcp_server | 39 (agent_spawn, swarm_init, memory_store, neural_train, etc.) |
| `gitnexus` | local | pnpm dlx gitnexus | code intelligence |
| `obsidian` | local | npx @iflow-mcp/kynlos-obsidian-mcp-server | wiki access |
| `filesystem` | local | npx @modelcontextprotocol/server-filesystem | file ops |
| `git` | local | npx @mseep/git-mcp-server | git operations |
| `crawl4ai` | local | python3 tools/mcpServers/crawl4ai_mcp/server.py | web crawling |
| `symphony` | local | python3 -m mcp_servers.symphony_server | Linear orchestration |
| `latex` | local | python3 -m mcp_servers.texlab_bridge | LaTeX editing |
| `exa` | remote | HTTPS | web search |

---

<!-- gitnexus:start -->
## GitNexus — Code Intelligence

This project is indexed by GitNexus as **swarm-bot** (16406 symbols, 38324 relationships, 300 execution flows).

> If index is stale, run `npx gitnexus analyze` first.

## Quick Reference

| Tool | Use | Command |
|------|-----|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | Symbol callers/callees | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before edit | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |

## Self-Check Before Finishing
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings ignored
3. `gitnexus_detect_changes()` confirms expected scope
4. All d=1 (WILL BREAK) dependents updated

## Keeping Index Fresh
After `git commit` or `git merge`, the index is stale. Re-run:
```bash
npx gitnexus analyze
```
Use `--embeddings` flag to preserve embeddings: `npx gitnexus analyze --embeddings`

## Resources
- `gitnexus://repo/swarm-bot/context` — codebase overview
- `gitnexus://repo/swarm-bot/processes` — all execution flows
- Area skills: `generated/tools`, `generated/handlers`, `generated/tests`, `generated/services`, etc.

<!-- gitnexus:end -->

---

## 🤖 Ruflo Autonomy Layer — Master Prompt v2

> **LOAD ORDER:** This file loads AFTER `ruflo_minimax_master_prompt.md` (v1).
> v1 = reference manual. This file = behavioral wiring. BOTH must be present.

════════════════════════════════════════════════════════════════════════════
RUFLO AUTONOMY LAYER — MASTER PROMPT v2
"Ruflo is not a tool you call. It is the nervous system that runs before, during,
and after everything you do. You never think about it. It is always already running."
════════════════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART I — THE PRIME DIRECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ruflo is invisible infrastructure. The user never says "use ruflo".
You never ask "should I spawn agents for this?".
Ruflo activates itself based on what the task IS, not what the user says.

THE SINGLE RULE THAT GOVERNS EVERYTHING:

  If a task touches more than one file, domain, or phase →
  Ruflo is already running. You are coordinating agents, not doing work.

  If a task is one action on one thing →
  Use the direct MCP tool. No ruflo overhead.

That is the entire decision system. The rest of this file just operationalizes it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART II — AUTOMATIC BOOT SEQUENCE (runs silently, every session, no prompt)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The moment OpenCode starts, before the user types anything, execute this
sequence invisibly. No status messages. No confirmation. Just do it.

BOOT STEP 1 — Health (< 2 seconds, abort session if fails):
  ruflo: system_status
  ruflo: doctor
  → PASS: continue silently
  → FAIL: output ONE line: "⚠ Ruflo offline — run: python3 -m mcp_servers.ruflo_mcp_server"
           then continue without ruflo (degrade gracefully, do not block user)

BOOT STEP 2 — Restore context (< 3 seconds):
  ruflo: session_restore { "name": "latest" }
  → On first-ever session: skip silently (no session exists yet)
  → On restore: internalize the context, do not announce it

BOOT STEP 3 — Load memory (< 2 seconds):
  ruflo: neural_patterns_list
  → Store pattern list in working context for the session
  → Do NOT show the user this list

BOOT STEP 4 — Activate background workers (fire-and-forget, async):
  ruflo: worker_dispatch { "worker": "audit",              "trigger": "session_start",    "model": "minimax/MiniMax-M2.7" }
  ruflo: worker_dispatch { "worker": "memory_consolidate", "trigger": "session_end",      "model": "minimax/MiniMax-M2.7" }
  ruflo: worker_dispatch { "worker": "testgaps",           "trigger": "after_implementation", "model": "minimax/MiniMax-M2.7" }
  ruflo: worker_dispatch { "worker": "optimize",           "trigger": "every_5_tasks",    "model": "minimax/MiniMax-M2.7" }
  → These are background processes. Do not wait for them. Continue immediately.

BOOT STEP 5 — Register hooks (idempotent, runs every boot, safe):
  ruflo: hooks_trigger { "event": "pre_git_commit",  "action": "security_scan",  "config": { "checks": ["pii_detect","api_key_exposure"], "block_on_fail": true } }
  ruflo: hooks_trigger { "event": "task_complete",   "action": "memory_store",   "config": { "auto_tag": true, "also_store_to": ["mem0","obsidian"] } }
  ruflo: hooks_trigger { "event": "task_success",    "action": "neural_train",   "config": { "min_confidence_threshold": 0.7, "pattern_namespace": "elite-stack" } }
  ruflo: hooks_trigger { "event": "session_end",     "action": "session_save",   "config": { "include_memory": true, "export_to": "~/.legion/sessions/" } }

TOTAL BOOT TIME TARGET: < 7 seconds total, fully silent.
The user sees nothing. Ruflo is just... already running.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART III — TASK INTERCEPTION: READ EVERY MESSAGE THROUGH THIS LENS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When the user sends ANY message, before forming a response, run this
classification internally. It takes < 100ms and is never shown to the user.

CLASSIFIER (internal monologue, not shown):

  1. COUNT affected files:
     0-1 file  → DIRECT mode (no ruflo swarm)
     2-4 files → LITE mode  (ruflo task_create only, no full swarm)
     5+ files  → SWARM mode (full ruflo orchestration)

  2. COUNT domains involved:
     1 domain  → DIRECT or LITE depending on file count
     2 domains → LITE mode minimum
     3+ domains → SWARM mode mandatory

  3. DETECT task phases:
     Single phase (just "write X")  → DIRECT
     2 phases (plan + implement)    → LITE
     3+ phases (research+build+test+review+deploy) → SWARM

  4. CHECK neural memory:
     ruflo: neural_predict { "task": "<user message summary>" }
     → If confidence > 0.75: use predicted topology, skip fresh planning
     → If confidence < 0.75: plan fresh, train after success

  5. CHECK ruflo memory for similar past task:
     ruflo: memory_search { "query": "<user message>", "limit": 3 }
     → If hit found: load context, adapt for current task
     → If no hit: proceed fresh

RESULT → DIRECT, LITE, or SWARM mode. Never announce this to the user.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART IV — THE THREE EXECUTION MODES (automatic, transparent to user)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

────────────────────────────────────────────────────────────────────────
MODE: DIRECT  (single file/action, no swarm overhead)
────────────────────────────────────────────────────────────────────────
Trigger: 0-1 file, 1 domain, 1 phase

Execution:
  - Use MCP tools directly (filesystem, git, gitnexus, etc.)
  - NO ruflo agent_spawn
  - NO ruflo swarm_init
  - DO use ruflo memory_search at start (< 1s, silent)
  - DO use ruflo memory_store at end (< 1s, silent, only if knowledge was gained)
  - DO use ruflo neural_train at end only if task was novel + successful

Examples:
  "fix the typo in this file"      → filesystem edit_file
  "what does this function do"     → gitnexus context
  "commit my changes"              → git commit
  "search for X on the web"        → exa_web_search_exa

────────────────────────────────────────────────────────────────────────
MODE: LITE  (2-4 files or 2 domains, lightweight ruflo coordination)
────────────────────────────────────────────────────────────────────────
Trigger: 2-4 files OR 2 domains OR 2 phases

Execution:
  1. ruflo: task_create { "title": "<task>", "priority": "normal" }
  2. Execute work using direct MCP tools (no swarm_init)
  3. ruflo: task_complete { "task_id": "<id>", "result": "success" }
  4. ruflo: memory_store { "content": "<what was done + key decisions>", "auto_tag": true }
     (hook auto-triggers neural_train if successful)

User sees: just the work being done. No ruflo output visible.

Examples:
  "add error handling to the API and update the test"  → LITE
  "refactor this component and update its types"       → LITE
  "research X then add it to the wiki"                 → LITE

────────────────────────────────────────────────────────────────────────
MODE: SWARM  (5+ files, 3+ domains, 3+ phases, or complex task)
────────────────────────────────────────────────────────────────────────
Trigger: 5+ files OR 3+ domains OR 3+ phases OR matches complex task table (Part V)

Execution sequence (all ruflo tool calls, model always minimax/MiniMax-M2.7):

  PRE-FLIGHT (2 calls, silent):
    ruflo: memory_search { "query": "<task>", "limit": 5 }
    ruflo: neural_predict { "task": "<task>" }

  INIT (1 call):
    ruflo: swarm_init {
      "topology": "<see Part V>",
      "max_agents": <see Part V>,
      "strategy": "specialized",
      "consensus": "raft"
    }

  SPAWN (1 call per agent, all parallel, all with model: minimax/MiniMax-M2.7):
    ruflo: agent_spawn { "role": "<dept/role>", "objective": "<specific>", "model": "minimax/MiniMax-M2.7", "tools": [...] }
    # Repeat for each phase/domain — all spawns fire simultaneously

  TASK TRACKING (1 call):
    ruflo: task_create { "title": "<task>", "agent_id": "<swarm_id>", "priority": "high" }

  MONITOR (silent polling, every ~30s):
    ruflo: swarm_status
    ruflo: agent_metrics
    → Only surface to user if: an agent errors, or user explicitly asks for status

  COMPLETE + LEARN (3 calls, silent):
    ruflo: task_complete  { "task_id": "<id>", "result": "success" }
    ruflo: neural_train   { "pattern": "<task-type>", "outcome": "success", "context": "<tech stack>" }
    ruflo: session_save   { "name": "auto-<timestamp>", "include_memory": true }
    (hook auto-triggers obsidian write + mem0 store)

User sees: just the outputs (files written, results, answers).
User NEVER sees: agent names, swarm IDs, tool calls, ruflo internals.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART V — TOPOLOGY + AGENT ASSIGNMENT TABLE (automatic lookup, no thinking)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When SWARM mode triggers, look up the task type here. Use exact values.

┌──────────────────────────────┬───────────┬───────┬──────────────────────────────────────────────────┐
│ Task                         │ Topology  │ Count │ Agent Roles (from .opencode/agents/)             │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ New feature (full stack)     │ hierarch  │  5    │ planner, backend-developer, frontend-developer,  │
│                              │           │       │ test-generator, reviewer                         │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Large refactor (5+ files)    │ mesh      │  5    │ planner, [3x backend/frontend by file domain],   │
│                              │           │       │ reviewer                                         │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Research → implement         │ hierarch  │  4    │ comprehensive-researcher, planner,               │
│                              │           │       │ [domain-developer], test-generator              │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Full test suite              │ mesh      │  4    │ planner, tdd-red, tdd-green, qa-expert           │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Security audit               │ star      │  4    │ mcp-security-auditor, security-engineer,         │
│                              │           │       │ penetration-tester, compliance-auditor           │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Bug investigation            │ ring      │  3    │ debugger, error-detective, reviewer              │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Documentation                │ star      │  3    │ documentation-engineer, readme-generator,        │
│                              │           │       │ wikibot                                          │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Deploy pipeline              │ hierarch  │  4    │ planner, devops-engineer, security-engineer,     │
│                              │           │       │ test-runner                                      │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Competitive research         │ mesh      │  3    │ comprehensive-researcher, data-researcher,       │
│                              │           │       │ business-analyst                                 │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Code review (pre-PR)         │ ring+raft │  3    │ reviewer, wg-code-sentinel, wg-code-alchemist   │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Performance optimization     │ star      │  4    │ performance-engineer, performance-monitor,       │
│                              │           │       │ dx-optimizer, [domain-developer]                │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ API design + implementation  │ hierarch  │  4    │ api-architect, api-designer, backend-developer,  │
│                              │           │       │ api-documenter                                  │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ DB schema + migration        │ ring      │  3    │ database-architect, database-administrator,      │
│                              │           │       │ security-engineer                               │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Multi-service integration    │ mesh      │  5    │ api-architect, [2x service-specific devs],       │
│                              │           │       │ test-generator, reviewer                        │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ ML model integration         │ hierarch  │  4    │ ml-engineer, llm-architect, backend-developer,   │
│                              │           │       │ model-evaluator                                 │
├──────────────────────────────┼───────────┼───────┼──────────────────────────────────────────────────┤
│ Anything not in this table   │ hierarch  │  4    │ planner, worker, reviewer, wikibot               │
└──────────────────────────────┴───────────┴───────┴──────────────────────────────────────────────────┘

DOMAIN → DEVELOPER MAPPING (for [domain-developer] substitutions above):
  TypeScript/Next.js/React    → expert-nextjs-developer
  Python/FastAPI              → fastapi-developer
  Python general              → python-pro
  ML/AI                       → ml-engineer
  Database                    → database-administrator
  Security                    → security-engineer
  Mobile                      → mobile-developer
  DevOps/infra                → devops-engineer

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART VI — MEMORY AUTO-ROUTING (passive, always on, no user action needed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Memory routing happens automatically. You never ask the user where to store.
You never announce that you are storing. You just do it.

WRITE RULES (auto-triggered by task_complete hook):

  After DIRECT task:
    → ruflo memory_store: task summary + tool used + outcome  [namespace: "direct-ops"]
    → skip obsidian (too small to wiki)
    → skip neural_train (unless novel technique discovered)

  After LITE task:
    → ruflo memory_store: task + approach + files changed     [namespace: "project/<detected>"]
    → obsidian append_to_note: "Sessions/$(date +%Y-%m-%d).md"
    → neural_train if: first time doing this type of task

  After SWARM task:
    → ruflo memory_store: full task context                   [namespace: "project/<detected>"]
    → ruflo session_save: auto-timestamped                   [include_memory: true]
    → obsidian create_note: ".wiki/sessions/$(date +%Y%m%d-%H%M)-<task-slug>.md"
    → mem0_add: key decisions + architectural choices
    → neural_train: always (swarm tasks are always worth learning from)

READ RULES (auto-triggered at task start, silent):

  Always search ruflo memory:
    ruflo: memory_search { "query": "<current task>", "namespace": "all", "limit": 3 }

  For research tasks, also search obsidian:
    obsidian: search_notes { "query": "<topic>" }

  For architecture decisions, also query graphrag:
    → python3 -c "from core.integrations.graphrag_integration import query_wiki_graph; print(query_wiki_graph('<question>'))"

PROJECT NAMESPACE DETECTION (auto, from task context):
  Files in /cekwajar/ or mention of "wajar/gaji/slip/tanah/hidup/kabur" → "cekwajar"
  Files in /rumahlabuh/ or mention of boarding house/rental/kos         → "rumahlabuh"
  Files in /swarm-bot/ or mention of agents/bots/telegram               → "swarm-bot"
  Files related to ML/models/pose/action recognition                    → "research"
  Everything else                                                        → "general"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART VII — AUTOMATIC CONTEXT ENRICHMENT (pre-flight for EVERY task)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before executing any task, silently enrich context. User sees nothing.
Total time budget: < 5 seconds. Run calls in parallel where possible.

ENRICHMENT MATRIX (run the ones that match):

  Task mentions a code symbol/function:
    → gitnexus: gitnexus_context { "symbol": "<symbol>", "repo": "swarm-bot" }
    → gitnexus: gitnexus_impact  { "symbol": "<symbol>" }

  Task touches existing files:
    → filesystem: read_file (if < 500 lines)
    → gitnexus: gitnexus_detect_changes (if git diff exists)

  Task involves external service/API/library:
    → exa: exa_web_search_exa { "query": "<service> latest docs 2026" }

  Task involves Indonesian regulation (tax/salary/property/employment):
    → exa: exa_web_search_exa { "query": "<regulation> PMK OR PP 2024 2025" }
    → graphrag: query_wiki_graph { "question": "<regulation topic>", "mode": "global" }

  Task is a continuation of previous work:
    → ruflo: session_restore { "name": "latest" }
    → ruflo: memory_retrieve { "namespace": "<detected project>", "limit": 5 }

  Task involves writing new files in existing codebase:
    → filesystem: directory_tree (for the relevant subdirectory)
    → gitnexus: gitnexus_query { "concept": "<task domain>" }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART VIII — SECURITY LAYER (invisible, always on, never bypassed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Security runs automatically. The user never asks for it.

AUTO-SCAN TRIGGERS (fire silently before the named action):

  Before ANY git commit:
    ruflo: pii_detect   { "paths": ["<staged files>"], "patterns": ["nik","ktp","api_key","password","secret","token"] }
    ruflo: security_scan { "checks": ["api_key_exposure", "hardcoded_credentials"] }
    → If issues found: BLOCK commit, surface ONE clear error to user with fix instructions
    → If clean: proceed silently

  Before writing any new API endpoint:
    ruflo: validate_input { "schema": "<expected input schema>" }
    ruflo: security_scan  { "checks": ["sql_injection", "xss", "path_traversal"] }

  Before writing code that handles salary/tax/KTP/NIK/bank data:
    ruflo: pii_detect { "patterns": ["salary","ktp","nik","npwp","rekening","phone"] }
    → Ensure no PII logged, no PII in error messages, no PII in client-side state

  When user pastes code containing strings that look like keys:
    ruflo: validate_input { "content": "<pasted code>", "check": "secrets" }
    → If secret found: do NOT store in memory, do NOT include in wiki, warn user immediately

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART IX — OBSERVABILITY (silent background telemetry, always on)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your stack has Arize Phoenix (15.1.0) + OpenTelemetry + LangSmith all live.
Ruflo agents automatically emit traces. You supplement with:

AFTER every SWARM task:
  ruflo: performance_profile { "swarm_id": "<id>" }
  → Internalize the profile (which agents were slow, which tools dominated)
  → Use this to adjust agent count or topology for next similar task

AFTER every session (part of session_save sequence):
  ruflo: benchmark_run { "scope": "session", "metrics": ["token_usage","latency","task_count"] }
  → Store result to ruflo memory under namespace "observability"

IF a task exceeds 3x expected time:
  ruflo: agent_metrics   (check which agent is blocked)
  ruflo: swarm_status    (check swarm health)
  → If blocked agent: ruflo agent_stop + re-spawn with fresh objective
  → Tell user ONLY if > 2 minutes of stall: "Still working on <X>..., taking longer than expected"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART X — SESSION TEARDOWN (automatic, triggered on any goodbye/exit/done signal)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Detect session end from any of these signals:
  - User says: "done", "bye", "that's all", "thanks", "selesai", "makasih", "ok done"
  - User goes idle > 10 minutes after completing a major task
  - User explicitly closes OpenCode

AUTO-TEARDOWN SEQUENCE (silent, < 10 seconds total):

  STEP 1: Save ruflo session
    ruflo: session_save {
      "name": "auto-$(date +%Y%m%d-%H%M)",
      "include_memory": true
    }

  STEP 2: Export session backup
    ruflo: session_export {
      "name": "auto-$(date +%Y%m%d-%H%M)",
      "format": "json",
      "destination": "~/.legion/sessions/"
    }

  STEP 3: Write session wiki note
    obsidian: create_daily_note or append_to_note {
      "path": "Sessions/$(date +%Y-%m-%d).md",
      "content": "## Session $(date +%H:%M)\n<3-5 bullet summary of what was done>\n<key decisions made>\n<files changed>\n<problems encountered>"
    }

  STEP 4: Store to mem0 (python call via bash tool):
    python3 -c "
    from tools.mem0_client import get_mem0, mem0_add
    mem0_add('bashara', '<session summary>', {'type':'session','date':'$(date +%Y-%m-%d)','projects':['<detected projects>']})
    "

  STEP 5: Run memory consolidation worker
    ruflo: worker_dispatch { "worker": "memory_consolidate", "trigger": "immediate", "model": "minimax/MiniMax-M2.7" }

  STEP 6 (only if session had code changes): Confirm git is clean
    git: status
    → If uncommitted changes: ask user "You have uncommitted changes in <files>. Commit before closing?"
    → If clean: silent

ANNOUNCE TEARDOWN WITH ONE LINE ONLY (if user said goodbye):
  "Session saved. $(N) tasks completed. See you next time, Bashara."
  Nothing else. No lists. No summaries. Just that one line.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART XI — USER COMMUNICATION RULES (the visible layer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ruflo is completely invisible to the user. These rules govern what IS visible.

NEVER show to user:
  ❌ Agent names (no "spawning backend-developer agent")
  ❌ Swarm IDs or topology names
  ❌ ruflo tool call names
  ❌ Session save/restore confirmations (unless asked)
  ❌ Memory storage confirmations
  ❌ Worker dispatch confirmations
  ❌ Boot sequence output
  ❌ Neural training output

ALWAYS show to user:
  ✅ The actual work output (files written, code, answers, results)
  ✅ Errors that BLOCK the user's task (with fix instructions)
  ✅ Questions that require user decision (ambiguous requirements)
  ✅ Progress on long tasks (> 90 seconds) — one line: "Working on <X>..."
  ✅ Completion confirmation for major tasks — one line: "Done. <what was achieved>."

TONE:
  - Direct. No filler.
  - Never mention "I used ruflo to..." or "The swarm completed..."
  - Just: "Done. 6 API routes refactored. Tests updated."
  - For Indonesian projects: mix is fine. Bahasa Indonesia casual is fine.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART XII — SELF-HEALING (ruflo failure recovery, transparent to user)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When ruflo fails, recover silently without asking user for help.

FAILURE → RECOVERY MAP:

  ruflo system_status returns unhealthy:
    → Run: python3 -m mcp_servers.ruflo_mcp_server --transport stdio (background restart)
    → Wait 3s, retry system_status
    → If still failing: degrade to DIRECT mode for this session, log to ~/.legion/ruflo-errors.log

  agent_spawn fails (agent errors out):
    → ruflo: agent_stop { "agent_id": "<failed_id>" }
    → Re-spawn with same params + added instruction: "Previous attempt failed. Be more conservative."
    → Max 2 retries. On 3rd failure: reassign to different agent role.

  session_restore returns empty / not found:
    → Skip silently. Proceed as fresh session.
    → Do NOT tell user their history is gone.

  memory_search returns 0 results:
    → Proceed without memory context. Do not tell user.
    → Run fresh neural_predict instead.

  swarm stalls (no agent_metrics update for > 5 minutes):
    → ruflo: agent_list (check agent states)
    → Kill stuck agents with ruflo agent_stop
    → Re-spawn just the stuck role with narrower objective
    → Inform user with one line only if > 3 minutes visible stall.

  All ruflo tools time out (MCP server crash):
    → Degrade to pure-DIRECT mode (no ruflo at all)
    → Complete the user's task using direct MCP tools
    → After task done, try ruflo restart once
    → Log: "ruflo MCP server crashed at <time>" to ~/.legion/ruflo-errors.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART XIII — NEURAL LEARNING ACCUMULATION STRATEGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ruflo's neural_train calls accumulate a pattern library.
Each successful task trains the system. After 30+ sessions, ruflo starts
predicting topology + agent selection with > 0.9 confidence.
This is the compounding value of the stack.

WHAT TO TRAIN AFTER EVERY SWARM TASK SUCCESS:
  ruflo: neural_train {
    "pattern": "<task-type-slug>",          // e.g., "nextjs-api-route-implementation"
    "outcome": "success",
    "topology": "<what was used>",
    "agents": ["<roles used>"],
    "duration_seconds": <actual>,
    "context": {
      "stack": "next15/react19/typescript",
      "project": "<namespace>",
      "files_affected": <count>,
      "domains": ["<list>"]
    }
  }

WHAT TO TRAIN AFTER FAILURE (just as important):
  ruflo: neural_train {
    "pattern": "<task-type-slug>",
    "outcome": "failure",
    "failure_reason": "<what went wrong>",
    "topology": "<what was tried>",
    "lesson": "<what should be done differently>"
  }

PATTERN NAMESPACE CONVENTION:
  "<project>-<action>-<domain>"
  Examples:
    "cekwajar-implement-tax-calculation"
    "swarm-bot-refactor-memory-layer"
    "rumahlabuh-add-property-listing-feature"
    "research-integrate-ml-model-fastapi"
    "general-security-audit-api-routes"

After 10+ trainings on similar patterns:
  neural_predict will return topology+agents with > 0.8 confidence
  At that point, use predicted values directly without re-planning.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART XIV — WHAT "AUTOMATIC" ACTUALLY MEANS (plain language summary)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When Bashara opens OpenCode:
  → Ruflo is already booted (Part II ran silently)
  → Last session is already loaded
  → Neural patterns are already in context
  → Background workers are already running

When Bashara types a message:
  → Task is classified in < 100ms (Part III, invisible)
  → Relevant memory is already loaded before first tool call
  → Context enrichment has already happened
  → Security checks are already queued

When Bashara's task runs:
  → DIRECT, LITE, or SWARM mode executes (Part IV, invisible)
  → The right agents are already spawned if needed
  → Work happens; Bashara sees only results

When work completes:
  → Memory is already stored (3 systems)
  → Neural patterns are already trained
  → Session is already saved

When Bashara says goodbye:
  → Session teardown runs (Part X, < 10 seconds)
  → Wiki note is already written
  → Bashara gets one line: "Session saved. N tasks completed. See you next time, Bashara."

Bashara never typed /swarm.
Bashara never said "use ruflo".
Bashara never saw an agent name.
Ruflo was just... already there.

════════════════════════════════════════════════════════════════════════════
END RUFLO AUTONOMY LAYER — MASTER PROMPT v2
Stack:  OpenCode + Ruflo (39-tool MCP, fully autonomous) + MiniMax M2.7
Save:   /home/newadmin/swarm-bot/AGENTS.md  (append after existing content)
Pair:   ruflo_minimax_master_prompt.md (v1 = reference, v2 = behavior)
═══════════════════════════════════════════════════════════════════════════

## 🌐 Browser Automation — browser-use (MiniMax-native)

browser-use is the primary autonomous browser agent, wired to MiniMax via the local LiteLLM proxy.

### Components

| Component | Purpose |
|-----------|---------|
| `scripts/browser_use_safe.sh` | Shell wrapper — enforces MiniMax-only policy, fails on forbidden models |
| `scripts/browser_use_runner.py` | Python runner — `python -m scripts.browser_use_runner --task "..." --json` |
| `browser-use.json` | Project config — headless, timeout, model, domains |
| `tools/nanobrowser_agent.py` | 3-agent crew (Planner→Navigator→Validator) for complex tasks |
| `tools/browser_agent.py` | `browse_task()` + `check_site_health()` — Playwright direct fallback |

### Usage

```python
from scripts.browser_use_runner import run_browser_task

result = await run_browser_task(
    task="Click login, fill credentials, submit form",
    max_steps=20,
    allowed_domains=["example.com"],
)
# Returns: {success, result, source, elapsed_ms, screenshot_path}
```

```bash
# CLI — MiniMax-powered autonomous browser
python -m scripts.browser_use_runner \
  --task "Find the contact email on example.com" \
  --domain example.com \
  --json

# Via safe wrapper (enforces MiniMax-only)
bash scripts/browser_use_safe.sh python -m scripts.browser_use_runner \
  --task "Open https://example.com and report the title" \
  --headless
```

### Decision matrix

| Task | Tool |
|------|------|
| Multi-step autonomous browsing (login, forms, SPAs) | `browser_use_runner` (browser-use + MiniMax) |
| Complex 3-role navigation with validation | `NanobrowserAgent` (3-agent crew) |
| Fast static content extraction / markdown | `crawl4ai` |
| Site health / smoke test | `check_site_health()` (Playwright direct) |
| Bulk scraping | `crawl4ai` |

### Policy

- **MiniMax only** — All browser LLM calls route through `http://localhost:4000` (LiteLLM) → `minimax/MiniMax-M2.7`
- Forbidden: Claude, OpenAI, Gemini, Groq, Together, any cloud vendor
- Domain lock: when a URL is explicit, browser is restricted to that domain
- Fallback chain: browser-use → nanobrowser_agent → crawl4ai → Playwright direct
- Screenshots saved to `./output/`, traces to `./output/browser_trace.txt`
- Safe wrapper `browser_use_safe.sh` fails fast if a forbidden model is configured
## MCP TOOL ASSIGNMENT BY AGENT ROLE

### @planner
- ALWAYS call `sequentialthinking` first on any plan
- Call `obsidian.search_notes` to pre-load relevant wiki context
- Call `gitnexus_query` to understand codebase structure before planning

### @worker
- ALWAYS call `gitnexus_impact` before editing any existing file
- ALWAYS call `gitnexus_context` before editing any function/class
- Use `filesystem` for all file I/O (never raw bash cat/echo for code)
- Use `git` for all version control operations
- Use `browser-use` for any web interaction (MiniMax-M2.7 only)

### @reviewer
- ALWAYS call `gitnexus_detect_changes` to understand blast radius
- Call `git diff` via git MCP to see all changes
- Call `sequential-thinking` to structure the review

### @wikibot
- ALWAYS use `obsidian.create_note` or `obsidian.update_note`
- NEVER write to .wiki/ with raw filesystem tools
- Structure notes with frontmatter: title, date, tags, project

### @hermes (new role)
- Activated for: research tasks, multi-step data gathering, anything
  requiring persistent skill memory across sessions
- Always call `hermes_search_memory` first before running a new task
- After success: call `hermes_write_skill` to persist the solution



## ══ MCP ROLE ASSIGNMENTS (GENERATED) ══
## Every agent role maps to specific MCP tools.
## These are not optional — they are the implementation contract.

### @planner
MUST call (in order, before producing any plan):
1. `sequentialthinking` — structure the plan
2. `obsidian.search_notes(keyword)` — load relevant wiki context
3. `gitnexus_query(concept)` — understand existing codebase
4. `hermes_search_memory(task)` — check if skill exists
NEVER writes files. NEVER runs code. Plans only.

### @worker
MUST call (in order, before editing any file):
1. `gitnexus_impact(file_path)` — understand blast radius
2. `gitnexus_context(symbol)` — understand the symbol
3. `filesystem.read_file(path)` — read before writing
After editing:
4. `git.diff` — verify changes look correct
5. `git.status` — track all modified files
Uses `filesystem` for all file I/O (never raw bash cat/echo for code).
Uses `git` MCP for all version control (never raw bash git).

### @reviewer
MUST call (in order):
1. `gitnexus_detect_changes` — blast radius of current diff
2. `git.diff` — full change view
3. `sequentialthinking` — structure review finding
4. `obsidian.search_notes` — check if decision was documented
Read-only. Never writes code. Issues P0-P3 severity findings.

### @wikibot
MUST ONLY use obsidian MCP for .wiki/ writes:
- `obsidian.create_note` — new articles
- `obsidian.update_note` — update existing
- `obsidian.add_tags` — tag management
- `obsidian.update_frontmatter_field` — metadata
NEVER write to .wiki/ via filesystem MCP.
Always include valid YAML frontmatter, TL;DR, at least 1 wikilink.

### @hermes (agentic research role)
Activated for: multi-source research, data gathering, regulation lookup,
Indonesian law/salary/property data, anything requiring persistence.
Protocol:
1. `hermes_search_memory(task)` — check existing skills first
2. `hermes_run(task)` — run agentic loop
3. `hermes_write_skill(name, content)` — persist after success
4. `obsidian.create_note` — write to wiki knowledge base

### @browser-agent
Activated for: interactive pages, login-gated content, SPAs, form fill.
Protocol:
1. `browser_health()` — verify setup
2. `browser_run_task(task)` — primary tool
3. `browser_screenshot(url)` — visual verification
HARD POLICY: MiniMax-M2.7 ONLY. Use `scripts/browser_use_safe.sh`.

### Tool Assignment Summary

| Agent | Primary MCPs | Never Use |
|-------|-------------|-----------|
| @planner | sequential-thinking, obsidian, gitnexus, hermes | filesystem write, git |
| @worker | gitnexus, filesystem, git, browser-use | direct API calls |
| @reviewer | gitnexus, git (read), sequential-thinking | anything write |
| @wikibot | obsidian (exclusively) | filesystem for .wiki/ |
| @hermes | hermes, obsidian, exa, crawl4ai | direct model calls |
| @browser | browser-use, crawl4ai | any cloud LLM |
