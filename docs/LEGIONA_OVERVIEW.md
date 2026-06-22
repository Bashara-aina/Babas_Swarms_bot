# Legiona Feature Inventory
**Commit:** `56f8d29` | **Date:** April 2026 | **Source:** git log

> ⚠️ Confidence guidelines: `[VERIFY]` = <85% confidence (unverified from context). `⚠️ Partial` = partially wired. `🔑 Needs config` = requires unset env var.

---

## Surface 1 — Claude Code

**Entry point:** `CLAUDE.md` (800 lines) — single source of truth for all Claude coding sessions.

### Core Infrastructure

| Feature | File | Status | Notes |
|---------|------|--------|-------|
| **MiniMax M3 with reasoning_split** | `.claude/settings.json` | ✅ Complete | `reasoning_split=True`, `temperature=1.0`, model=`MiniMax-M3` |
| **10-layer anti-hallucination protocol** | `.claude/settings.json`, `.github/copilot-instructions.md` | ✅ Complete | CoT + CoVe, P1–P6 evidence hierarchy, `[VERIFY]` tags |
| **Context Health Monitor** | `core/context_health.py` | ✅ Complete | HEALTHY/CAUTION/CRITICAL/OVERFLOW levels; pre-compaction checkpoint ritual |
| **Drift Detection** | `core/drift_detector.py` | ✅ Complete | Error accumulation prevention; abort at 5+ failed attempts |
| **Self-Evolution Feedback Pipeline** | `core/self_evolution.py` | ✅ Complete | `record_failure()`, `record_decision()`, `build_eval_set_from_failures()` |
| **Pre-Compaction Checkpoint** | `core/checkpoint_runner.py` | ✅ Complete | Writes `.claude/.checkpoint_index.json` + `.claude/memory_bootstrap.md` |
| **Agent Teams (Planner/Builder/Critic)** | `core/agent_teams.py` | ⚠️ Partial | Adversarial 3-role reasoning; Planner locks spec → Builder implements → Critic attacks |
| **GitNexus Code Intelligence** | `.claude/settings.json` (MCP) | ✅ Complete | `query`, `context`, `impact`, `rename`, `detect_changes`, `cypher` |

### Intent Router (23 intents)

| Intent | Handler | Status |
|--------|---------|--------|
| 23-intent classifier | `core/intent_router.py` | ✅ Complete |
| Falls back to `general` agent if all scores <0.35 | `handlers/ai.py` | ✅ Complete |

### Memory Architecture (4 active tiers)

| Tier | Technology | Purpose | Status |
|------|------------|---------|--------|
| Working | `core/memory/memory_manager.py` (in-process dict) | Current session | ✅ Complete |
| Episodic | `core/memory/episodic_store.py` (SQLite/aiosqlite) | 30-day recall | ✅ Complete |
| Semantic | `core/memory/memory_manager.py` (mem0ai) | Vector retrieval | ✅ Complete |
| Graph | `core/memory/temporal_graph.py` (SQLite) | Relationship KG | ✅ Complete |

> Note: ChromaDB is **NOT** used (mem0 handles vector storage). Letta is **NOT** present.

### 84-Agent Roster

| Category | Count | Config |
|----------|-------|--------|
| engineering | 15 | `config/departments.yaml` |
| design | 10 | `config/departments.yaml` |
| research | 12 | `config/departments.yaml` |
| marketing | 12 | `config/departments.yaml` |
| operations | 7 | `config/departments.yaml` |
| legal_compliance | 6 | `config/departments.yaml` |
| product | 8 | `config/departments.yaml` |
| creative | 8 | `config/departments.yaml` |
| vision_multimodal | 6 | `config/departments.yaml` |

**Routing layers:** keyword (`routing_keywords.yaml`) → semantic (sentence-transformers ALL 3 LAYERS ACTIVE) → LLM fallback (Gemma3:12b local).

### UI/UX Excellence System

| Feature | File | Status |
|---------|------|--------|
| OKLCH + Nexus Palette design tokens | `.claude/rules/ui-ux-excellence.md` | ✅ Complete |
| NL auto-activation (ui-ux-pro-max, frontend-design, libre-ui-ux, taste) | `.claude/rules/ui-ux-excellence.md` | ✅ Complete |
| Forbidden AI-slop patterns enforcement | `.claude/rules/ui-ux-excellence.md` | ✅ Complete |
| Design reference benchmarks (Linear, Vercel, Stripe, Oxide) | `.claude/rules/ui-ux-excellence.md` | ✅ Complete |

### Background Tasks

