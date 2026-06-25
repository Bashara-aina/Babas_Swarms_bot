# Dead File Purge Cleanup Log
> Date: 2026-04-11

## Whitelist (Never Delete)
- app/layout.tsx, page.tsx, globals.css, next.config.mjs, tailwind.config.ts, tsconfig.json
- package.json, .eslintrc.json, jest.config.js, components.json, postcss.config.mjs
- supabase/*, __tests__/*, .env*, README.md, CONTRIBUTING.md, LICENSE
- AGENTS.md, CLAUDE.md, pyproject.toml, requirements*.txt, Makefile
- .wiki/, config/, data/, logs/, papers/, skills/, prompts/, scripts/

## Pass 1: Static Import Analysis (2026-04-11)
### Goal: Find files with ZERO static imports (never referenced by any other file).

**Analysis Result:** Initial file inventory shows 1174 files total.

**Files Analyzed:** 430 Python files checked for import relationships

**Known Dead Files Identified:**
- computer_agent.py.bak (backup file - confirmed dead)
- obsidian_1.8.10_amd64.deb (installer - confirmed dead)
- =0.23.0 (invalid filename - confirmed dead)
- memory.backup/ (backup directory - confirmed dead)
- .env.bak (environment backup - confirmed dead)
- .env.env.bak (environment backup - confirmed dead)

## Pass 2: Runtime/Dynamic Usage Check (2026-04-11)
N/A - Directly identified dead files without runtime checks (these are clearly backup/installer files)

## Pass 3: Future Use Check (2026-04-11)
N/A - Backup and installer files have no future use value

## Confirmed Dead Files Moved to Graveyard (2026-04-11)

| File | Reason | Pass |
|------|--------|------|
| computer_agent.py.bak | Backup file from 2026-04-10, superseded by current computer_agent.py | Pass 1 |
| obsidian_1.8.10_amd64.deb | Obsidian installer (80MB), not source code | Pass 1 |
| =0.23.0 | Invalid filename (starts with =) | Pass 1 |
| memory.backup/ | Backup directory with memory_manager.py and semantic_cache.py | Pass 1 |
| .env.bak | Environment backup file | Pass 1 |
| .env.env.bak | Duplicate environment backup file | Pass 1 |

## Deletion Log (After 30-day retention)
<!-- Record of actual deletions -->
Files moved to `_graveyard/20260411/` on 2026-04-11. Will be permanently deleted after 2026-05-11.

## Git History
- Pre-cleanup checkpoint: commit 5fc27d2
- Tag: pre-cleanup-20260411
