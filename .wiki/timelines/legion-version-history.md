---
title: legion-version-history
type: timeline
status: active
tags: [legion, versions, history, changelog, humanization]
created: 2026-04-13
updated: 2026-04-13
summary: Legion evolved from a simple Telegram bot (v1.0) to a multi-agent swarm platform (v8.0) over 2025-2026, with v6.0.0 being the major humanization update introducing persistent memory tiers, emotion engine, reflection engine, and autonomous skill selection.
wikilinks:
  - [[legion-bot]]
  - [[adr-2026-04-12-opencode-over-cursor-for-backend]]
  - [[memory-system-architecture]]
confidence: high
source: documentation
---

# Legion Version History

## TL;DR
Legion evolved from a simple Telegram bot (v1.0) to a multi-agent swarm platform (v8.0) over 2025-2026. The most transformative update was v6.0.0 "THE HUMANIZATION UPDATE" which introduced persistent 3-tier memory, emotion engine, reflection engine, and autonomous skill selection. Current version v8.0 focuses on multi-agent pipeline execution, budget enforcement, and full skill registry coverage.

## Version Timeline

### v1.0 — Initial Bot (2025)
- Basic Telegram bot functionality
- Single LLM provider (OpenAI)
- No memory system
- Single command handler
- Stateless responses

### v2.0 — LLM Expansion
- Multiple LLM provider support
- Basic fallback chain
- Prompt templates introduced

### v3.0.0 — Memory Foundation (2026-02-01)
**Major**: Initial multi-agent swarm architecture

- ChromaDB integration for vector memory
- Session transcript storage
- Basic skills system
- `/swarm` command for parallel execution
- 9 department architecture defined

### v4.0.0 — Capability Expansion (2026-03-08)
**Major**: Computer use and multi-provider routing

| Feature | Implementation |
|---------|----------------|
| Computer control | Screenshot, click, type, drag, scroll |
| LLM fallback chain | Groq → Cerebras → Gemini → OpenRouter → ZAI → Ollama |
| Per-agent routing | computer, coding, debug, vision, math, architect, analyst, general |
| Second brain | /remember, /recall, /memories, /briefing |
| arXiv integration | /paper, /ask_paper for academic papers |
| Deep research | /scrape, /research for web content |
| Background scheduler | /monitor, /schedule, /cancel |
| Email client | /email |
| Context compaction | Long thread handling |
| QwQ-32b reasoning | /think command |

### v4.1.0 — Architecture Refactor (2026-03-14)
**Major**: Handler decomposition and enterprise layer

- **Handler refactor**: main.py reduced from 2678 lines → 230 lines
- **12 handler modules**: computer, system, ai, research, brain, sessions, tasks, dev, pm, enterprise, shared
- **Enterprise orchestration** (`swarms_bot/`):
  - ChiefOfStaff
  - BudgetManager
  - SecurityGuard
  - AuditLogger
  - CostAwareRouter
  - CostMetricsCollector
  - SessionManager
- **New commands**: /loop, /metrics, /budget, /routing_stats, /security_stats, /audit_summary
- **CI/CD**: GitHub Actions CI + Release workflow
- **Docker**: GPU passthrough for RTX 3060

### v5.0 — Swarm Architecture (Mid-March 2026)
- 9 departments × 8 agents = 72 specialist agents
- 6 debate personas for structured argumentation
- OpenRouter as primary routing hub
- Task orchestrator with SwarmDebateOrchestrator
- Nexus semantic embedding routing

### v6.0.0 — THE HUMANIZATION UPDATE (2026-04-07)
**Most transformative release**

This update addressed Legion feeling "robotic" by adding genuine persistent identity:

#### Persistent 3-Tier Memory (letta + mem0 architecture)
| Tier | Implementation | Purpose |
|------|---------------|---------|
| CoreMemory | JSON key-value | High-priority facts always in prompt |
| ArchivalMemory | SQLite FTS5 | Unlimited persistent store |
| RecallMemory | Full conversation log | Permanent history |

#### Temporal Knowledge Graph (graphiti architecture)
- Tracks facts over time with validity windows
- Seeded with known facts about Bashara from day one
- Temporal queries: "What was X like 3 months ago?"

#### User Profile (memobase architecture)
- Permanent profile of who Bashara is
- Grows from interactions and explicit `/teach`
- Not just what was said, but who the user is

#### Emotion Engine (openfeelz-inspired)
- OCEAN-backed personality framing
- PAD emotional state tracking (Pleasure-Arousal-Dominance)
- Tracks: curiosity, frustration, energy, connection
- Persists across sessions, decays toward baseline

#### Reflection Engine (generative_agents + Reflexion)
- Micro-reflection after each turn
- Deep reflection every 10 turns
- Stores: observations, technical opinions, lessons, concerns

#### Autonomous Skill Selection (ReAct-style routing)
- Plain text routes automatically to: chat, research, code, system, computer, memory
- Legacy slash commands still supported
- Intent router with 23 intent types

### v7.0 — ClawCode Upgrade (Early April 2026)
**Major**: OpenCode integration and session persistence

- OpenCode CLI integration for autonomous coding
- Session transcript persistence (SQLite-backed)
- Sandboxed shell execution (Blacklist guard)
- Proactive check-in engine with 9-message pool
- 4-hour check-in cooldown

### v8.0 — Current (2026-04)
**Major**: Multi-agent pipeline and budget enforcement

| Feature | Status |
|---------|--------|
| Multi-agent pipeline | Planner/Worker/Reviewer |
| Budget enforcement | Cost-aware routing |
| Full skill registry | 30+ skills documented |
| Deep research pipeline | gpt-researcher integration |
| Dify workflow | Self-hosted RAG pipelines |
| MCP backbone | Model Context Protocol |

## Version Comparison Matrix

| Version | Memory | Agents | Skills | Humanization |
|---------|--------|--------|--------|--------------|
| v1.0 | None | 1 | 0 | None |
| v3.0 | ChromaDB | 72+ | 5 | No |
| v4.x | +Transcripts | 76 | 15 | Basic |
| v5.0 | Semantic | 87 | 20 | Partial |
| v6.0 | 3-tier + Graph | 87 | 25 | Full |
| v7.0 | +Persistence | 87 | 28 | +Emotions |
| v8.0 | Unified | 76 registry | 30+ | +Reflection |

## Related Pages

- [[legion-bot]] — Current state
- [[adr-2026-04-12-opencode-over-cursor-for-backend]] — OpenCode selection
- [[memory-system-architecture]] — Memory tiers
- [[architecture/audit-2026-04-11-fixes]] — Critical fixes applied 2026-04-11
- [[architecture/refactoring-2026-04-11]] — Refactoring round 2
- [[architecture/orchestrator-comparison]] — Consolidation planning
- [[timelines/2026-04-10]] — Session log 2026-04-10
- [[timelines/2026-04-11]] — Session log 2026-04-11
- [[timelines/2026-04-12]] — Session log 2026-04-12
