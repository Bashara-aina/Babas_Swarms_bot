---
title: Adr 001 Dual Router Conflict
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

# ADR-001: Dual Router Conflict (agents.py vs autonomous_router.py)

**Date**: 2026-04-12  
**Status**: Accepted  
**Deciders**: Worker agent (audit task)

## Context

During the import chain audit (W-1), a potential architectural concern was identified:
- `agents.py` re-exports from `core.agent_registry`
- `autonomous_router.py` provides `route()` function for LLM-driven routing

Both serve similar purposes but in different code paths.

## Decision

No immediate action required. The two modules serve different purposes:
- `agents.py`: Agent registry and model configuration
- `autonomous_router.py`: Runtime intent classification

However, this creates cognitive overhead and could lead to confusion.

## Consequences

**Positive**:
- Separation of concerns (registry vs routing)

**Negative**:
- Developers may not know which to use
- Potential for divergence if updated independently

## Review

Re-evaluate if routing bugs appear that could be caused by divergence.
