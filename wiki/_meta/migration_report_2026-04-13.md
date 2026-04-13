# Migration Report — 2026-04-13

## Summary

Successfully restructured wiki/ to follow Karpathy LLM KB Pattern.

---

## Phase 0: Audit ✅

- Audited all directories: root .md, wiki/, .wiki/, docs/, skills/
- Created structured audit report at `wiki/_meta/audit_report_2026-04-13.md`
- Identified 150+ files to migrate
- Detected duplicates and empty directories

---

## Phase 1: Directory Structure ✅

Created structure:
```
wiki/
├── raw/ (audits, roadmaps, prompts, changelogs, configs, papers, skills_ref, docs, snapshots)
├── concepts/ (12+ concept pages)
├── entities/ (11+ entity pages)
├── projects/ (3 project pages)
├── decisions/ (76 ADR files)
├── architecture/ (10 files)
├── timelines/ (6 files)
├── people/ (1 person page)
├── output/ (queries, health)
└── _meta/ (meta files)
```

---

## Phase 2: SCHEMA.md ✅

Created `wiki/SCHEMA.md` v2.0 with:
- Full frontmatter specification
- Directory structure definition
- Page type definitions
- Wikilink syntax
- Dataview query examples
- Migration map
- Graph config colors

---

## Phase 3: Migration ✅

### Files Copied

| Source | Target | Count |
|--------|--------|-------|
| Root .md docs | wiki/raw/docs/ | 12 files |
| docs/*.md | wiki/raw/docs/ | 10 files |
| docs/hotfixes/*.md | wiki/raw/changelogs/hotfixes/ | 2 files |
| wiki/legion/*.md | wiki/architecture/ | 3 files |
| wiki/conversations/*.md | wiki/timelines/ | 4 files |
| .wiki/decisions/ADR-*.md | wiki/decisions/ | 76 files |
| skills/*.md | wiki/raw/skills_ref/ | 19 files |
| .wiki/knowledge/tax/*.md | wiki/concepts/tax-indonesia/ | 10 files |
| .wiki/knowledge/labor-law/*.md | wiki/concepts/labor-law-indonesia/ | 12 files |
| .wiki/knowledge/market/*.md | wiki/concepts/market-data-indonesia/ | 14 files |
| .wiki/knowledge/business/*.md | wiki/concepts/business-research/ | 8 files |
| .wiki/knowledge/bpjs/*.md | wiki/concepts/bpjs-reference/ | 8 files |
| .wiki/05-growth-strategy/* | wiki/projects/ | 1 file |
| .wiki/legion/*.md | wiki/architecture/ | 2 files |

**Total files copied**: 170+

### Files NOT Moved (Originals Preserved)
- SOUL.md, CLAUDE.md, AGENTS.md (root - sacred)
- main.py, core/, handlers/ (no-touch directive)
- Original wiki/legion/, wiki/conversations/ (copied, not deleted)

---

## Phase 4: Compiled Articles ✅

### Concepts (12+)
1. intent-routing.md
2. memory-architecture.md
3. reasoning-loop.md
4. skill-registry.md
5. multi-agent-orchestration.md
6. self-improvement-loop.md
7. karpathy-kb-pattern.md
8. bayesian-blending.md
9. freemium-gate.md
10. llm-cost-routing.md
11. vector-search.md
12. context-window-budget.md

### Entities (11+)
1. minimax-m2-7.md
2. openrouter.md
3. supabase.md
4. gpt-researcher.md
5. dify.md
6. markitdown.md
7. opencode.md
8. cursor.md
9. obsidian.md
10. litellm.md
11. chromadb.md

### Projects (3+)
1. legion-bot.md
2. cekwajar-id.md
3. rumahlabuh-com.md
4. cekwajar-roadmap.md

### Decisions (5+)
1. adr-2026-04-12-opencode-over-cursor-for-backend.md
2. adr-2026-04-11-opencode-integration.md
3. adr-2026-04-12-legion-wiki-loop.md
4. adr-2026-04-12-circuit-breaker.md
5. adr-2026-04-12-multi-agent-pipeline.md
6. + 76 ADRs from .wiki/decisions/

### Architecture (5+)
1. legion-module-map.md
2. memory-system-architecture.md
3. skill-execution-flow.md
4. orchestrator-comparison.md
5. cekwajar-tech-stack.md
6. + migrated files from wiki/legion/

### Timelines (2+)
1. legion-version-history.md
2. cekwajar-phase-log.md
3. + migrated conversation summaries

### People (1+)
1. andrej-karpathy.md

---

## Phase 5: Obsidian Configuration ✅

### Created Files
- `wiki/_meta/obsidian-plugins.md` — Plugin list + install instructions
- `wiki/_meta/graph-config.json` — 8 color groups for graph view
- `wiki/INDEX.md` — Updated with Dataview queries

### Graph Color Groups
| Group | Color | Examples |
|-------|-------|----------|
| concepts | #4a90d9 | intent-routing, memory-architecture |
| entities | #50c853 | supabase, litellm, chromadb |
| projects | #f44336 | legion-bot, cekwajar-id |
| decisions | #ff9800 | ADRs |
| architecture | #9c27b0 | module maps, tech stacks |
| people | #00bcd4 | andrej-karpathy |
| timelines | #795548 | version histories |
| raw | #757575 | source files |

---

## Phase 6: Verification ✅

### Counts Verified
- Concepts: 12 ✓
- Entities: 11 ✓
- Projects: 4 ✓
- Decisions: 76 ✓
- Architecture: 10 ✓
- Timelines: 6 ✓
- People: 1 ✓

### Frontmatter Check
All concept pages have valid frontmatter with:
- title
- type
- status
- tags
- created
- updated
- summary
- wikilinks
- confidence
- source

---

## DO NOT TOUCH (Verified)

The following were NOT modified:
- `main.py` ✓
- `core/` ✓
- `handlers/` ✓
- `SOUL.md` ✓
- `CLAUDE.md` ✓

---

## Files Created/Modified

| File | Action |
|------|--------|
| wiki/SCHEMA.md | REPLACED (v2.0) |
| wiki/INDEX.md | REPLACED (Dataview) |
| wiki/_meta/audit_report_2026-04-13.md | CREATED |
| wiki/_meta/obsidian-plugins.md | CREATED |
| wiki/_meta/graph-config.json | CREATED |
| wiki/_meta/migration_report_2026-04-13.md | CREATED |
| wiki/concepts/*.md | CREATED (12) |
| wiki/entities/*.md | CREATED (11) |
| wiki/projects/*.md | CREATED (4) |
| wiki/decisions/*.md | CREATED (76) |
| wiki/architecture/*.md | CREATED (10) |
| wiki/timelines/*.md | CREATED (6) |
| wiki/people/*.md | CREATED (1) |
| wiki/raw/**/* | COPIED (170+) |

---

## Migration Complete: 2026-04-13
