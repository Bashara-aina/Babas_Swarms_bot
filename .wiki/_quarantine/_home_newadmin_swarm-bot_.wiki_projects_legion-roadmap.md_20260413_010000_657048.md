---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/projects/legion-roadmap.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.657068"
}
---

# Legion / Babas_Swarms_bot — Roadmap
Generated: April 11, 2026
Source: CLAUDE.md + ADR-001 + BASHARA-MASTER-PROFILE

---

## Project Vision
Legion is not an assistant — Legion is Bashara's permanent AI coworker.
Jarvis-level personal AI with: soul, long-term memory, proactive intelligence, autonomous skill selection.
Manages all of Bashara's businesses, thesis, research, and daily life without being asked explicitly.

---

## Current Version: v10 (April 10, 2026)
- Most recent commit: e074f45
- Soul + disagreement + SYSTEM_PROMPTS wired into llm_client.chat()
- SQLite conversation history + aiosqlite temporal graph
- Intent router + debate skill in autonomous flow
- Dead code removed

---

## Architecture
```
Babas_Swarms_bot/
├── main.py                      ← Telegram bot startup (DO NOT ADD LOGIC HERE)
├── agents.py                    ← Thin wrapper — re-exports from core/agent_registry.py
├── router.py                    ← Thin shim — re-exports from agents.py only
├── llm_client.py                ← chat(), agent_loop(), fallback chains — ALL LLM calls
├── computer_agent.py            ← Desktop control (screenshot, mouse, keyboard, shell)
├── task_orchestrator.py         ← Task chaining, swarm debate
├── SOUL.md                      ← Legion's living identity
├── data/beliefs.json           ← Structured beliefs for debate_engine.py
│
├── core/
│   ├── soul_engine.py          ← Reads SOUL.md, builds soul_context (v2: caching, emotional states)
│   ├── memory_engine.py        ← 3-tier: working + episodic + permanent
│   ├── intent_router.py         ← 23-intent LLM classifier (enhanced with LLM for ambiguous cases)
│   ├── skill_registry.py        ← manifest.json + LLM-based skill routing
│   ├── system_prompt_builder.py ← Assembles layered system prompt (SOUL first, always)
│   ├── emotion_modulator.py     ← Sentiment → emotion state
│   ├── debate_engine.py         ← Builds debate/opinion injection blocks
│   ├── proactive/scheduler.py   ← Morning brief, GitHub trends, rumahlabuh.com ping, late night
│   ├── self_upgrade.py          ← GitHub trending analysis, hot-reload, rollback
│   ├── capability_audit.py       ← Monthly self-audit with benchmark + gap analysis
│   └── conversation_interface.py ← Shared state (resolves circular imports)
│
├── handlers/                    ← 45+ aiogram routers (one per feature domain)
│   ├── ai.py                   ← /run /think /agent + NL catch-all
│   ├── admin_handlers.py        ← /budget /soul admin commands
│   ├── brain.py                 ← /memories /briefing /learn /instincts
│   ├── computer.py              ← /do /screen /click /type /key /cmd
│   └── system.py               ← /start /stats /keys /models /git
│
├── tools/
│   ├── supabase_client.py       ← Async Supabase REST client (PostgREST)
│   ├── rumahlabuh_crew.py       ← Booking alerts, overbooking detection
│   ├── n8n_bridge.py           ← n8n webhook listener (port 7835)
│   ├── browser_agent.py         ← Playwright + browser-use autonomous browsing
│   └── location_aware.py        ← Google Places + OpenWeatherMap
│
├── skills/
│   ├── manifest.json            ← All skills indexed (auto-discovered)
│   ├── web_search.py            ← DuckDuckGo + SerpAPI, async
│   ├── geo_intelligence.py      ← Restaurant/hotel/nearby recommendations
│   ├── database_agent.py         ← NL→SQL for Supabase (SELECT-only)
│   └── supabase-engineer.md     ← Skill file for Supabase operations
│
├── agents/                       ← 76+ specialized agents (YAML-based)
├── swarms_bot/                   ← Enterprise orchestration layer
└── config/
    ├── models.yaml               ← Provider registry + free model tiers
    ├── departments.yaml           ← 76 agents across 9 departments
    └── routing_keywords.yaml     ← 200+ keywords → agent mapping
```

---

## LLM Architecture
### Primary Model
- **MiniMax M2.7** via MiniMax Coding Plan Plus ($20/month)
- Context window: 200K
- Max output: 131K tokens
- Input: $0.30/1M, Output: $1.20/1M

### Fallback Chain
1. MiniMax M2.7 (primary)
2. Anthropic Claude Sonnet 4.6 ($20/month)
3. Gemini 2.0 Flash

