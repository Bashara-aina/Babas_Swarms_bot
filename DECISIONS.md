# Architecture Decision Records
**Project:** Babas Agency Swarm | **File:** DECISIONS.md
**Purpose:** Why things are the way are — consulted at session start to understand architectural contracts.
Every non-obvious decision documented here with rationale, alternatives considered, and consequences.

---

## ADR Template

```markdown
## ADR-[N]: [Decision Title]
Date: YYYY-MM-DD
Status: ACCEPTED | SUPERSEDED by ADR-[M]

### Context
[What situation required a decision]

### Decision
[What was decided]

### Rationale
[Why — including alternatives considered and rejected]

### Consequences
[What becomes easier / harder because of this decision]

### Do Not Revisit Unless
[What would need to be true for this to change]
```

---

## Seeded Decisions (pre-populated from established project choices)

### ADR-001: Cloud-First LLM Routing (No Local Fallback for Text)
Date: 2026-03-01 | Status: ACCEPTED

**Context:** Legion needs reliable, high-quality LLM responses for complex tasks. Local models are available but have VRAM/quality tradeoffs.

**Decision:** Cloud-first routing with litellm. Ollama only for vision. All text/coding/reasoning uses cloud providers (Groq, Cerebras, etc.) with fallback chains.

**Rationale:**
- RTX 3060 (12GB) is insufficient for 70B+ text models at speed
- Cloud providers (Groq, Cerebras) offer free tiers with high quality 70B models
- Ollama local models add latency without quality gain for text tasks
- Vision tasks (screenshots) ARE local via Ollama — privacy-preserving, no GPU VRAM pressure

**Alternatives rejected:**
- Local-only text: VRAM too limited, quality insufficient for coding/debate tasks
- OpenAI Anthropic-only: expensive, no free tier
- Single provider: no fallback on rate limits

**Consequences:**
- Easier: reliable 70B model access via Groq free tier
- Harder: requires API keys for multiple providers
- Harder: need fallback chain management for reliability

**Do Not Revisit Unless:** RTX 4090+ or similar GPU available, OR cloud API costs become prohibitive.

---

### ADR-002: aiogram 3.x Async Framework (Not python-telegram-bot)
Date: 2026-02-01 | Status: ACCEPTED

**Context:** Building a multi-agent async Telegram bot. Need full asyncio support for concurrent LLM calls, background tasks, and tool execution.

**Decision:** aiogram 3.x as Telegram framework. Fully async, middleware system, FSM support, no sync blocking.

**Rationale:**
- aiogram 3.x has first-class asyncio support
- python-telegram-bot is sync-blocking by default (ThreadPoolExecutor for callbacks)
- aiogram's middleware system enables rich pre-processing (auth, intent routing, rate limiting)
- Group middleware stacks cleanly vs. decorator soup

**Alternatives rejected:**
- python-telegram-bot: sync-only defaults, harder to integrate with async LLM calls
- Bot API-only (raw HTTP): too much boilerplate, reinventing轮子
- Node.js (telegraf): wrong language for ML/LLM integration

**Consequences:**
- Easier: concurrent background tasks (LLM calls, curiosity engine, memory consolidation)
- Easier: middleware stack for auth + intent + rate limiting
- Harder: aiogram learning curve for team members familiar with PTB

---

### ADR-003: mem0 Over ChromaDB for Vector Semantic Memory
Date: 2026-03-15 | Status: ACCEPTED

**Context:** Need persistent semantic vector storage for long-term memory. Two options: mem0ai (managed/ cloud) vs. ChromaDB (local).

**Decision:** mem0 for semantic memory, ChromaDB probed but NOT used as primary. LegionMemoryFacade composites mem0 + wiki + Screenpipe.

**Rationale:**
- mem0ai has superior retrieval algorithms (auto-metadata extraction, adaptive forgetting, multi-modal)
- ChromaDB is just a vector store — no retrieval intelligence
- ChromaDB was kept as probe-target for compatibility but is not used standalone
- LegionMemoryFacade (core/legion_memory_facade.py) is the single write path — never write directly to mem0 or ChromaDB

**Alternatives rejected:**
- ChromaDB standalone: no retrieval intelligence, would need custom forgetting/freshness logic
- Pinecone: cost, managed service dependency
- Local FAISS: no cloud sync, no managed retrieval

**Consequences:**
- Easier: intelligent retrieval with adaptive forgetting
- Harder: MEM0_API_KEY required, cloud dependency for memory
- Harder: must always use memory_manager.py facade — never bypass

---

### ADR-004: Fully Async Project (No threading, No time.sleep)
Date: 2026-02-01 | Status: ACCEPTED