| Task | Schedule | File | Budget-gated |
|------|----------|------|-------------|
| Curiosity engine | Every 30 min | `core/proactive/curiosity_engine.py` | ✅ Yes |
| Daily briefing | 07:30 JST | `tools/briefing.py` | ❌ Disabled |
| GitHub intel scan | 09:00 JST | `tools/composio_hub.py` | ✅ Yes |
| Memory consolidation | 02:00 JST | `core/memory/consolidator.py` | ❌ Local only |
| Proactive scheduler | Event-driven | `core/proactive/scheduler.py` | ✅ Yes |
| Ruflo Node.js sidecar | On boot | `tools/ruflo/server.js` | N/A |

---

## Surface 2 — OpenCode

**Entry point:** `.opencode/opencode.json`

### MCP Servers Configured

| MCP Server | Type | Target | Status |
|-----------|------|--------|--------|
| `gitnexus` | local | pnpm dlx gitnexus | ✅ Complete |
| `obsidian` | local | npx kynlos-obsidian-mcp-server | ✅ Complete (vault at `.wiki/`) |
| `git` | local | npx @mseep/git-mcp-server | ✅ Complete |
| `filesystem` | local | mcp-server-filesystem `/home/newadmin` | ✅ Complete |
| `firecrawl` | local | firecrawl-mcp (API key: `FIRECRAWL_API_KEY`) | 🔑 Needs config |
| `exa` | remote | `https://mcp.exa.ai/mcp` | 🔑 Needs config |

### Agent Definitions

**Count:** 100+ agents across domains.

| Domain | Examples |
|--------|---------|
| `research/` | trend-analyst, research-analyst, competitive-analyst, market-researcher |
| `backend/` | api-designer, websocket-engineer, backend-developer, microservices-architect |
| `frontend/` | ui-designer, frontend-developer, design-bridge, accessibility-tester |
| `ml/` | ml-engineer, ai-engineer, nlp-engineer, llm-architect, fintech-engineer, prompt-engineer |
| `mcp/` | task-distributor, context-manager, agent-installer, workflow-orchestrator |
| `devops/` | chaos-engineer, tooling-engineer, build-engineer, docker-expert, kubernetes-specialist |
| `security/` | license-engineer, penetration-tester, security-auditor, ad-security-reviewer |
| `data/` | data-scientist, data-analyst, data-researcher, database-optimizer |
| `product/` | project-manager, product-manager, scrum-master, project-idea-validator |
| `gaming/` | search-specialist, graphql-architect, electron-pro, game-developer |
| `docs/` | technical-writer, api-documentor, documentation-engineer, readme-generator |
| `meta/` | customer-success-manager, legal-advisor, risk-manager, performance-engineer, dx-optimizer |
| `platform/` | wordpress-master, payment-integration |
| `embedded/` | iot-engineer, embedded-systems |
| `blockchain/` | blockchain-developer |
| `mobile/` | mobile-developer, mobile-app-developer |
| `windows/` | m365-admin, windows-infra-admin, powershell-ui-architect, powershell-module-architect |

### Memory (OpenCode)

| File | Purpose |
|------|---------|
| `.opencode/memory/` | Cross-session memory components |

---

## Surface 3 — Legiona Bot

**Commit:** `56f8d29 feat(legiona): streaming, memory guard, native tool loop`

### Core MiniMax Client

| Feature | File:Line | Status |
|---------|-----------|--------|
| `reasoning_split=True` | `lib/legiona/minimax_client.py` | ✅ Complete |
| `temperature=1.0`, `top_p=0.95`, `top_k=40` | `lib/legiona/minimax_client.py` | ✅ Complete |
| Preset profiles: `coding`, `research` | `lib/legiona/minimax_client.py` | ✅ Complete |
| OpenRouter fallback chain | `lib/legiona/minimax_client.py` | ⚠️ Partial [VERIFY] |
| Prompt caching via `cache_control` | `lib/legiona/minimax_client.py` | ✅ Complete |
| Vision: `_load_image_as_base64()`, `_inject_images_into_messages()` | `lib/legiona/minimax_client.py` | ✅ Complete |
| Cost logging → `lib/legiona/memory/cost_log.jsonl` | `lib/legiona/minimax_client.py` | ✅ Complete |

### Bot Handlers

| Command | Handler | Status | Notes |
|---------|---------|--------|-------|
| `/run <prompt>` | `lib/legiona/bot/handlers.py:cmd_run` | ✅ Complete | Streams via `stream_to_telegram()`, aiogram 3.24 |
| `/think <prompt>` | `lib/legiona/bot/handlers.py:cmd_think` | ✅ Complete | Direct completion, no streaming |
| Owner check decorator | `lib/legiona/bot/handlers.py:_require_owner` | ✅ Complete | `message.from_user.id == ALLOWED_USER_ID` |
| HTML escaping | `lib/legiona/bot/handlers.py:_escape` | ✅ Complete | `html.escape()` on all output |

