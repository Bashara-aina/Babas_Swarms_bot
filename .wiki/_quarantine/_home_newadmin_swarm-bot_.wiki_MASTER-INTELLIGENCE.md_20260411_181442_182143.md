---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/MASTER-INTELLIGENCE.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.182184"
}
---

# SwarmBot Master Intelligence Index
> Single file loaded first in every OpenCode session
> Auto-generated: 2026-04-12
> Total knowledge sources: 7 repositories + custom wiki + Bashara profiles + project docs

---

## HOW TO USE THIS FILE
At the start of every session, read this file completely before taking any action.
It contains distilled knowledge from 7 world-class knowledge bases plus project-specific context.

---

## 1 CONTEXT ENGINEERING PRINCIPLES
Source: ~/swarm-bot/.wiki/research/context-engineering

**Top 10 Context Engineering Principles:**
- Context window optimization is non-trivial — too little/irrelevant hurts performance, too much increases cost
- Use KV-Cache for performance optimization (cache hit rates reduce latency/cost)
- Append-only context maintains cache validity — avoid modifying previous context
- Treat file systems as external context memory
- Mask, don't remove tools for better action selection in agents
- Context poisoning, distraction, confusion, and clash are primary failure modes
- RAG + tool loadout + context quarantine + pruning are core solutions
- Model Context Protocol (MCP) standardizes context sharing between tools
- LangGraph provides low-level orchestration for context management
- Error preservation (keeping failure traces) enables model learning

**Key Frameworks:** LangGraph, LangSmith, LangMem, Claude Code, Reflexion, RAG

---

## 2 AI AGENT FRAMEWORKS — TOP 10 FOR SWARM BOTS
Source: ~/swarm-bot/.wiki/research/ai-agents

| Framework | Use Case | Key Feature |
|-----------|----------|-------------|
| LangGraph | Multi-agent orchestration | Graph-based stateful directed graphs |
| CrewAI | Role-based agents | 60%+ Fortune 500 usage, goal-oriented crews |
| AutoGen | Multi-agent conversations | Microsoft-backed, flexible patterns |
| OpenAI Agents SDK | Multi-step agents | Official OpenAI, handoffs |
| MetaGPT | Software company sim | PM, architect, engineer roles |
| LangChain | General purpose | Most adopted, modular |
| LlamaIndex | Data-focused RAG | Knowledge-intensive agents |
| Pydantic AI | Type-safe agents | Clean Pythonic API |
| DSPy | Programming not prompting | Stanford, auto-optimizes |
| Smolagents | Lightweight | HuggingFace, ~1000 lines |

**Protocols:** MCP (USB-C for AI), A2A (Google agent-to-agent), OpenAI Function Calling, Anthropic Tool Use

---

## 3 OPENCODE ELITE TRICKS — TOP 15
Source: ~/swarm-bot/.wiki/research/opencode

**Top 15 Tips:**
1. Use /handoff to create focused prompts when switching sessions
2. Install opencode-snip to reduce LLM token consumption by 60-90%
3. Use opencode-dynamic-context-pruning to keep context lean
4. Configure opencode-model-announcer so agent knows which model it's using
5. Use tmux integration plugins for real-time multi-agent visibility
6. Leverage background agents for parallel task execution
7. Use opencode-envsitter-guard to prevent .env leaks
8. Install opencode-workspace for bundled 16-component orchestration
9. Use opencode-oh-my-opencode-slim for lightweight token-efficient orchestration
10. Use opencode-tokenscope to track and optimize token costs
11. Use opencode-swarm-plugin for swarm-based coordination
12. Use opencode-mcp for Model Context Protocol server support
13. Use opencode-agent-memory for Letta-inspired persistent memory
14. Use opencode-background for long-running task management
15. Use opencode-snippets for DRY prompt engineering

**Top 5 Workflows:**
1. Multi-Agent Swarm: opencode-swarm-plugin + background-agents
2. Context Pruning Loop: dynamic-context-pruning + tokenscope
3. Session Handoff: Create handoff → new session → immediate productivity
4. Safe .env: envsitter-guard + opencode-mem
5. Background Processing: background plugin + tmux panes

