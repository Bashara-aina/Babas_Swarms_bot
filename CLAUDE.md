# LEGION COGNITIVE OPERATING SYSTEM — CLAUDE.md (TRIMMED BY AUDIT v2)

**Original:** CLAUDE.md.cekwajar-backup (CEKWAJAR content removed)
**Reference:** .wiki/health/audit-2026-05-03-v2.md for full audit report
**Purpose:** Essential boot + routing rules only. Everything else → wiki.

## SESSION BOOT (runs automatically)
1. Read SOUL.md — identity
2. Read this file — routing + safety
3. Read /tmp/legion_*.txt — hot memory (session boot)
4. Call cognition_boot() — see core/cognition_boot.py
5. Call hermes_search_memory() + gitnexus_query()

**Context health:** 🟢<40% | 🟡40-60% | 🔴60-80% | 💀>80% → /compact

## MODELS
- Primary: minimax/MiniMax-M2.7 via http://localhost:4000
- Fallback: gemini/gemini-2.0-flash-exp:free → minimax/MiniMax-Text-01
- browser-use: MiniMax-M2.7 ONLY

## SAFETY RULES
- Verify before asserting (show proof)
- Same approach failing twice → STOP and report
- NEVER commit PII/secrets to wiki or memory
- NEVER hardcode API keys — always os.getenv()
- NEVER use time.sleep() — fully async project

## 5-TIER MEMORY PYRAMID
| Tier | Storage | TTL |
|------|---------|-----|
| T1 HOT | /tmp/legion_*.txt | session |
| T2 WORKING | memory_manager.py facade | conversation |
| T3 EPISODIC | SQLite (aiosqlite) | 30 days |
| T4 SEMANTIC | mem0 vector store | permanent |
| T5 STRUCTURAL | .wiki/ Obsidian | permanent |

## MCP ROUTING (always available, silent)
| Task | Tool |
|------|------|
| Code blast radius | gitnexus_impact |
| Multi-step reasoning | sequentialthinking |
| Did we do this before? | hermes_search_memory |
| Web research | exa_web_search_exa |
| Full page scrape | crawl4ai_crawl4ai_crawl |
| Autonomous browser | browser-use_browser_run_task |
| Wiki write | obsidian_create_note |
| Memory store | hermes_write_skill |
| Background jobs | ruflo_agent_spawn |

## SECURITY (never violate)
- ALWAYS check message.from_user.id == ALLOWED_USER_ID
- /cmd shell timeout: asyncio.wait_for(proc, timeout=30)
- subprocess.Popen for ruflo must store process handle
- Parse mode default: parse_mode='HTML' — escape < > &

## LLM CALLS (all go through llm_client.py)
- Model format: provider/model (e.g., minimax/MiniMax-M2.7)
- Ollama (ollama_chat/...) is vision ONLY — never text/coding
- Responses > 4000 chars: chunk before sending to Telegram

## ASYNC RULES
- NEVER time.sleep() — use asyncio.sleep()
- NEVER threading — fully async project
- All DB: aiosqlite — never sync sqlite3
- Background tasks: asyncio.create_task() with try/except

## SELF-EVOLUTION (run after any failure)
```python
from core.self_evolution import get_self_evolution_engine
engine = get_self_evolution_engine('/home/newadmin/swarm-bot')
await engine.record_failure(task='...', approach='...', failure_mode='...', fix='...')
```

## ANTIPATTERNS (never do)
- NEVER skip gitnexus before editing code
- NEVER call browser-use AND crawl4ai for same URL
- NEVER write to obsidian via filesystem MCP
- NEVER call hermes for code execution
- NEVER use ruflo for LLM calls
- NEVER call exa AND firecrawl for same research query

## FILES TO ALWAYS VERIFY
| File | Purpose |
|------|---------|
| core/soul_engine.py | SOUL.md → soul_context |
| core/intent_router.py | 23-intent classifier |
| core/system_prompt_builder.py | Layered prompt assembly |
| core/memory/memory_manager.py | All memory writes via facade |
| handlers/shared.py | _shared.require_owner() |

## TESTING (after any change)
```bash
python -c 'from core.soul_engine import build_soul_context; print(build_soul_context()[:100])'
python -c 'from core.intent_router import IntentRouter; print(IntentRouter().route_sync("hello"))'
pytest tests/ -x --asyncio-mode=auto -q
```

