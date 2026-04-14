---
title: Cursor
type: entity
status: deprecated
tags: [ide, coding, agent, alternative]
created: 2026-04-13
updated: 2026-04-13
summary: Cursor is an AI-first IDE evaluated for Legion's coding tasks but OpenCode was selected instead for its CLI-first approach, native subprocess model, and Telegram-compatible agent output. Decision recorded in adr-2026-04-12-opencode-over-cursor-for-backend.
wikilinks:
  - [[./entities/opencode]]
  - [[decisions/adr-2026-04-12-opencode-over-cursor-for-backend]]
confidence: high
source: decision
project: legion
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

See [[decisions/adr-2026-04-12-opencode-over-cursor-for-backend]]

## Evaluation Details

Cursor was evaluated on 2026-04-12 for backend coding tasks:
- **Strengths**: AI-first IDE, Copilot++ features, strong autocomplete, VSCode-compatible extensions
- **Weaknesses**: GUI-only (no headless mode), no native subprocess bridge, agent runs inside editor not from CLI
- **OpenCode advantages**: CLI-first, auto-starts on port 4096, stdout/stderr streamable, perfect for Telegram output

## Why Not Used

Legion needs autonomous code execution triggered from an iPhone Telegram message. Cursor requires:
1. Human at a GUI desktop
2. Manual agent invocation
3. Manual result retrieval

OpenCode's server model (`opencode serve --port 4096`) is purpose-built for programmatic invocation — exactly what Legion's bridge architecture requires.

## Current Status

**Not used** — OpenCode selected for all backend coding tasks. Cursor remains installed on the machine for direct IDE use by Bashara but is not integrated into Legion's agent pipeline.

## Related Pages

- [[./entities/opencode]] — Selected alternative
- [[decisions/adr-2026-04-12-opencode-over-cursor-for-backend]] — Decision record
