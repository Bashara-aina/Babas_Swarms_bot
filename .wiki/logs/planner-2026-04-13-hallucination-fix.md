---
title: Planner 2026 04 13 Hallucination Fix
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- `.wiki/` and `wiki/` directories exist (different locations - wiki/ is
  the target)'
wikilinks: []
confidence: medium
source: research
---
## Plan: Fix Worker Hallucination - Wiki File Verification
Date: 2026-04-13
Type: FILE_OPERATION

## Context Gathered
- `.wiki/` and `wiki/` directories exist (different locations - wiki/ is the target)
- `wiki/_meta/compile_state.json` exists but shows `"articles": 0` and epoch timestamp (WRONG)
- `wiki/SCHEMA.md` exists (285 lines, complete)
- `wiki/INDEX.md` exists (193 lines, complete)
- `wiki/_meta/migration_report_2026-04-13.md` exists (220 lines)
- `wiki/raw/` has 9 subdirectories but NO .gitkeep files
- `wiki/concepts/` has 12 concept files with frontmatter
- `wiki/entities/` has 11 entity files with frontmatter
- `wiki/projects/` has 4 project files with frontmatter
- `wiki/decisions/` has 76+ ADR files
- Found malformed wikilinks in supabase.md and legion-bot.md (commas missing)
- compile_state.json never updated after wiki creation

## Risk Assessment
- Medium risk: Some wikilinks are malformed (missing commas between items)
- Low risk: raw/ directories exist but have no .gitkeep sentinel files
- Low risk: compile_state.json has wrong data (articles: 0 vs actual ~100+)
- Low risk: migration_report_2026-04-13.md exists but may not reflect actual state

## Approach
Multi-step file-first workflow with read-back verification after every write:
1. First verify existing files are actually written (read-back sample)
2. Fix malformed wikilinks in existing files
3. Add .gitkeep to each raw/ subdirectory
4. Copy 16 source files one at a time with verification
5. Update compile_state.json with correct article counts
6. Final comprehensive verification

## Hallucination Fix Strategy
The "worker hallucination" problem = claiming files written when not. Fix:
- ALWAYS read-back after write to confirm
- ALWAYS verify file exists before claiming success
- ALWAYS use exact file counts and content as proof