---

## 4 AI-DRIVEN DEV PATTERNS — TOP 10
Source: ~/swarm-bot/.wiki/research/ai-dev-patterns

**Top 10 Patterns for Python + Multi-Agent Systems:**

1. **Multi-Agent Orchestration**: Use LangGraph, CrewAI, AutoGen — define roles, tools, handoff protocols
2. **Context Engineering**: RAG, pruning, summarization, external memory for long sessions
3. **Iterative Self-Refinement**: generate → review → improve loop
4. **Tool Use with Function Calling**: JSON schemas + handler functions
5. **ReAct**: thought → action → observation → repeat
6. **TDD with AI**: Use shortest, testzeus-hercules, qodo-cover
7. **SWE-Bench Issue Resolution**: SWE-agent, OpenHands for autonomous fixing
8. **Background Agents**: Parallel async execution with opencode-background-agents
9. **Memory-Augmented Agents**: Mem0, simple-memory, opencode-mem
10. **MCP Standardization**: MCP servers for GitHub, databases, tool sharing

---

## 5 KARPATHY LLM WIKI METHOD
Source: ~/swarm-bot/.wiki/tools/karpathy-wiki

**Key principles:**
- Treat the wiki as the codebase — agent reads before every task
- Every session ends with a /wiki save to .wiki/logs/
- Use ripgrep (rg) for fast semantic search across all notes
- AGENTS.md files = instructions injected into every file edit
- Wiki grows smarter over time as agent adds to it
- Use external memory (file systems) as extended context
- Append-only context to maintain cache validity

---

## 6 SWARMBOT PROJECT CONTEXT
Source: ~/swarm-bot/AGENTS.md

```
# SwarmBot — Master Agent Context
> Auto-generated by OpenCode elite setup | Updated: 2026-04-10

## Project Architecture
- Type: Python Telegram bot with multi-agent orchestration
- Framework: aiogram 3.4+ (async Telegram bot), litellm 1.57+ (LLM routing)
- Python: 3.11+, asyncio-first, no threading/blocking I/O
- Key Files: main.py (bot startup), agents.py (agent registry), llm_client.py (LLM calls), computer_agent.py (desktop control)

## Agent System
- Planner (@planner): Decomposes tasks, never edits files directly
- Worker (@worker): Executes code changes, full file + bash access
- Reviewer (@reviewer): Reviews all changes before commit, read-only
- WikiBot (@wikibot): Writes session summaries and decisions to .wiki/

## Coding Standards
- Python: Type hints on all functions, docstrings on public methods, Black formatting
- Imports: stdlib → third-party → local (enforced by ruff)
- Async: All I/O operations must use asyncio/await, no threading or time.sleep()
- Error handling: Specific try/except, never bare except
- Formatting: f-strings only (no .format() or % formatting)

## Critical Rules
- NEVER edit .env, .env.local, .env.production, secrets.json directly
- NEVER hardcode API keys — always use os.getenv()
- ALWAYS run tests before committing: pytest tests/ -x --asyncio-mode=auto -q
- ALWAYS write decisions to .wiki/decisions/ as ADR-XXX files
- ALWAYS log completed tasks to .wiki/logs/
- Use async/await for all I/O operations
- Check .wiki/ for existing context before starting any task
- LLM calls go through llm_client.py — never call litellm directly

## Directory Guide
- handlers/ — 45+ aiogram router files (one per feature domain)
- core/ — Agent orchestration, intent routing, memory, soul engine
- swarms_bot/ — Enterprise orchestration layer (routing, sessions, security)
- agents/ — 76+ specialized agents across 9 departments
- tools/ — External integrations (browser, email, GitHub, n8n)
- config/ — YAML configs for models, departments, routing keywords
- .wiki/ — Knowledge base (architecture, agents, decisions, logs, research)
- tests/ — pytest-asyncio test suite
```

---

