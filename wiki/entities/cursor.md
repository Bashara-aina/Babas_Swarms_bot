---
title: cursor
type: entity
status: deprecated
tags: [ide, coding, agent, alternative]
created: 2026-04-13
updated: 2026-04-13
summary: Cursor is an AI-powered IDE that was evaluated but not selected in favor of OpenCode for backend Legion tasks.
wikilinks: [[opencode]]
confidence: high
source: decision
---

# Cursor

## TL;DR
Cursor is an AI-first IDE evaluated for Legion's coding tasks, but OpenCode was selected instead for its CLI-first approach and Telegram integration.

## Evaluation Summary

| Criteria | Cursor | OpenCode |
|----------|--------|----------|
| CLI access | ❌ Limited | ✅ Full |
| Telegram integration | ❌ | ✅ |
| Agent pipeline | ✅ | ✅ |
| Self-hosted | ✅ | ✅ |

## Decision

See [[adr-2026-04-12-opencode-over-cursor-for-backend]]

## Current Status

**Not used** — OpenCode selected for all backend coding tasks.

## Related Pages

- [[opencode]] — Selected alternative
- [[adr-2026-04-12-opencode-over-cursor-for-backend]] — Decision record
