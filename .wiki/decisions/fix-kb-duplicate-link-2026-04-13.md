---
title: Fix Kb Duplicate Link 2026 04 13
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Two issues were identified in the wiki knowledge base:'
wikilinks: []
confidence: medium
source: research
---
# ADR-006: Fix KB Duplicate memory-architecture.md and Malformed Wikilink

**Date**: 2026-04-13
**Status**: Resolved

## Context

Two issues were identified in the wiki knowledge base:
1. Malformed wikilink in `wiki/projects/legion-bot.md` line 9
2. Duplicate `memory-architecture.md` files in `wiki/architecture/` and `wiki/concepts/`

## Decision

### Issue 1: Malformed Wikilink

**File**: `wiki/projects/legion-bot.md` line 9
**Problem**: `[[entities/opencode.md],` — errant comma inside bracket
**Fix**: Changed wikilinks format from `[[link1], [link2], [link3]]` to `[[link1]], [[link2]], [[link3]]`

### Issue 2: Duplicate memory-architecture.md

**Files involved**:
- `wiki/concepts/memory-architecture.md` — abstract concept about memory layers (KEPT)
- `wiki/architecture/memory-architecture.md` — system design content about memory problems (RENAMED)

**Decision rationale**:
- `wiki/concepts/` directory is for abstract ideas and concepts
- `wiki/architecture/` directory is for system design documents
- The file in `wiki/architecture/memory-architecture.md` contained "Critical Problems" analysis, which is system design content
- Since `wiki/architecture/memory-system-architecture.md` already exists with technical implementation details, the problem analysis file was renamed

**Resolution**: Renamed `wiki/architecture/memory-architecture.md` → `wiki/architecture/memory-gaps-analysis.md`

## Consequences

- Malformed wikilink in legion-bot.md is now properly formatted
- Only one `memory-architecture.md` remains in `wiki/concepts/`
- New file `wiki/architecture/memory-gaps-analysis.md` contains the system design content about memory problems
- Wikilinks across the wiki that pointed to `concepts/memory-architecture.md` remain valid