## 7 ACTIVE AGENTS ROSTER

| Agent | Invoke | Role | Model |
|-------|--------|------|-------|
| Planner | @planner | Decomposes tasks | MiniMax M2.7 |
| Worker | @worker | Executes code | MiniMax M2.7 |
| Reviewer | @reviewer | Reviews changes | MiniMax M2.7 |
| WikiBot | @wikibot | Manages knowledge | MiniMax M2.7 |

---

## 8 SLASH COMMANDS REFERENCE

| Command | Purpose |
|---------|---------|
| /swarm [task] | Full 3-agent pipeline |
| /audit | Deep security + quality scan |
| /wiki | Save session to wiki |
| /fix [bug] | Diagnose and fix bug |
| /refactor [target] | Safe incremental refactor |
| /status | Full project dashboard |
| /commit | Smart conventional commit |
| /research [topic] | Research and save to wiki |

---

## 9 CRITICAL RULES — NEVER VIOLATE

1. Always read MASTER-INTELLIGENCE.md at session start
2. Never read or edit .env files — use $ENV_VAR references only
3. Always write session summary with /wiki before ending
4. Always run @reviewer before any git commit
5. All architecture decisions → .wiki/decisions/ as ADR files
6. Use rg for wiki search: rg "keyword" ~/swarm-bot/.wiki
7. Context is precious — use /prune if context feels heavy
8. LLM calls go through llm_client.py — never call litellm directly
9. All I/O must be async — no threading or blocking calls
10. Tests must pass before any commit: pytest tests/ -x --asyncio-mode=auto -q

---

## 10 QUICK REFERENCE — WIKI STRUCTURE

~/swarm-bot/.wiki/
├── MASTER-INTELLIGENCE.md  ← YOU ARE HERE — read every session
├── README.md               ← vault index
│
├── profiles/               ← Bashara + Legion personal knowledge
│   ├── BASHARA-MASTER-PROFILE.md   ← PRIMARY: all personal context (READ FIRST)
│   ├── bashara-technical.md        ← Hardware, APIs, subscriptions, git workflow
│   ├── legion-soul.md              ← Legion's soul (copied from SOUL.md)
│   ├── bashara-claude-profile.md   ← Legacy Claude profile export
│   ├── bashara-gemini-profile.md  ← Legacy Gemini profile export
│   └── bashara-perplexity-profile.md ← Legacy Perplexity profile export
│
├── projects/               ← Project architecture docs
│   ├── legion-roadmap.md         ← Legion v10 full architecture + roadmap
│   ├── rumahlabuh-architecture.md ← rumahlabuh.com Supabase schema + business
│   └── cekwajar-architecture.md  ← cekwajar.id domain knowledge + labor law
│
├── research/               ← External research + thesis
│   ├── EXTERNAL-RESEARCH-FINDINGS.md ← Perplexity: benchmarks, tax, conferences
│   ├── thesis/
│   │   ├── thesis-context.md      ← POPW protocol, architecture, advisor
│   │   └── benchmark-audit.md    ← IKEA ASM baselines, 17-paper audit
│   ├── context-engineering/
│   ├── ai-agents/
│   ├── opencode/
│   ├── ai-dev-patterns/
│   └── agent-intelligence/   ← Agent capabilities & intelligence research
│       ├── CONTEXT-ENGINEERING-GUIDE.md   ← RAG, memory tiers, dynamic context (Meirtz/Awesome-Context-Engineering)
│       ├── AGENT-CAPABILITIES-REFERENCE.md ← Full capabilities map by category (e2b-dev/awesome-ai-agents)
│       └── MEMORY-ARCHITECTURE-GUIDE.md   ← Mem0, Letta, memory tiers wiring
│
├── architecture/           ← Production system architecture
│   └── PRODUCTION-AGENT-PATTERNS.md   ← Memory, A2A, observability, orchestration (EthicalML/awesome-production-agentic-systems)
│
├── tools/                  ← executable tools + MCP server registry
│   ├── karpathy-wiki/
│   ├── openaugi/
│   └── MCP-SERVERS-AVAILABLE.md   ← 5000+ MCP servers by category (punkpeye/awesome-mcp-servers)
│
├── workflows/             ← Automation documentation
│   └── n8n-documentation.md     ← n8n webhook bridge, auto-start, workflows
│
├── templates/              ← note templates
├── indexes/                ← distilled summaries (read these fast)
├── agents/                 ← agent definitions and status
├── decisions/              ← ADR files
├── logs/                   ← session logs
├── prompts/                ← reusable prompts
└── issues/                 ← bugs and blockers