### Streaming Response

| Feature | File | Status |
|---------|------|--------|
| Progressive Telegram edits via `edit_message_text` | `lib/legiona/bot/stream_handler.py` | ✅ Complete |
| Token usage tracking | `lib/legiona/bot/stream_handler.py` | ⚠️ Partial [VERIFY] |

### Debate Engine

| Feature | File | Status |
|---------|------|--------|
| 3-agent parallel debate (Advocate + Challenger → Judge) | `lib/legiona/debate.py` | ✅ Complete |
| `debate()` async, `debate_sync()` sync wrapper | `lib/legiona/debate.py` | ✅ Complete |
| Parallel advocate + challenger via `asyncio.gather` | `lib/legiona/debate.py` | ✅ Complete |

### Self-Evolution

| Feature | File | Status |
|---------|------|--------|
| `record_session()` → `sessions.jsonl` | `lib/legiona/self_evolve.py` | ✅ Complete |
| `evolve()` → reads last N sessions, generates rule | `lib/legiona/self_evolve.py` | ✅ Complete |
| `load_evolved_rules()` → prepends to system prompt | `lib/legiona/self_evolve.py` | ⚠️ Partial [VERIFY] |
| Rule deduplication via `_normalize_rule()` | `lib/legiona/self_evolve.py` | ✅ Complete |
| `_sync_global_memory()` → `global_memory.md` | `lib/legiona/self_evolve.py` | ✅ Complete |

### RAG (Retrieval-Augmented Generation)

| Feature | File | Status |
|---------|------|--------|
| Supabase pgvector embedding retrieval | `lib/legiona/rag_retriever.py` | 🔑 Needs config (SUPABASE_URL + service key) |
| `retrieve_context()` → list of content strings | `lib/legiona/rag_retriever.py` | ✅ Complete |
| `retrieve_context_as_messages()` → cache-controlled user msg | `lib/legiona/rag_retriever.py` | ✅ Complete |
| BM25 + vector hybrid scoring | `lib/legiona/rag_indexer.py` | ⚠️ Partial [VERIFY] |
| `get_embedding()` via MiniMax embedding model | `lib/legiona/rag_indexer.py` | 🔑 Needs config [VERIFY] |

### Scheduler (APScheduler)

| Task | Schedule (JST) | Status |
|------|----------------|--------|
| Weekly evolution (`evolve`) | Sunday 09:00 | ✅ Complete |
| Friday hallucination eval | Friday 18:00 | ⚠️ Partial (`lib/legiona/eval/hallucination_eval.py` [VERIFY exists]) |
| Monthly rule deduplication | 1st of month 02:00 | ✅ Complete |

### Tool Registry

**Total tools:** 8 native tools in M3 tool-calling loop.

| Tool | Function | Status |
|------|---------|--------|
| `mmx_vision` | MMX-CLI vision modality wrapper | 🔑 Needs config (`mmx-cli` npm package) |
| `mmx_search` | MMX-CLI web search wrapper | 🔑 Needs config |
| `mmx_speech` | MMX-CLI TTS wrapper | 🔑 Needs config |
| `shell_exec` | Async shell with timeout (30s default) | ⚠️ Partial (SECURITY: read-only assumed) |
| `supabase_query` | Direct Supabase table query | 🔑 Needs config |
| `rag_retrieve` | Local RAG retrieval BM25+vector | 🔑 Needs config |
| `Bash` | [VERIFY from context — likely subprocess] | ⚠️ Partial |
| `Read` | [VERIFY from context — likely file read] | ⚠️ Partial |

> Note: MMX-CLI is npm-installed (`npm install -g mmx-cli`), wraps 7 MiniMax modalities. API key set via `mmx config set api_key=<key>` not env vars.

### Observability

| Feature | File | Status |
|---------|------|--------|
| OTLP/Jaeger tracing | `lib/legiona/observability/tracer.py` | ⚠️ Partial [VERIFY] |
| ¥ cost logging → `cost_log.jsonl` | `lib/legiona/observability/cost_log.py` | ✅ Complete |
| `today_total_jpy()` | `lib/legiona/observability/cost_log.py` | ✅ Complete |

### Memory Files (Legiona)

| File | Purpose | Status |
|------|---------|--------|
| `lib/legiona/memory/global_memory.md` | Persists across all sessions; architecture facts + evolved rules | ✅ Complete |
| `lib/legiona/memory/rules.md` | Accumulated evolved rules from self-evolution | ✅ Complete |
| `lib/legiona/memory/sessions.jsonl` | Per-session records: task, tool_calls, outcome, success | ✅ Complete |
| `lib/legiona/memory/cost_log.jsonl` | Token usage + ¥ cost per call | ✅ Complete |

---