### Model Assignments
| Agent | Model | Task |
|---|---|---|
| general | minimax | Reliable fallback |
| coding | groq/llama-3.3-70b | Code generation |
| researcher | groq/moonshotai/kimi-k2 | Academic research |
| debate | cerebras/qwen-3-235b | Opinion, dialectic |
| vision | ollama_chat/gemma4:e4b | Screenshot OCR (local) |

---

## Memory Architecture (6 tiers)
| Tier | Technology | Purpose | TTL |
|---|---|---|---|
| Working | In-process dict | Current session turns | Session |
| Episodic | SQLite (aiosqlite) | Recent conversations | 30 days |
| Semantic | mem0ai + ChromaDB | Vector semantic retrieval | Permanent |
| Graph | graphiti-core | Relationship knowledge graph | Permanent |
| Long-term | Letta | Hierarchical memory | Permanent |
| Core facts | memory_manager | Bashara's persistent profile | Permanent |

All writes go through `core/memory/memory_manager.py` facade.

---

## Proactive Scheduler Jobs
| Job | Schedule | Purpose |
|---|---|---|
| Morning brief | 07:00 JST | Weather + schedule + Supabase health |
| GitHub trend watcher | 10:00 JST | LLM-evaluated multi-topic digest |
| rumahlabuh.com ping | Every 30 min | Health check, alerting |
| Late night check | 22:00 JST | Soul-powered warm/casual tone |
| Memory consolidation | 02:00 JST | Cross-tier memory cleanup |
| Capability audit | Monthly | Self-audit with gap analysis |

---

## Skill Manifest (skills/manifest.json)
| Skill | Handler | Keywords |
|---|---|---|
| Web Search | WebSearch | search, lookup, research |
| Geo Intelligence | GeoIntelligence | restaurant, hotel, nearby |
| Screenpipe Recall | screenpipe_tool | screen, what's on screen |
| MiroFish Simulation | mirofish | simulate, forecast |
| Open Interpreter | interpreter_tool | run code, execute |
| Database Agent | DatabaseAgent | database, supabase, sql, schema |

---

## Known P0 Issues (from CLAUDE.md)
1. /debate command not registered in main.py
2. /cmd missing timeout guard (asyncio.wait_for missing)
3. ruflo process handle not stored (restart policy missing)
4. parse_mode inconsistency (bare Markdown → should be HTML)

---

## What "Done" Looks Like for Legion
From CLAUDE.md definition:
> When Bashara sends a message, does the response feel like it came from a trusted senior colleague who knows him, remembers the last conversation, has opinions, and genuinely cares about the quality of the answer?

---

## Consolidated from legion/roadmap.md on 2026-04-12

### 2026-04-11 — Audit Fixes Applied
| # | Fix | File | Severity |
|---|---|---|---|
| F1 | Duplicate admin_handlers.router removed | handlers/__init__.py | Critical |
| F2 | Graceful shutdown via on_shutdown handler | main.py | Warning |
| F3 | Fail-fast env validation for TELEGRAM_BOT_TOKEN + ALLOWED_USER_ID | main.py | Critical |
| F4 | Ollama bypass removed (all agents can use local fallbacks) | llm_client.py | Warning |
| F5 | MiniMax retry exponential backoff + jitter | llm_client.py | Warning |
| F6 | chunk_output() infinite loop guard added | llm_client.py | Critical |
| F7 | LEGACY_FALLBACK_CHAIN updated | core/agent_registry.py | Warning |

Full details: `legion/audit-2026-04-11-fixes.md`

### 2026-04-10 — 10 Phases Complete
| Phase | Status | Key Deliverables |
|---|---|---|
| Phase 1 | ✅ | Audit + ADR-001 (deep scan, architecture catalogued) |
| Phase 2 | ✅ | MiniMax as primary (retry logic, 16384 tokens, 3 retries) |
| Phase 3 | ✅ | Soul Engine + MemoryEngine + EmotionModulator |
| Phase 4 | ✅ | Autonomous skill selection (LLM-based intent routing) |
| Phase 5 | ✅ | Proactive scheduler (morning brief, GitHub trends, rumahlabuh ping, late night) |
| Phase 6 | ✅ | Web search (DuckDuckGo + SerpAPI fallback) |
| Phase 7 | ✅ | Self-updating (scan_weekly_trends, CapabilityAudit) |
| Phase 8 | ✅ | Business intelligence (booking alerts, DatabaseAgent) |
| Phase 9 | ✅ | Wiki + OpenCode integration (AGENTS.md in 5 dirs) |
| Phase 10 | ✅ | Final wiring (requirements.txt, import verification) |

---

## Related Wiki Files
- `.wiki/profiles/legion-soul.md` — Legion's personality
- `.wiki/profiles/BASHARA-MASTER-PROFILE.md` — tech setup + vision
- `.wiki/_archive/decisions/ADR-001-legion-upgrade-audit.md` — upgrade phases 1-10 (archived)
