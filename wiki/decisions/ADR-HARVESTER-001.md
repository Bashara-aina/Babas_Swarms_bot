---
title: Adr Harvester 001
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-HARVESTER-001: Legion Daily Intelligence Harvester v1.0

**created:** 2026-04-11  
**status:** accepted  
**decider:** @planner → @worker implementation  

---

## Context

Legion needs an autonomous daily intelligence system that:
- Runs at 04:00 WIB every day
- Harvests knowledge from web sources across adaptive topic quotas (100 slots/day)
- Debates every piece via 4-agent swarm before wiki acceptance
- Generates morning Telegram reports (max 3000 chars)
- Topic budget adapts based on Bashara's Telegram chats and git commits

Without such a system, knowledge accumulation is passive and opportunistic, not systematic.

---

## Decision

Implement the **Legion Daily Intelligence Harvester** with:

### 1. Adaptive Topic Quota (100 slots/day)
- 10 base topics with base weights
- Weight formula: `mention_count × 2 + commit_count × 3 + (days_since)^0.5`
- Normalize to 100 total slots
- Min 3, Max 35 per topic; 5 reserved for surprise discoveries

### 2. 4-Agent Swarm Debate
- **Prosecutor** (MiniMax M2.7): find flaws
- **Defender** (MiniMax M2.7): counter-argue
- **Fact Checker** (Claude Sonnet 4): verify claims
- **Judge** (Claude Sonnet 4): render verdict
- Verdict types: ACCEPT, ACCEPT_WITH_CAVEAT, SUPERSEDE, REJECT, NEEDS_MORE_RESEARCH

### 3. Wiki Storage with Naming Convention
- Filename: `[PREFIX]-[NNN]-[slug]-[YYYY-MM-DD].md`
- Prefixes: CW- (cekwajar), POPW- (popw), AI- (ai-tools), PERS- (personal), GEN- (general)
- INDEX.md per topic directory, updated on each write
- Harvest log, rejected log, conflict log

### 4. Morning Telegram Report
- Max 3000 chars
- Sections: TOP FINDINGS, CONFLICTS FOUND, REJECTED TODAY, TOPIC BUDGET visualization
- Emoji anchors for quick scanning

### 5. Cron Scheduling
- Runs at 21:00 UTC = 04:00 WIB daily
- Log output to `logs/harvest_YYYYMMDD.log`

---

## Alternatives Considered

### Alternative A: Manual Curation
- Pros: full control, no false positives
- Cons: not scalable, doesn't run daily, requires human effort

### Alternative B: Single LLM Filter
- Pros: simple, fast
- Cons: no genuine debate, no multi-perspective verification, lower quality

### Alternative C: Full Research Agent per Topic
- Pros: thorough
- Cons: extremely expensive, too slow for daily 100-slot quota

---

## Consequences

### Positive
- **Cumulative knowledge**: each day's findings build on prior days
- **Quality gate**: 4-agent debate catches misinformation before wiki ingestion
- **Adaptive focus**: topic weights shift with Bashara's actual interests (Telegram + git)
- **Morning briefing**: Telegram report keeps Bashara informed without checking manually
- **Conflict tracking**: contradictions between entries are logged and resolvable

### Negative
- **API costs**: ~4 LLM calls per candidate × 100 candidates = 400 calls/day
  - Mitigated by using cheap M2.7 for Prosecutor/Defender, Sonnet 4 only for Judge/FactChecker
- **Complexity**: 9 new modules, more to maintain
- **Stub search**: web search integration (Tavily/Firecrawl) not yet implemented — current build is skeleton

---

## Implementation Notes

- All async I/O with asyncio/aiofiles
- Uses existing `llm_client.chat()` for all LLM calls
- Telegram integration is stub (no actual bot send yet)
- Git log analysis is stub (not yet reading real git history)
- Web search is stub (not yet connected to Tavily/Firecrawl)