---

## 11 INSTALLED TOOLS

| Tool | Path | Purpose |
|------|------|---------|
| karpathy-wiki | tools/karpathy-wiki | LLM wiki method implementation |
| openaugi | tools/openaugi | Notes → agent task dispatch |

**Run openaugi:** python ~/swarm-bot/.wiki/tools/openaugi/main.py --vault ~/swarm-bot/.wiki

---

## 12 LEGION UPGRADE STATUS 2026-04-10

### Completed Phases (1-4 ✅)
- **Phase 1**: Deep scan & audit — SOUL.md, llm_client.py, main.py, ADR-001 written
- **Phase 2**: MiniMax as primary model — minimax provider in llm_client.py, retry logic
- **Phase 3**: Soul Engine v2 — caching, emotional states, mood momentum, banned phrases
- **Phase 4**: Autonomous skill selection — LLM classification, skills/manifest.json, skill_registry.py

### Active Phases (5-10 🔄)
- **Phase 5**: Proactive Intelligence — scheduler enhanced with SelfUpgradeEngine GitHub digest + Soul Engine late-night tone
- **Phase 6**: Web Search — DuckDuckGo + SerpAPI (skills/web_search.py), GeoIntelligence (skills/geo_intelligence.py)
- **Phase 7**: Self-Updating — scan_weekly_trends() in self_upgrade.py, CapabilityAudit (core/capability_audit.py)
- **Phase 8**: Business Intelligence — booking alerts, failed payments, overbooking detection (tools/rumahlabuh_crew.py), DatabaseAgent (skills/database_agent.py)
- **Phase 9**: Wiki & OpenCode — AGENTS.md in 5 dirs, ADR-002 updated, MASTER-INTELLIGENCE.md updated
- **Phase 10**: Final Wiring — requirements.txt updated (duckduckgo-search, apscheduler, chromadb, aiofiles), import verification, smoke test

### Test Status
276 tests passing (Phase 2-4 complete)

### New Files Created
- `core/capability_audit.py` — monthly self-audit
- `skills/web_search.py` — DuckDuckGo + SerpAPI
- `skills/geo_intelligence.py` — location recommendations
- `skills/database_agent.py` — NL→SQL for Supabase

### Enhanced Files
- `core/proactive/scheduler.py` — T5.2 (GitHub digest), T5.3 (Soul Engine late night)
- `core/self_upgrade.py` — T7.1 (scan_weekly_trends)
- `tools/rumahlabuh_crew.py` — T8.1 (booking alerts)
- `requirements.txt` — T10.1 (duckduckgo-search, apscheduler, chromadb, aiofiles)

---

## 13 BASHARA PROFILE — CRITICAL CONTEXT

**READ FIRST before any task**: `.wiki/profiles/BASHARA-MASTER-PROFILE.md`

Quick facts:
- Master's student, SIT Tokyo, Data Science/CV, MEXT visa expires ~Sept 2027
- Runs rumahlabuh.com (32-room boarding house, Surakarta) + cekwajar.id (salary SaaS)
- Wake 7AM, sleep often past 1AM, thesis deadline July 2026
- Prof. Masaomi Kimura advisor, zemi Thu 1–3PM JST
- Korean girlfriend Hanifah in Bandung, ADB scholarship decision pending → Sept 2026 wedding plan
- LLM: MiniMax M2.7 primary, Claude Sonnet 4.6 fallback
- Total AI spend: ~$40/month

