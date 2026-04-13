---
title: legion-version-history
type: timeline
status: active
tags: [legion, versions, history, changelog]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's version history tracks major releases from v1.0 through v8.0 with key features added at each version.
wikilinks: [[projects/legion-bot.md], [wiki/decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md]]
confidence: high
source: documentation
---

# Legion Version History

## TL;DR
Legion evolved from a simple Telegram bot (v1.0) to a multi-agent swarm platform (v8.0) over 2025-2026.

## Version Timeline

### v1.0 — Initial Bot
- Basic Telegram bot
- Single LLM (OpenAI)
- No memory

### v3.0 — Memory Foundation
- ChromaDB integration
- Session transcripts
- Basic skills

### v5.0 — Swarm Architecture
- 9 departments × 8 agents
- Debate personas
- OpenRouter integration

### v6.0 — Production Hardening
- Error resilience
- Rate limiting
- Circuit breakers

### v7.0 — ClawCode Upgrade
- OpenCode integration
- Session persistence
- Sandboxed shell

### v8.0 — Current (2026-04)
- Multi-agent pipeline (Planner/Worker/Reviewer)
- Budget enforcement
- Full skill registry

## Major Decisions

- [[wiki/decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md]]
- ADR-001: OpenCode integration
- ADR-005: Wiki loop strategy

## Related Pages

- [[projects/legion-bot.md]] — Current state
- [[decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md]] — Recent decision