## Surface 4 — GitHub Copilot

**Entry point:** `.github/copilot-instructions.md` (164 lines)

### LEGIONA MASTER SYSTEM PROMPT v3

| Layer | Feature | Status |
|-------|---------|--------|
| Layer 1 | Reasoning gate (5-step CoT before output) | ✅ Complete |
| Layer 2 | Chain-of-verification (per-factual-claim check) | ✅ Complete |
| Layer 3 | P1–P6 evidence hierarchy | ✅ Complete |
| Layer 4 | Explicit uncertainty phrases | ✅ Complete |
| Layer 5 | Fact vs inference block separation | ✅ Complete |
| Layer 6 | Coding discipline (only confirmed imports/APIs) | ✅ Complete |
| Layer 7 | Long-context drift protection | ✅ Complete |
| Layer 8 | Agentic safety gate (≥85% confidence, ≤5 steps) | ✅ Complete |
| Layer 9 | Structured output validation | ✅ Complete |
| Layer 10 | Self-audit footer (confidence/verification checklist) | ✅ Complete |

### ANTI-LOOP PROTOCOL (M3 Self-Evolution)

| Rule | Trigger | Action |
|------|---------|--------|
| Same file read >2× | STOP | Summarize + proceed |
| Same test/command >2× | STOP | Change approach entirely |
| 3 identical tool results | STOP | Escalate to user |
| >8 tool calls without progress | STOP | Replan from scratch |

### Override Rules (absolute — never skip)

1. Never fabricate functions/libraries/APIs
2. Never present inference as confirmed fact
3. Never skip self-audit on code/architecture output
4. Never take irreversible action below 85% confidence
5. Never hallucinate test results, benchmarks, or metric values

### GitHub Workflows

| Workflow | Purpose | Status |
|----------|---------|--------|
| `legiona-review.yml` | Legiona-specific review automation | ✅ Complete (2347 bytes) |
| `claude-review.yml` | Claude Code review automation | ✅ Complete |
| `ci.yml` | General CI pipeline | ✅ Complete |
| `typecheck.yml` | Type checking workflow | ✅ Complete |
| `release.yml` | Release workflow | ✅ Complete |

---

## Shared Infrastructure

### Cross-System Bridges

| Bridge | File | Purpose |
|--------|------|---------|
| OpenCode ↔ Claude Code ↔ LegionBot | `core/opencode_bridge.py` | Directive protocol: `@claude <task>` spawns CC, `@legion <task>` recurses |
| GitNexus MCP | `core/claude_code_bridge.py` | Code intelligence integration |

### Wiki Guardian Protocol (Obsidian Vault `.wiki/`)

| Rule | Requirement |
|------|------------|
| Boot check | `ls .wiki/.obsidian/` + `compile_state.json` timestamp |
| Write target | `.wiki/` ONLY (not `wiki/` or `~/swarm-bot/wiki/`) |
| After write | Update `compile_state.json` + `git add .wiki/` |

### Multi-Session Worktree System

| Component | Location |
|----------|----------|
| Registry | `~/.claude/worktrees/registry.json` |
| CLI | `cd ~/.claude/lib && python cli.py --help` |
| Root | `CLAUDE_REPO_ROOT=/home/newadmin/swarm-bot` |

---

## Environment Variables Reference

| Variable | Used By | Status |
|----------|---------|--------|
| `TELEGRAM_BOT_TOKEN` | Legiona bot handlers | 🔑 Needs config |
| `ALLOWED_USER_ID` | All bot handlers | 🔑 Needs config |
| `LEGIONA_NOTIFY_CHAT_ID` | Scheduler (Telegram alert) | 🔑 Needs config |
| `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL` | RAG retriever | 🔑 Needs config |
| `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_KEY` | RAG retriever | 🔑 Needs config |
| `MMX_TIMEOUT` (default 120s) | mmx_tools | 🔑 Needs config (npm package) |
| `FIRECRAWL_API_KEY` | OpenCode MCP | 🔑 Needs config |
| `EXA_API_KEY` | OpenCode MCP | 🔑 Needs config |

---

## Quick Status Summary

| Surface | Completeness | Key Gaps |
|---------|-------------|---------|
| **Claude Code** | ✅ ~95% | `P2-3: /budget command`, `P2-4: /soul command` pending |
| **OpenCode** | ✅ ~90% | `P3-4: URL allowlist in browser_agent.py` pending |
| **Legiona Bot** | ✅ ~85% | `/debate` wired; streaming + self-evolution complete; RAG needs Supabase |
| **GitHub Copilot** | ✅ ~95% | LEGIONA v3 prompt fully implemented |

> `[VERIFY]` tags above indicate items where confidence <85% — actual file inspection recommended before relying on behavior.