For full context → `.wiki/profiles/BASHARA-MASTER-PROFILE.md`
For technical setup → `.wiki/profiles/bashara-technical.md`
For thesis → `.wiki/research/thesis/thesis-context.md`
For Legion architecture → `.wiki/projects/legion-roadmap.md`

---

## 14 WIKI HEALTH SCORE — ALL GAPS FILLED ✅

All 5 remaining gaps filled as of 2026-04-12. Wiki Intelligence Upgrade added 5 research files (2026-04-11). Wiki IQ is now **9.5/10**.

| Dimension | Score | Status |
|---|---|---|
| Personal Identity & Personality | 9/10 | 🟢 |
| Technical Knowledge | 9/10 | 🟢 |
| Projects & Business Context | 9/10 | 🟢 |
| Academic & Research Context | 9/10 | 🟢 |
| Life Context & Environment | 8/10 | 🟢 |
| Goals & Ambitions | 8/10 | 🟢 |
| Legion-Specific Intelligence | 9/10 | 🟢 |
| External World Knowledge | 9.5/10 | 🟢 |
| **OVERALL WIKI IQ** | **9.5/10** | 🟢 EXCELLENT |

### Wiki Intelligence Upgrade (2026-04-11)
- **New files**: 5 research documents from 4 GitHub repositories
  - `research/agent-intelligence/CONTEXT-ENGINEERING-GUIDE.md` — RAG, memory tiers, dynamic context
  - `research/agent-intelligence/AGENT-CAPABILITIES-REFERENCE.md` — Full capabilities map by category
  - `research/agent-intelligence/MEMORY-ARCHITECTURE-GUIDE.md` — Mem0, Letta, memory tiers wiring
  - `architecture/PRODUCTION-AGENT-PATTERNS.md` — Memory at scale, A2A, observability
  - `tools/MCP-SERVERS-AVAILABLE.md` — 5000+ MCP servers curated by category

### Gap Resolution Log (2026-04-12)
- **GAP-001**: SOUL.md mirrored → `.wiki/profiles/legion-soul.md`
- **GAP-002**: Supabase schema documented → `.wiki/projects/rumahlabuh-architecture.md`
- **GAP-003**: Thesis LaTeX noted → `.wiki/research/thesis/thesis-context.md`
- **GAP-004**: MiniMax config verified in `.env.example`
- **GAP-005**: n8n bridge documented → `.wiki/workflows/n8n-documentation.md`

### Founder Mindset (2026-04-11)
10 distilled principles from world-class agentic company builders:
- **01-glean**: Reliability > capability always (boringly reliable first)
- **02-swarm**: One agent = one job, always
- **03-100pct-ai**: "Can it run 7 days without me?" test
- **04-flow**: Think → Plan → Verify → Execute → Reflect
- **05-vertical**: Own a vertical before going horizontal
- **06-compound**: Stop re-deriving, start compiling
- **07-picks**: Build picks & shovels around platforms
- **08-reliability**: Production gap is enormous — audit checklist
- **09-leverage**: G.U.M.M.I. morning check-in, 3-5 decisions max
- **10-distribution**: Free tool = best distribution strategy

Source: `.wiki/founder-mindset/` + `.wiki/indexes/founder-mindset-index.md`

### Wisdom & Mental Models (2026-04-11)
20 distilled sources for Legion's reasoning capability:
- **Tier 1 (Thinking)**: Munger latticework, Taleb antifragile, PG founder mode, first principles, second-order thinking
- **Tier 2 (Reasoning)**: Chain-of-thought, theory of mind, steelmanning, pre-mortem, epistemic humility
- **Tier 3 (Operational)**: 80/20 Pareto, decision-making under uncertainty, systems thinking, stoic principles, Feynman technique
- **Tier 4 (Builder)**: Lean startup, skin-in-the-game, deep work, network effects/moats, purpose-driven clarity

Source: `.wiki/wisdom/` + `.wiki/indexes/wisdom-index.md`

---

Last updated: 2026-04-12