**Context:** Multi-agent bot with concurrent LLM calls, background tasks, database operations. Sync I/O would create convoy effects.

**Decision:** ALL I/O is async. No threading module usage. No time.sleep(). All DB via aiosqlite.

**Rationale:**
- LLM calls are I/O-bound — blocking would serialize what should be parallel
- Background tasks (curiosity engine, memory consolidation) need to run concurrently with message handling
- asyncio.create_task() for all background work with try/except wrapping
- time.sleep() blocks the event loop → defeats the purpose of async

**Alternatives rejected:**
- thread pool for LLM calls: works but adds overhead, harder to debug, no native asyncio
- gevent: invasive monkey-patching, conflicts with aiogram

**Consequences:**
- Easier: concurrent LLM chains, parallel tool calls
- Harder: must always use asyncio.wait_for() with timeout for shell/CLI commands
- Harder: learning asyncio discipline (await not blocking, create_task not fire-and-forget)

---

### ADR-005: SOUL.md as Living Identity (Not Static Prompt)
Date: 2026-01-15 | Status: ACCEPTED

**Context:** Legion needs to feel like a persistent coworker who grows, not a static bot. SOUL.md is Legion's living identity document.

**Decision:** SOUL.md is read at boot AND every conversation. When Legion learns something new, it updates SOUL.md AND data/beliefs.json. Personality/emotion state persists via Letta.

**Rationale:**
- Static prompts → Legion forgets between sessions → breaks "permanent coworker" illusion
- SOUL.md gives Legion a sense of continuity and growth
- data/beliefs.json stores structured beliefs for debate engine
- soul_engine.py builds soul_context → injected as section 0 of system prompt (before personality, before everything)

**Alternatives rejected:**
- Personality in DB only: not human-editable, harder to audit
- Static personality in code: requires deploy to change — too heavy

**Consequences:**
- Easier: Bashara can audit/edit Legion's identity directly via SOUL.md
- Easier: Legion can update its own beliefs when it learns something significant
- Harder: soul_engine.py must not fail silently — broken SOUL.md breaks the whole bot

---

### ADR-006: Department-Based 84-Agent Architecture
Date: 2026-03-01 | Status: ACCEPTED

**Context:** Legion needs specialized agents for different domains (engineering, research, marketing, etc.). Need to scale beyond a single general-purpose agent.

**Decision:** 84 agents across 9 departments in config/departments.yaml. Nexus orchestrator routes tasks by keyword → semantic embedding → LLM fallback. Agents selected by task type, not manually.

**Rationale:**
- Single general agent → mediocre at everything, great at nothing
- Department structure mirrors organizational knowledge domains
- Nexus 3-layer routing: keyword (fast) → semantic (accurate) → LLM (handles edge cases)
- Agent definitions in YAML → no code changes for adding new agents

**Alternatives rejected:**
- 5 mega-agents: defeats specialization benefit
- Per-feature hard-coded routing: brittle, hard to maintain
- Single prompt with tool selection: less transparent than explicit agent dispatch

**Consequences:**
- Easier: adding new agents = edit YAML, no code change
- Easier: each agent has explicit capabilities, tools, model assignment
- Harder: agent selection quality depends on intent router accuracy
- Harder: 84 agents × fallbacks = large model routing table

---

### ADR-007: 3-System Integration (OpenCode + Claude Code + LegionBot)
Date: 2026-04-01 | Status: ACCEPTED

**Context:** Three AI systems touching the same codebase. Need shared brain + coordination protocol to avoid conflicts.

**Decision:** Three-system integration via: (1) shared .wiki/ vault as joint brain, (2) git worktree for parallel sessions, (3) cross-system bridges (legion_callback_bridge, claude_code_bridge, opencode_bridge), (4) joint_memory.py as single write path for all three.

**Rationale:**
- OpenCode for deep multi-file refactors (4-agent pipeline)
- Claude Code for targeted single-file work
- LegionBot for Telegram operational tasks
- All three share the same Obsidian wiki (.wiki/) as persistent brain
- joint_memory.py facade prevents write conflicts
- Max 3 recursive spawns to prevent infinite loops

**Alternatives rejected:**
- Three isolated systems: no shared learning, divergent decisions
- Single system: can't parallelize

**Consequences:**
- Easier: shared knowledge across all three AI systems
- Harder: need discipline to use joint_memory.py instead of writing directly
- Harder: cross-system directive protocol (@claude, @legion) must be wired correctly

---

## Accumulated ADRs (append new records below)

<!-- Add new ADRs above this line. -->
