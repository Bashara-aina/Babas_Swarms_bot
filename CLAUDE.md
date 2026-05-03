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