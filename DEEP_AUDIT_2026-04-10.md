# LEGION DEEP AUDIT — April 10, 2026

## Executive Summary

**Why does Legion feel robotic, soulless, and empty?**

Legion has an impressive codebase with 2600+ files, 76 defined agents, 6-tier memory, personality engines, debate systems, soul files, and proactive behaviors. But the bot feels dead because **most of these systems are not actually wired together in the live message path**. The architecture is a collection of powerful modules that exist in isolation — like having a Ferrari engine, luxury seats, and premium speakers all sitting in separate boxes instead of being assembled into a car.

**The core problem is not routing. It's integration.**

---

## Table of Contents

1. [Architecture Diagnosis: Why It Feels Dead](#1-architecture-diagnosis)
2. [Critical Wiring Failures (P0)](#2-critical-wiring-failures)
3. [Soul & Personality System Audit](#3-soul--personality-system)
4. [Memory System Audit](#4-memory-system)
5. [Intent & Routing Audit](#5-intent--routing)
6. [LLM Client Audit](#6-llm-client)
7. [Handler Audit](#7-handler-audit)
8. [Tools & Integration Audit](#8-tools--integration)
9. [Config & Registry Audit](#9-config--registry)
10. [Proactive Behavior Audit](#10-proactive-behavior)
11. [Missing Features for Your Dream Assistant](#11-missing-features)
12. [Dead Code & Orphans](#12-dead-code--orphans)
13. [Priority Fix Order](#13-priority-fix-order)

---

## 1. Architecture Diagnosis

### Why Legion Feels Like a Robot Instead of Jarvis

**Root Cause Analysis:**

| Problem | Why It Happens | Impact |
|---------|---------------|--------|
| **Soul is buried, not leading** | `build_base_persona()` comes first in `chat()`, soul is nested inside `SystemPromptBuilder.build()` which comes 5th+ in the prompt | LLM treats persona as primary identity, soul as secondary context |
| **Disagreement protocol is disconnected** | `get_disagreement_prompt()` is only used in `build_full_system_prompt()` which `chat()` NEVER calls | Legion can never push back, debate, or disagree — it's always a yes-man |
| **PERSONALITY_WRAPPER is orphaned** | Defined in `agents.py` (80+ lines of rich personality), but `chat()` uses `build_base_persona()` instead | The most detailed personality spec is literally unused in live chat |
| **Intent router doesn't route** | `classify_intent_fast` adds a "hint" into the system prompt — it doesn't actually route to different handlers | All messages go through the same generic handler regardless of intent |
| **76 agents exist in YAML but are never loaded** | `config/departments.yaml` has 76 specialized agents; `load_registry()` is only called on SIGHUP, not at startup | The enterprise agent roster is a dead config file |
| **Two parallel systems compete** | `agents.py` keyword routing vs `config/routing_keywords.yaml` + `nexus_orchestrator` — neither is complete | Confused routing, neither system gets all messages |
| **Memory writes are inconsistent** | `MemoryManager` facade exists but `chat()` also writes to mem0, Letta, MemoryOS, episodic store directly | Memory drift, some conversations remembered, others lost |
| **Emotion is calculated but barely used** | `emotion_modulator.py` runs but its output is one small line in the system prompt | No emotional depth, no mood persistence, no affect on response style |
| **Proactive features are budget-gated to death** | `MAX_PROACTIVE_PER_DAY=3` + budget checks → curiosity engine barely fires | Legion never initiates conversation, never surprises you |
| **No automatic skill selection** | User must use `/command` for specific features — no autonomous "I should research this" or "I should check your email" | Legion waits passively instead of acting like Jarvis |

### The Message Flow Problem (Visual)

What SHOULD happen:
```
User Message → Intent Classification → Skill Auto-Selection → Context Assembly
    → Soul (identity) + Personality (voice) + Emotion (mood) + Memory (history)
    → Disagreement Check → Research if needed → LLM Call → Character Enforcement
    → Memory Write → Proactive Follow-up Check → Response
```

What ACTUALLY happens:
```
User Message → F.text catch-all → AutonomousRouter (basic keyword match)
    → chat(task) → build_base_persona() (generic) + maybe SystemPromptBuilder
    → LLM Call → basic character enforcement → Response
```

**Missing in the actual flow:**
- No real intent classification driving behavior
- No automatic skill/tool selection
- No disagreement injection
- No research-before-answering
- No proactive follow-up scheduling
- Soul is buried under other prompt layers
- PERSONALITY_WRAPPER completely unused
- Emotion barely affects anything

---

## 2. Critical Wiring Failures

### P0-1: `chat()` Discards SYSTEM_PROMPTS

**File:** `llm_client.py` lines 987–993 and 1296

**Problem:** `chat()` sets `system_prompt = SYSTEM_PROMPTS.get(agent_key)` at line 987, then at line 1296 it **replaces** `system_prompt` with `"\n\n".join(prompt_sections)`. The per-agent role prompts (coding, debug, architect, etc.) are **thrown away**. The local-Ollama bypass note is also dropped.

**Impact:** Agents lose their specialized instructions. A coding agent responds the same as a research agent because the role-specific system prompt is discarded.

**Fix:** Push `SYSTEM_PROMPTS[agent_key]` into `prompt_sections` as one of the sections (probably via `build_mode_instructions()` which is already called — verify it covers all agent keys).

### P0-2: Disagreement Protocol Disconnected

**File:** `core/character/disagreement_protocol.py`

**Problem:** `get_disagreement_prompt()` returns a rich set of rules for when/how Legion should push back. But it's only called from `build_full_system_prompt()` in `core/system_prompt_builder.py`. `chat()` in `llm_client.py` **never calls `build_full_system_prompt()`** — it uses `SystemPromptBuilder.build()` + manual section assembly instead.

**Impact:** Legion never pushes back. It's always a yes-man. This is the single biggest reason it feels empty — it has no spine.

**Fix:** Add `get_disagreement_prompt()` to `prompt_sections` in `chat()`, or inject it inside `SystemPromptBuilder.build()`.

### P0-3: PERSONALITY_WRAPPER Not Used in Live Chat

**File:** `agents.py` lines 34–117

**Problem:** `PERSONALITY_WRAPPER` is 80+ lines of rich personality definition (identity, tone, language matching, memory behavior, quality standards). It's used in `build_system_prompt()` which is a separate function. But `chat()` uses `build_base_persona()` from `core/character/persona.py` instead, which loads from `legion_character.json`.

**Impact:** The most detailed personality specification is completely bypassed in the main chat path.

**Fix:** Either (a) make `chat()` use `build_system_prompt()` as its base, or (b) merge `PERSONALITY_WRAPPER` content into `build_base_persona()` / `legion_character.json`, or (c) add `PERSONALITY_WRAPPER` as a section in `prompt_sections`.

### P0-4: Soul is Buried, Not Leading

**File:** `llm_client.py` `chat()` function

**Problem:** The prompt assembly order in `chat()` is:
1. `build_base_persona()` ← comes first
2. emotion modulation
3. relationship memory
4. working memory
5. cognition fragment
6. intent hint
7. `SystemPromptBuilder.build()` ← soul is here, inside this block
8. ... many more sections ...

SOUL.md content ends up 5+ sections deep. LLMs weight early content more heavily. Soul should be FIRST.

**Impact:** Legion's identity is treated as supplementary context rather than its core being.

**Fix:** Move `build_soul_context()` to be `prompt_sections[0]`, before `build_base_persona()`.

### P0-5: `/debate` Handler is Broken at Runtime

**File:** `handlers/debate_handlers.py`

**Problem:** Calls `chat(messages=[...], system=...)` but `chat()`'s signature is `chat(task: str, agent_key=..., ...)`. `messages` and `system` are not valid parameters. This will raise `TypeError` at runtime.

**Impact:** `/debate` and `/opinion` commands crash when used.

**Fix:** Rewrite the debate handler to use the correct `chat()` signature: `chat(task=..., agent_key="debate", ...)`.

### P0-6: 76 YAML Agents Never Loaded at Startup

**File:** `core/agent_registry.py`, `config/departments.yaml`

**Problem:** `load_registry()` which loads the 76-agent YAML is only called from `reload_from_yaml()` which is triggered by SIGHUP signal. There is no call at startup in `main.py` or module import time.

**Impact:** The entire enterprise agent roster (76 specialized agents across 9 departments) is a dead config file. Routing only uses the ~12 hardcoded agents in `agents.py`.

**Fix:** Call `load_registry()` during `on_startup()` in `main.py`.

---

## 3. Soul & Personality System

### SOUL.md
- **Status:** Exists, ~48 lines, loaded by `core/soul_engine.py`
- **Content:** Identity, values, relationship with Bashara, opinions, proactive behaviors, growth rules
- **Problem:** It's good but **too short** for the depth of personality you want. A real "friend" would have:
  - Detailed knowledge of Bashara's preferences, habits, schedule
  - Opinions on specific topics (not just meta-opinions about having opinions)
  - Communication style preferences per context
  - Inside jokes, shared references
  - Personal growth journal entries over time

### data/beliefs.json
- **Status:** Exists, has stances on topics, `bashara_facts`, `things_to_follow_up`
- **Problem:** Underutilized — only debate engine and curiosity engine read it. Should be central to ALL responses.

### Personality Layers (the mess)
There are **5 separate personality systems** that partially overlap:

| System | File | Used in chat()? |
|--------|------|-----------------|
| `PERSONALITY_WRAPPER` | `agents.py` | **NO** — orphaned |
| `build_base_persona()` | `core/character/persona.py` | YES — first section |
| `LEGION_PERSONALITY` dataclass | `core/personality/personality.py` | Partial — via SystemPromptBuilder |
| `legion_character.json` | loaded by persona.py | YES — but file may be thin |
| `letta_personality` state | `tools/letta_personality.py` | YES — local JSON persona block |

**Recommendation:** Consolidate into ONE authoritative personality source that feeds ALL paths.

### Character Enforcement
- `character_voice.py` — Adds opinion/humor injection. **Used** in `chat()`. Works.
- `character_enforcer.py` — Post-processes responses to remove sycophantic openers. **Used** in `chat()`. Works.
- **Gap:** Enforcement is reactive (cleaning bad output) not proactive (ensuring rich personality from the start). If the system prompt doesn't inject personality deeply, enforcement can't save it.

---

## 4. Memory System

### Architecture (6 tiers documented, reality differs)

| Tier | Documented | Actual Status |
|------|-----------|---------------|
| **Working Memory** | In-process dict per session | `core/working_memory.py` — **Exists, env-gated** (`LEGION_WORKING_MEMORY_ENABLED`) |
| **Episodic** | SQLite (aiosqlite) | `core/memory/episodic_store.py` — **Exists, Supabase primary + JSON fallback** |
| **Semantic (mem0)** | mem0ai + ChromaDB | `core/memory_manager.py` (LegionSemanticMemory) — **Exists** |
| **Core Facts** | memory_manager facade | `core/memory/memory_manager.py` (MemoryManager) — **Exists, tiered** |
| **Graph** | graphiti-core | `core/memory/temporal_graph.py` — **Exists but uses SYNC sqlite3** (violation of async rule) |
| **Long-term (Letta)** | Letta service | `tools/letta_personality.py` — **LOCAL JSON FILE, not Letta server** |

### Critical Memory Problems

1. **Two MemoryManagers**: `core/memory/memory_manager.py` (MemoryManager) and `core/memory_manager.py` (LegionSemanticMemory) — confusing, writes may go to one and not the other
2. **Direct writes in `chat()`**: Despite the facade, `chat()` makes direct calls to mem0, Letta, MemoryOS, episodic store separately — bypassing the facade
3. **No long-term memory**: Letta is supposed to be long-term but it's just a local JSON file at `~/.legion/persona_state.json`
4. **temporal_graph.py uses sync sqlite3**: Breaks the project's async rule, could block the event loop
5. **Episodic store Supabase dependency**: Falls back to local JSON when Supabase isn't configured — means no cross-session memory on a fresh install without Supabase
6. **MemoryOS/OpenMemory**: Both are initialized in `on_startup` but may not be functional without additional setup

### Why Memory Makes It Feel Dumb

- **Conversation history is RAM-only**: `CONVERSATION_HISTORY` in `agents.py` is a plain dict — it's lost on restart
- **No automatic fact extraction**: When you tell Legion something ("I'm going to Tokyo next week"), nothing automatically extracts and stores this fact
- **No memory retrieval before answering**: Legion doesn't check "what do I know about this topic/person/event" before responding
- **No temporal awareness**: Legion doesn't know "Bashara told me about X 3 days ago" or "this is a follow-up to our conversation about Y"

---

## 5. Intent & Routing

### What Exists

- `core/intent_router.py` — `classify_intent_fast()` with regex-based intent detection for ~20 intents
- `classify_intent_llm()` — exists but **NEVER CALLED** (dead code)
- `agents.py` — `detect_agent()` with keyword-based routing to ~12 agent keys
- `config/routing_keywords.yaml` — 200+ keywords → agent mapping (used by `nexus_orchestrator`)
- `core/nexus_orchestrator.py` — layer-based routing (not in main message path)
- `message_handler.py` — `AutonomousRouter` for NL messages

### The Problem

**There is no unified routing system.** Instead there are 4+ partial routing mechanisms:

1. `classify_intent_fast` → adds a hint to the prompt (doesn't route)
2. `detect_agent()` → selects model/fallback chain based on keywords
3. `AutonomousRouter` → basic task categorization
4. `nexus_orchestrator` → layered routing (mostly unused in main path)

**None of them actually change behavior.** Whether you ask Legion to code, research, debate, or tell a joke, it goes through nearly the same `chat()` path with the same prompt assembly. The only difference is which LLM model is selected.

### What Should Happen

Intent classification should:
1. Detect WHAT the user wants (code, research, chat, debate, help, tool use, etc.)
2. Select the RIGHT HANDLER (not just model, but behavior)
3. Determine if TOOLS are needed (browser, email, shell, etc.)
4. Decide if RESEARCH is needed before answering
5. Choose the appropriate RESPONSE STYLE (technical, casual, debate, etc.)
6. Auto-select SKILLS without requiring slash commands

---

## 6. LLM Client

### `chat()` Function (the heart of everything)

**Status:** Massive function (~400 lines) that does too many things. It works, but:

1. **Prompt assembly is fragile**: 30+ optional sections added via try/except, any failure silently skips the section
2. **Soul ordering is wrong**: Soul should be first but it's buried in the middle
3. **SYSTEM_PROMPTS are discarded**: Per-agent role prompts set at line 987 are overwritten at line 1296
4. **No structured output support**: Everything is free-text completion
5. **No tool calling in chat()**: Only `agent_loop()` has tool support; regular `chat()` is pure text

### `agent_loop()` (tool-using computer agent)

**Status:** Works for `/do`, `/cmd` commands. Has tool calling loop, rate limit handling, Groq XML recovery.

**Problem:** Uses a completely different prompt stack than `chat()`:
- Only `SYSTEM_PROMPTS["computer"]` + optional conversation summary
- NO soul, NO personality, NO emotion, NO memory
- So when Legion controls your computer, it has zero personality

### Model Selection

- Primary models defined in `agents.py` `AGENT_MODELS`
- Fallback chains in `FALLBACK_CHAIN`
- `general` agent defaults to `ollama_chat/gemma4:e4b` (local)
- **Issue**: Default to local Ollama for general chat might cause slow/low-quality responses if the local model isn't great. Cloud-first is documented but `AGENT_MODELS["general"]` points to local.

---

## 7. Handler Audit

### Handler Registration

All routers are registered via `handlers/__init__.py` `register_all_routers()`. Order matters — `ai.router` is LAST (catch-all for plain text).

### Critical Issues

| Handler | Issue |
|---------|-------|
| `debate_handlers.py` | **BROKEN**: Wrong `chat()` call signature — will crash at runtime |
| `basic.py` | **DOESN'T EXIST**: CLAUDE.md says it does. `/start`, `/help` are in `system.py` |
| `llm_handlers.py` | **DOESN'T EXIST**: CLAUDE.md says it does. `/run`, `/agent` are in `ai.py` |
| `memory_handlers.py` | **DOESN'T EXIST**: Memory commands split between `memory_commands.py` and `brain.py` |
| `brain.py` | **DUPLICATE COMMANDS**: Defines `/remember`, `/recall`, `/forget` which are also in `memory_commands.py` — `brain.py` commands are shadowed |
| `streaming.py` | **NOT WIRED**: Not included in `register_all_routers` — dead code |
| `/debate`, `/opinion` | **NOT IN COMMAND MENU**: Missing from `set_my_commands` in `main.py` |

### Missing Handlers for Your Vision

- **No auto-skill handler**: No handler that autonomously decides to use a tool/skill
- **No proactive conversation handler**: No handler for Legion-initiated messages based on context
- **No multi-step task handler**: No handler for "research this topic, then summarize, then email me"
- **No WhatsApp reading handler**: `/whatsapp` exists but auto-reading incoming WhatsApp doesn't
- **No email auto-reply handler**: Can read emails but no smart auto-reply capability
- **No scheduling handler**: No "remind me at 3pm" or "check this daily"
- **No recommendation handler**: No smart restaurant/hotel/location recommendations

---

## 8. Tools & Integration

### What Exists vs What Works

| Tool | File | Connected? | Working? |
|------|------|-----------|----------|
| Composio (email/calendar) | `tools/composio_hub.py` | YES | Needs API key + OAuth |
| Browser Automation | `tools/browser_agent.py` | `check_site_health` YES, `browse_task` **ORPHAN** | Partial |
| Location/Places | `tools/location_aware.py` | **MOSTLY ORPHAN** — handler uses `location_advisor` instead | Partial |
| n8n Workflows | `tools/n8n_bridge.py` | YES | Needs n8n setup |
| Letta Memory | `tools/letta_personality.py` | YES but **LOCAL JSON, not Letta server** | Degraded |
| Ruflo Sidecar | `tools/ruflo/server.js` | YES (started) | Python bridge (`ruflo_bridge.py`) unused |
| Computer Control | `computer_agent.py` | YES | 79KB monolith, needs splitting |
| Screenpipe | `bridges/screenpipe_bridge.py` | YES (env-gated) | Needs Screenpipe running |
| WhatsApp | `bridges/whatsapp_bridge.py` | YES | Needs WA sidecar running |
| GitHub Intel | `tools/github_intel.py` | YES (daily scan) | Needs GitHub API |
| Briefing | `tools/briefing.py` | YES | Uses wttr.in for weather |

### Missing Tools for Your Vision

| Capability You Want | Status | What's Needed |
|---------------------|--------|---------------|
| **Code like Claude Max** | Partial — basic code gen via LLM | Need: code execution sandbox, file editing, project understanding, multi-file context |
| **Research like Perplexity** | Missing | Need: web search integration (Tavily/Exa/SerpAPI), source citation, multi-step research pipeline |
| **Understand code like Copilot** | Missing | Need: codebase indexing, vector search over repos, file tree understanding |
| **Scheduled scraping** | Missing | Need: cron-like scheduler, scraping engine, data pipeline |
| **API data fetching by prompt** | Missing | Need: API catalog + autonomous API calling based on NL requests |
| **Full computer control** | Partial — `computer_agent.py` exists | Need: reliable screen reading, GUI automation, multi-monitor support |
| **Email auto-reply** | Missing | Need: email classification + smart reply generation + confirmation before sending |
| **WhatsApp assistance** | Partial — bridge exists | Need: message classification, smart reply suggestions, auto-response |
| **Smart recommendations** | Missing | Need: Google Places/Maps integration, preference learning, context-aware suggestions |
| **Self-updating from GitHub** | Missing | Need: trending repo scanner, self-analysis pipeline, automated PR creation |
| **Business maintenance (rumahlabuh)** | Minimal — Supabase access possible | Need: site monitoring, database queries, content management, analytics |

---

## 9. Config & Registry

### models.yaml
- **Status:** Loaded by `core/agent_registry.py`
- **Problem:** `load_registry()` not called at startup → config is dead at runtime

### departments.yaml
- **Status:** 76 agents defined across 9 departments
- **Problem:** Same as above — never loaded at startup

### routing_keywords.yaml
- **Status:** Used by `nexus_orchestrator.py` for Layer 1 routing
- **Problem:** `nexus_orchestrator` is not in the main message path

### .env.example
- **Status:** Comprehensive, 156 lines
- **Problem:** Many feature flags default to `false` or missing — minimal functionality out of the box
- **Critical Missing:** `LEGION_SOUL_ENABLED` is documented but not implemented as a gate in `soul_engine.py`

---

## 10. Proactive Behavior

### Why Legion Never Initiates Conversation

1. **Budget gating**: `MAX_PROACTIVE_PER_DAY=3` severely limits proactive messages
2. **Curiosity engine bug**: Follow-up message formats as dict string `"{task}"` instead of task text
3. **No daily briefing file**: `core/proactive/daily_briefing.py` doesn't exist — briefing logic split between `core/proactive/scheduler.py` and `tools/briefing.py`
4. **No event-driven triggers**: Legion doesn't react to external events (new email, calendar reminder, weather change)
5. **No "thinking of you" moments**: No system to occasionally share interesting findings or check in

### What Jarvis Would Do

- Wake you up with a briefing based on your calendar + weather + news
- Proactively alert you about important emails
- Remind you about tasks without being asked
- Share interesting GitHub repos related to your work
- Check on rumahlabuh.com health without being asked
- Follow up on conversations: "Did you resolve that bug we discussed yesterday?"

---

## 11. Missing Features for Your Dream Assistant

### Gap Analysis: Current State vs Jarvis Vision

#### 1. Autonomous Skill Selection (CRITICAL GAP)

**Current:** User must type `/do`, `/run`, `/screen`, `/debate`, etc.
**Needed:** Legion analyzes the message and autonomously decides:
- "This needs code execution" → uses computer agent
- "This needs research" → searches web first
- "This is about rumahlabuh" → queries Supabase
- "This is a debate topic" → activates debate mode
- "User wants a restaurant" → uses location + Places API

**Solution:** Build a `JarvisOrchestrator` that:
1. Classifies intent (what type of request)
2. Selects skills (what tools/capabilities needed)
3. Plans execution (what steps in what order)
4. Executes with soul/personality active throughout
5. Follows up proactively if needed

#### 2. Real Long-Term Memory (CRITICAL GAP)

**Current:** RAM history (lost on restart), fragmented stores
**Needed:** 
- Remember conversations from months ago
- Extract and store facts automatically ("Bashara lives in Koto City")
- Build a knowledge graph of relationships and events
- Temporal awareness ("You told me about X last week")

**Solution:** Implement proper Letta/MemGPT or similar persistent memory with automatic fact extraction pipeline.

#### 3. Web Research Capability (CRITICAL GAP)

**Current:** No web search integration
**Needed:** 
- Search the web before answering knowledge questions
- Cite sources
- Multi-step research with synthesis
- Stay current on news/trends

**Solution:** Integrate Tavily, Exa, or SerpAPI as a tool. Build a research pipeline that auto-triggers on knowledge-seeking questions.

#### 4. Business Management (rumahlabuh.com)

**Current:** Supabase access possible via tools
**Needed:**
- Monitor site uptime and performance
- Query/update database
- Content management
- Analytics dashboard via chat
- Customer inquiry handling

**Solution:** Build rumahlabuh-specific tools: site health monitor, Supabase query interface, content CRUD, analytics summary generator.

#### 5. Self-Improvement from GitHub

**Current:** `tools/github_intel.py` exists for daily scanning
**Needed:**
- Scan trending repos for relevant technologies
- Analyze potential self-improvements with pros/cons
- Propose implementation plans
- Auto-update capability catalog

**Solution:** Enhance GitHub Intel to do comparative analysis, create self-improvement proposals, and update SOUL.md/beliefs.json with new learnings.

#### 6. Real-Time Context (Location, Calendar, etc.)

**Current:** Location tools mostly orphaned, calendar via Composio
**Needed:**
- Know your location context
- Be aware of upcoming calendar events
- Adjust recommendations based on time/place
- "I'm near Shibuya, recommend lunch" should just work

**Solution:** Wire `location_aware.py` properly, integrate Google Calendar for context, build a context layer that feeds into every response.

---

## 12. Dead Code & Orphans

### Files/Directories to Delete

| Path | Reason |
|------|--------|
| `core/memory_old/` | Legacy, explicitly marked dead in CLAUDE.md |
| `core/orchestration_old/` | Legacy |
| `core/reliability_old/` | Legacy |
| `core/task_orchestrator_old.py` | Legacy |
| `EMERGENCY_FIX.md` | Move to `docs/hotfixes/` |
| `HOTFIX_2026-03-08.md` | Move to `docs/hotfixes/` |
| `everything-claude-code-main/` | Appears to be a cloned reference repo, not part of the bot |

### Orphaned Code (Not Dead, But Disconnected)

| File | Status |
|------|--------|
| `handlers/streaming.py` | Not in `register_all_routers` |
| `tools/browser_agent.py` `browse_task()` | Never called from any handler |
| `tools/location_aware.py` | Handler uses `location_advisor` instead |
| `bridges/ruflo_bridge.py` | Python bridge never imported |
| `bridges/mastra_bridge.py` | Never imported |
| `classify_intent_llm()` | Dead code — function exists but never called |
| `build_full_system_prompt()` | Exists but `chat()` never uses it |
| `PERSONALITY_WRAPPER` (agents.py) | Chat path uses `build_base_persona()` instead |

---

## 13. Priority Fix Order

### Phase 1: Make Legion ALIVE (Fix the Soul)

| # | Task | Impact | Effort |
|---|------|--------|--------|
| 1.1 | **Move soul to prompt position 0** in `chat()` | Soul becomes primary identity | Low |
| 1.2 | **Inject disagreement protocol** into `chat()` prompt_sections | Legion can push back and debate | Low |
| 1.3 | **Fix PERSONALITY_WRAPPER** — either use it in chat() or merge into persona | Rich personality in every response | Medium |
| 1.4 | **Fix `/debate` handler** — correct chat() call signature | Debate commands work | Low |
| 1.5 | **Enrich SOUL.md** with deeper personality, more Bashara facts, opinions, communication preferences | Richer character | Medium |
| 1.6 | **Wire emotion engine deeply** — emotion should affect response style, not just add a one-liner | Emotional range | Medium |

### Phase 2: Make Legion SMART (Fix Routing & Skills)

| # | Task | Impact | Effort |
|---|------|--------|--------|
| 2.1 | **Build JarvisOrchestrator** — autonomous skill/tool selection without slash commands | No more `/command` needed | High |
| 2.2 | **Load 76 YAML agents at startup** — call `load_registry()` in `on_startup` | Full agent roster available | Low |
| 2.3 | **Add web search tool** — Tavily/Exa/SerpAPI integration | Research capability | Medium |
| 2.4 | **Build research-before-answering pipeline** — auto-detect when research is needed | Smarter answers | Medium |
| 2.5 | **Fix intent router** — make it actually route to different behaviors, not just hints | Intent-driven responses | High |
| 2.6 | **Push SYSTEM_PROMPTS into prompt_sections** so per-agent roles aren't discarded | Agents behave differently | Low |

### Phase 3: Make Legion REMEMBER (Fix Memory)

| # | Task | Impact | Effort |
|---|------|--------|--------|
| 3.1 | **Consolidate memory writes** through MemoryManager facade only | Consistent memory | Medium |
| 3.2 | **Add automatic fact extraction** from every conversation | Learns about you automatically | Medium |
| 3.3 | **Implement persistent conversation history** (not just RAM dict) | Remembers across restarts | Medium |
| 3.4 | **Fix temporal_graph.py** to use aiosqlite | Async compliance | Low |
| 3.5 | **Build memory retrieval before answering** — "what do I know about this?" | Context-aware responses | Medium |
| 3.6 | **Connect real Letta/MemGPT** for hierarchical long-term memory | Deep long-term memory | High |

### Phase 4: Make Legion PROACTIVE (Fix Automation)

| # | Task | Impact | Effort |
|---|------|--------|--------|
| 4.1 | **Fix curiosity engine dict bug** | Proactive messages work | Low |
| 4.2 | **Increase proactive budget** or make it smarter about when to initiate | More proactive behavior | Low |
| 4.3 | **Build daily briefing properly** — weather, calendar, emails, tasks | Morning Jarvis experience | Medium |
| 4.4 | **Add email auto-classification** and smart reply suggestions | Email assistant | Medium |
| 4.5 | **Build rumahlabuh.com monitoring** tools | Business maintenance | Medium |
| 4.6 | **Build GitHub self-improvement pipeline** | Self-evolving AI | High |

### Phase 5: Make Legion CAPABLE (Add Missing Features)

| # | Task | Impact | Effort |
|---|------|--------|--------|
| 5.1 | **Add code execution sandbox** for real coding assistance | Code like Claude | High |
| 5.2 | **Add codebase indexing** for project understanding | Understand code like Copilot | High |
| 5.3 | **Wire location_aware.py** properly to handlers | Location-aware recommendations | Low |
| 5.4 | **Build scheduled task system** (cron-like) for recurring automation | Scheduled scraping/checks | Medium |
| 5.5 | **Split computer_agent.py** (79KB) into modules | Maintainability | Medium |
| 5.6 | **Build WhatsApp auto-reply** suggestions | WhatsApp assistant | Medium |

---

## Appendix A: File Naming Mismatches (CLAUDE.md vs Reality)

| CLAUDE.md Says | Actually Is |
|---------------|------------|
| `handlers/basic.py` | `handlers/system.py` |
| `handlers/llm_handlers.py` | `handlers/ai.py` |
| `handlers/memory_handlers.py` | `handlers/memory_commands.py` + `handlers/brain.py` |
| `handlers/_shared.py` | `handlers/shared.py` |
| `tools/n8n_client.py` | `tools/n8n_bridge.py` |
| `tools/letta_client.py` | `tools/letta_personality.py` |
| `tools/memory/` | Does not exist |
| `core/proactive/daily_briefing.py` | Does not exist as separate file |
| `core/proactive/proactive_scheduler.py` | `core/proactive/scheduler.py` |
| `.env RUFLO_PORT=3847` | Code uses port `7834` |

## Appendix B: Feature Flags Status

| Flag | Default | Actually Implemented? |
|------|---------|----------------------|
| `LEGION_SOUL_ENABLED` | `true` | **NOT CHECKED** — soul_engine has no gate for this flag |
| `LEGION_WORKING_MEMORY_ENABLED` | `true` | Yes — checked in working_memory.py |
| `LEGION_COGNITION_PIPELINE` | `true` | Yes — checked in cognition_pipeline.py |
| `LEGION_UNIFIED_CONTEXT_ENABLED` | `true` | Yes — checked in llm_client.py |
| `LEGION_DEBATE_ENABLED` | `true` | Yes — checked in debate handlers |
| `LEGION_CURIOSITY_ENABLED` | `true` | Yes — checked in curiosity_engine.py |
| `LEGION_COMPOSIO_ENABLED` | `false` | Yes — checked in composio_hub.py |
| `LEGION_BROWSER_ENABLED` | `false` | Yes — checked in browser_agent.py |
| `LEGION_LOCATION_ENABLED` | `false` | Yes — checked in location tools |
