---
title: legion-vision-2026
domain: future-architecture
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 420
---

# Legion Vision 2026

## ONE-LINE SUMMARY
What Legion becomes by May 2026 — architecture, capabilities, and timeline.

## FACTS
- Current state: 63% implementation (16/19 tasks) as of 2026-04-12
- Phase 1 complete: session transcripts, sandboxed shell, budget gates, proactive dedup
- Phase 2 pending (next session): skills registry, MCP backbone, heartbeat daemon
- Phase 3 pending (next week): webhook listener, MCP servers expansion
- Remaining P2 tasks: main.py swarm migration, ai.py → agent.py refactoring
- Remaining P3 tasks: ARCHITECTURE.md, MIGRATION.md, inline comments
- 76+ agents registered in YAML — many untested, no capability audit
- Memory: 6 tiers but no cross-store consistency validation
- Proactive: 3 separate engines (ProactiveScheduler, CuriosityEngine, ProactiveInitiator, proactive_engine) — fragmented
- Context window: no task-type optimization, no token budget enforcement

## LEGION 2.0 ARCHITECTURE

### Core Changes (30-day plan):
1. **Skills Registry V2**: Skill manifest with automatic discovery + LLM-based skill router (core/skills/)
2. **MCP Backbone**: Unified Model Context Protocol client connecting to 10+ external services (Brave Search, GitHub, Filesystem, Obsidian, Supabase, Playwright, mem0, Notion, Google Workspace)
3. **Job Queue**: Async job queue for tasks >30s — users get job ID, results posted when ready
4. **Context Optimizer**: Per-task-type context injection — 30-50% token reduction on simple queries
5. **Capability Audit**: Monthly automated capability regression tests

### Week 1 (by April 19):
- Skills Registry + MCP backbone wired
- Job queue prototype for thesis chapter tracking + booking escalation
- Context optimizer implemented for quick questions

### Week 2 (by April 26):
- Webhook listener: GitHub PR merged → instant notification
- Calendar integration: morning briefing includes tomorrow's meetings
- Weather + currency tools

### Week 3 (by May 3):
- POPW training dashboard: loss curve + GPU metrics
- Proactive consolidation: 3 engines → 1 unified proactive orchestrator
- Capability audit automation

### Week 4 (by May 10):
- Full context window optimization (all 5 task types)
- 100x performance definition per use case
- Agent topology redesign if needed

## ANTI-PATTERNS
1. Scope creep: trying to do all 30-day items simultaneously — prioritize thesis tracking + calendar first
2. Parallel engine proliferation: adding new proactive engines without consolidating existing ones — first merge, then extend
3. Feature bloat: skills/agents keep accumulating without pruning — need quarterly capability audit to remove dead features

## DEBATE RECORD
Advocate: 9 | Skeptic: 6 | Judge: WRITE 9
Judge note: Vision document grounds all architectural decisions — enables focused execution vs reactive firefighting.
