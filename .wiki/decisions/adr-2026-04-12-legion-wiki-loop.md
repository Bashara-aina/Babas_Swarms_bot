---
title: adr-2026-04-12-legion-wiki-loop
type: decision
status: accepted
tags: [wiki, knowledge-base, karpathy, pattern]
created: 2026-04-12
updated: 2026-04-12
summary: Wiki auto-ingest configured with KARPATHY_KB_PATTERN for structured knowledge storage with frontmatter and TL;DR summaries.
wikilinks:
  - [[./concepts/karpathy-kb-pattern]]
  - [[SCHEMA]]
confidence: high
source: decision
---

# ADR: Legion Wiki Loop Strategy

**Date**: 2026-04-12  
**Status**: ACCEPTED

## Context

Legion needs persistent knowledge storage that:
- Survives conversations
- Is queryable by AI and Dataview
- Follows consistent structure
- Enables wikilink cross-referencing

## Decision

Use Karpathy KB Pattern with:
- Frontmatter YAML for metadata
- TL;DR summary first on every page
- Wikilinks for cross-references
- Dataview queries for indexing

## Implementation

- New schema: `wiki/SCHEMA.md` v2.0
- Auto-ingest via `wiki_auto_ingest.py`
- Quality gate with duplicate detection
- Dataview-enabled `wiki/INDEX.md`

## Consequences

### Positive
- Consistent page structure
- AI-readable knowledge base
- Automated indexing
- Cross-reference discovery

### Negative
- Migration effort for existing pages
- Schema enforcement required

## Related Pages

- [[./concepts/karpathy-kb-pattern]] — Pattern reference
- [[SCHEMA]] — Schema definition
