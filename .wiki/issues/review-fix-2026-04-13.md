---
title: Review Fix 2026 04 13
type: concept
status: legacy
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: '**File:** `wiki/projects/legion-bot.md` line 9'
wikilinks: []
confidence: medium
source: research
---
**File:** `wiki/projects/legion-bot.md` line 9

**Current state:**
```
wikilinks: [[entities/opencode.md], [concepts/multi-agent-orchestration.md], [architecture/legion-module-map.md]]
```

**Expected:** `[[entities/opencode.md]] [[concepts/multi-agent-orchestration.md]] [[architecture/legion-module-map.md]]` (three separate bracket pairs, no commas)

**Result:** ❌ **FAIL** — Wikilinks are comma-separated inside a single bracket group, which is malformed. The parser likely treats this as a single link `[[entities/opencode.md], [concepts/multi-agent-orchestration.md], [architecture/legion-module-map.md]]`.

**Additional malformed wikilinks found:** 29 files have the same pattern in their frontmatter `wikilinks:` field. All use comma-separated links inside a single `[[...]]` group.
---


## CHECK 2: Duplicate memory-architecture.md

**Command:** `find wiki/ -name "*memory*" -type f`

**Found 3 files:**
1. `wiki/architecture/memory-architecture.md` ✓
2. `wiki/architecture/memory-system-architecture.md` ✓
3. `wiki/concepts/memory-architecture.md` ✓

**Frontmatter validation:**
- `architecture/memory-architecture.md`: Valid frontmatter (title, type, status, tags, created, updated, summary, wikilinks, confidence, source)
- `concepts/memory-architecture.md`: Valid frontmatter (title, type, status, tags, created, updated, summary, wikilinks, confidence, source)

**Analysis:** The "memory-architecture" concept exists in two places (`architecture/` and `concepts/`). The `architecture/memory-system-architecture.md` is a separate file (not a duplicate). The duplication is architectural inconsistency, not file duplication per se.

**Result:** ⚠️ **WARNING** — Two `memory-architecture.md` files exist in different directories with different content. Links from `concepts/` context resolve to `concepts/memory-architecture.md`, links from `architecture/` context may resolve to either.

---

## CHECK 3: Overall wikilink integrity

**Broken wikilinks found:** 40

**Categories of broken links:**
1. **Legacy/conversational paths** (28 links): `wiki/conversations.md`, `wiki/mental_health.md`, `wiki/emotional_intelligence.md`, `wiki/relationships.md`, `wiki/user_interactions.md` — these conversation/timeline files reference wiki pages that don't exist
2. **Old wiki paths** (6 links): `.wiki/decisions/ADR-001-opencode-integration.md`, `.wiki/logs/2026-04-11-opencode-integration.md` — paths with leading `.wiki/` that don't exist
3. **Renamed/moved files** (4 links): `wiki/legion/conversations_log.md`, `wiki/algorithms/data_structures.md`
4. **Malformed references** (2 links): `[[wikilink]]` in SCHEMA.md, `[[page]]` in obsidian-plugins.md

**Sample broken links:**
```
legion/opencode-integration-2026-04-11.md: [[decisions/ADR-001-opencode-integration.md]]
legion/conversations_log.md: [[legion/interactions.md]]
conversations/2026-04-11.md: [[conversations.md]]
timelines/2026-04-10.md: [[mental_health.md]]
_meta/obsidian-plugins.md: [[page]]
```

**Note:** `rag-engineer.md` exists at `wiki/raw/skills_ref/rag-engineer.md` but linked as `concepts/rag-engineer.md` — not resolvable.

**Result:** ❌ **FAIL** — 40 broken links across 25+ files

---

## Summary

| Check | Result | Evidence |
|-------|--------|----------|
| Malformed wikilink | ❌ FAIL | 30 files have comma-separated wikilinks in single brackets |
| Duplicate memory files | ⚠️ WARN | 2 `memory-architecture.md` files in different dirs |
| Wikilink integrity | ❌ FAIL | 40 broken links found |

**Total issues:** 70+ wikilink problems requiring manual correction.