## DEFINITION OF DONE
1. Smoke tests pass
2. Pytest passes — no regressions
3. 0 new broken wikilinks (run wiki_health.py)
4. SOUL.md updated if Legion learned something new
5. Wiki updated for architectural changes
6. compile_state.json updated

## REFERENCE (moved to wiki — load on demand)
Full architecture map → .wiki/architecture/legion-module-map.md
Full agent roster → .wiki/agents/ (76 specialized agents)
Full memory spec → .wiki/concepts/memory-architecture.md
Full env vars → .wiki/operations/environment-variables.md
CEKWAJAR content → CLAUDE.md.cekwajar-backup (DO NOT load into context)
Full rules → .wiki/health/audit-2026-05-03-v2.md

---

## Octogent Orchestration Layer

This repo uses Octogent for multi-session coordination.
Dashboard: http://localhost:8788 (start with ./scripts/start_octogent.sh)

### Tentacle → Context mapping

| Tentacle ID    | Scope                              | Workdir             |
|----------------|------------------------------------|---------------------|
| legion-core    | Bot engine, swarms, scheduler      | ./                  |
| mirofish       | Market intel, MiroFish bridge      | ./                  |
| cekwajar       | Indonesian salary/tax SaaS tools   | ~/cekwajar          |
| rumahlabuh     | Rental platform Solo               | ~/rumahlabuh        |
| research       | Academic CV research, PyTorch      | ~/research          |
| popw           | POPW project                      | ~/popw              |

### Agent routing rules

- Task touches tools/, bot.py, scheduler → use legion-core tentacle
- Task touches tools/market_intel.py or MiroFish → use mirofish tentacle
- Task touches Cekwajar suite (Wajar*) → use cekwajar tentacle
- Task touches Rumahlabuh or real estate → use rumahlabuh tentacle
- Task touches ML models, training, paper → use research tentacle

### Inter-agent communication

When an OpenCode session needs to delegate to another session:
  octogent channel send <target-terminal-id> "message"
  octogent channel list <terminal-id>

Durable handoffs (survive restarts): write to tentacle markdown files.
In-flight messages (in-memory only): use channel send.

### Spawning child agents from todos

From the Octogent UI (Deck), click any todo checkbox item → "Solve with Agent"
to spawn a child OpenCode terminal scoped to that todo item. The child receives:
  - tentacle CONTEXT.md as system context
  - the specific todo item as its task
  - worktree mode (isolated git branch) or shared mode

Max 9 child agents per parent. Overflow items are deferred in todo order.

---

## INFINITE MEMORY (no compaction — additive only)

This stack implements infinite memory without compaction. Memory only grows.

### Session Lifecycle

```
.start_session_watcher.sh → work → /memory → work → .stop_session_watcher.sh
```

- **Before work**: `/memory <query>` — queries 4-layer recall engine → writes `.session_state/recalled_context.md`
- **During work**: `session_watcher` daemon polls `.session_state/` every 30s, saves to mem0+langmem every 2 min
- **After work**: `.stop_session_watcher.sh` sends STOP_SIGNAL → final checkpoint + save

### Memory Layers (recall order)

| Layer | Source | Notes |
|-------|--------|-------|
| 1 | `.session_state/checkpoints/` | Timestamp-named snapshots of full session state |
| 2 | mem0 (ChromaDB + Ollama) | Vector search via `tools.mem0_client` |
| 3 | langmem | `core.integrations.langmem_integration.SwarmBotMemoryManager` |
| 4 | graphrag | `core.integrations.graphrag_integration.query_wiki_graph` |

### Key Files

- `core/memory/session_watcher.py` — daemon; writes PID to `.session_state/watcher.pid`
- `core/memory/memory_injector.py` — `build_memory_context(query, user_id)` for /memory command
- `.opencode/command/memory.md` — `/memory` slash command definition
- `scripts/start_session_watcher.sh` / `scripts/stop_session_watcher.sh` — lifecycle scripts

### LiteLLM Callback Bridge

`core/memory/litellm_callbacks.py` bridges every LLM call to `.session_state/current.json` via `_bridge_to_session_state()`. This lets session_watcher track LLM activity without parsing logs.