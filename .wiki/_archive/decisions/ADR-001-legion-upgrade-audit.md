# ADR-001: Legion Upgrade Audit — Jarvis-Level Transformation

**Date:** 2026-04-10  
**Agent:** Planner  
**Status:** IN PROGRESS — Phases 2-4 Complete, Phase 5 in progress

---

## 1. Project Overview

**What it is:** Legion (Bashara's personal AI companion) — a Python Telegram bot with multi-agent LLM orchestration, computer control, memory layers, and proactive intelligence.  

**What it needs to become:** Jarvis-level personal AI — proactive, soul-driven, context-aware, always online, aware of Bashara's schedule, business, and preferences.

---

## 2. Current State Audit

### 2.1 `llm_client.py` (1858 lines) — WORKING, needs MiniMax Primary
- **Current:** Uses `groq/llama-3.3-70b-versatile` as primary, falls back through Groq → Cerebras → ZAI → Gemini → OpenRouter
- **ZAI/MiniMax:** Already integrated (lines 430-437) via `https://open.bigmodel.cn/api/paas/v4` with `ZAI_API_KEY`
- **Problem:** MiniMax is NOT the primary — it's buried in fallback chain
- **Fix needed:** MiniMax `minimax-coding-plan/MiniMax-M2.7` → PRIMARY, retry logic for 429/high-load, Anthropic as true fallback
- **Environment:** `.env.example` has `MINIMAX_API_KEY` NOT listed — needs update

### 2.2 `core/soul_engine.py` (215 lines) — EXISTS, needs Enhancement
- **Current:** Reads SOUL.md on every prompt, manages beliefs.json, tracks follow-ups
- **Missing (Phase 3 requirements):**
  - No time-aware context injection (late night detection)
  - No emotional state driven by hour + conversation length
  - No mood momentum (last 3 short messages → more direct)
  - No banned phrase enforcement at generation time
  - No SOUL.md caching with 5-min refresh

### 2.3 Memory — MULTI-TIER EXISTS, needs Consolidation
- **Working (Tier 1):** `core/working_memory.py` — deque, last 20 exchanges
- **Episodic (Tier 2):** `tools/memory.py` (SQLite), `tools/open_memory.py`, `tools/memoryos_client.py`
- **Permanent (Tier 3):** `mem0ai`, `chromadb`, `core/memory/temporal_graph.py`
- **Problem:** 4+ memory systems active simultaneously — no unified interface
- **Fix needed:** `core/memory_engine.py` wrapping all three tiers with auto-summarize at 15k tokens

### 2.4 Intent Routing — EXISTS, needs LLM Classification
- **Current:** `core/intent_router.py` — 26 intents via regex patterns, sub-millisecond
- **Problem:** Pure keyword matching — not truly intelligent
- **Fix needed:** LLM-based classification for ambiguous cases, chain routing for multiple intents

### 2.5 `core/proactive/scheduler.py` — EXISTS, needs Enhancement
- **Current:** Background loop every 30 min, checks DB health, briefing at 8 AM
- **Missing:**
  - rumahlabuh.com ping + alert if slow/down (every 30 min)
  - GitHub trend watcher (Monday 9 AM)
  - Late night check (1 AM JST — warm/casual tone)
  - Morning brief at 8 AM JST with weather + unfinished tasks

### 2.6 `core/intent_router.py` + `skills/` — EXISTS
- Skills directory has 19 skill files (.md) — nextjs-engineer, supabase-engineer, etc.
- **Missing:** `skills/manifest.json` — no unified manifest

### 2.7 `main.py` (745 lines) — WORKING
- Startup sequence: 12 parallel tasks + 6 sequential groups
- Already has proactive scheduler, curiosity engine, GitHub intel, memory consolidation, briefing
- **Good foundation to build on**

### 2.8 Other Key Files
| File | Status | Notes |
|------|--------|-------|
| `router.py` (70 lines) | Working | Thin shim to agents.py |
| `agents.py` (138 lines) | Working | Re-exports from core.agent_registry |
| `core/agent_registry.py` (27793 lines) | Working | 76 agents, YAML-based |
| `core/autonomous_router.py` (15698 lines) | Working | ReAct-based routing |
| `core/intent_router.py` (366 lines) | Working | Pattern-based, needs LLM upgrade |
| `core/task_router.py` (15148 lines) | Working | Task orchestration |
| `task_orchestrator.py` (491 lines) | Working | Multi-step chains, monitors |
| `computer_agent.py` (79702 lines) | Working | Full desktop control |
| `core/self_upgrade.py` (18851 lines) | Working | Self-update capability |

---

## 3. Phase-by-Phase Breakdown

### PHASE 1: DEEP SCAN & AUDIT ✅ (this document)
- Audit complete — 276 tests passing
- No code changes needed

### PHASE 2: FIX API — MINIMAX AS PRIMARY ✅ COMPLETE
- **2.1** Add `MINIMAX_API_KEY` to `.env.example` ✅
- **2.2** Update `llm_client.py` — add MiniMax provider to `_get_api_key()` ✅
- **2.3** Set primary model to `minimax-coding-plan/MiniMax-M2.7` ✅
- **2.4** Add retry logic: 429 → wait 30s → retry 3x → fallback to Anthropic ✅
- **2.5** Update fallback chains in `config/departments.yaml` ✅

### PHASE 3: FIX THE SOUL ✅ COMPLETE
- **3.1** Create `core/soul_engine.py` enhancement — cache SOUL.md, 5-min refresh ✅ (rewritten)
- **3.2** Add dynamic time context (past 1AM JST → mention it's late) ✅
- **3.3** Add emotional state: FOCUSED/CURIOUS/TIRED/PLAYFUL based on hour + conv length ✅
- **3.4** Add mood momentum (last 3 short/curt → more direct responses) ✅
- **3.5** Create `core/memory_engine.py` — THREE tier wrapper ✅
- **3.6** Update `llm_client.py` to use enhanced soul_engine + memory_engine ✅ APPLIED

### PHASE 4: AUTONOMOUS SKILL SELECTION ✅ COMPLETE
- **4.1** Enhance `core/intent_router.py` — add LLM classification for ambiguous cases ✅
- **4.2** Create `skills/manifest.json` — all skills indexed with capabilities ✅
- **4.3** Update `core/skill_registry.py` to use manifest + LLM-based routing ✅

### PHASE 5: PROACTIVE INTELLIGENCE 🔄 IN PROGRESS
- **5.1** Enhance `core/proactive/scheduler.py` — rumahlabuh.com ping every 30 min ✅
- **5.2** Add GitHub trend watcher — Monday 9 AM JST digest ⏳ pending
- **5.3** Add late night check — 1 AM JST warm/casual tone ⏳ pending
- **5.4** Enhance morning brief — weather + unfinished tasks + Supabase health ⏳ pending

### PHASE 6: WEB SEARCH & REAL-TIME INTELLIGENCE ⏳ PENDING
- **6.1** Create `skills/web_search.py` — DuckDuckGo API + SerpAPI fallback ⏳
- **6.2** Create `skills/geo_intelligence.py` — travel/location queries ⏳
- **6.3** Wire into intent_router for RESEARCH intent ⏳

### PHASE 7: SELF-UPDATING CAPABILITY ⏳ PENDING
- **7.1** Enhance `core/self_upgrade.py` — weekly trending scan ⏳
- **7.2** Create `core/capability_audit.py` — monthly self-audit, gap report ⏳

### PHASE 8: BUSINESS INTELLIGENCE ⏳ PENDING
- **8.1** Enhance `tools/rumahlabuh_crew.py` — Supabase watcher, booking alerts ⏳
- **8.2** Create `skills/database_agent.py` — natural language → SQL ⏳

### PHASE 9: UPDATE WIKI & OPENCODE INTEGRATION ⏳ PENDING
- **9.1** Update `.wiki/MASTER-INTELLIGENCE.md` ⏳
- **9.2** Create AGENTS.md in core/, skills/, agents/, tools/, handlers/ ⏳

### PHASE 10: FINAL WIRING & SMOKE TEST ⏳ PENDING
- **10.1** Update requirements.txt — add chromadb, apscheduler, duckduckgo-search, aiofiles ⏳
- **10.2** Verify all imports ⏳
- **10.3** Run smoke test `pytest tests/ -x --asyncio-mode=auto -q` ⏳

---

## 4. Critical Risks

1. **Memory fragmentation** — 4+ memory systems causing context drift
2. **API rate limits** — MiniMax quota management not tested
3. **Startup latency** — 30s parallel timeout may be too tight for all features
4. **SOUL.md writes** — concurrent updates from multiple async tasks

---

## 5. Recommendations

1. **Do Phases 1-3 first** — foundation, no value in building on broken base
2. **Phase 3 memory_engine is critical** — consolidates 4 memory systems into one interface
3. **Test after each phase** — don't accumulate changes
4. **Keep SOUL.md writes serialized** — use asyncio.Lock for beliefs.json
5. **Monitor token usage** — MiniMax M2.7 has 16k context, need compaction at 12k

---

*Audit complete. Phase 1-4 complete, Phase 5 in progress. 276 tests passing.*