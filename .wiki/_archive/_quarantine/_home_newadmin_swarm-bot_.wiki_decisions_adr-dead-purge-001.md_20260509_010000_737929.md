---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/decisions/adr-dead-purge-001.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-09T01:00:00.737948"
}
---

---
title: Adr Dead Purge 001
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
summary: 'The `/home/newadmin/swarm-bot` repository has accumulated dead files over
  time:'
wikilinks: []
confidence: medium
source: research
---
The `/home/newadmin/swarm-bot` repository has accumulated dead files over time:
- Backup files (`.bak`, `.backup`)
- Old installers (`.deb`)
- Invalid filenames (`=0.23.0`)
- Potentially orphaned Python modules, agents, handlers
- Unused test files

Before any deletion, we need a **safe, reversible, well-documented process**.
---


## Decision: Graveyard Pattern + 3-Pass Confirmation

### Graveyard Pattern
Instead of immediate deletion (`rm`), all confirmed-dead files are:
1. **Moved** to `_graveyard/YYYYMMDD/` directory
2. **Logged** in `CLEANUP_LOG.md` with reason and pass number
3. **Retained** for 30 days before permanent deletion

**Rationale**: Provides rollback capability. If a file was mistakenly marked dead, it can be recovered from the graveyard.

### 3-Pass Confirmation Protocol

| Pass | Name | Purpose |
|------|------|---------|
| Pass 1 | Static Import Analysis | Find files with zero import references |
| Pass 2 | Runtime/Dynamic Check | Verify file isn't used dynamically or at runtime |
| Pass 3 | Future Use Check | Search for TODO comments, docs, roadmaps referencing the file |

A file must pass **all 3 passes** to be considered confirmed-dead.

---

## Whitelist (Never Delete)

To prevent accidental deletion of critical files:

```
Config/Build:
- package.json, .eslintrc.json, jest.config.js, components.json
- postcss.config.mjs, next.config.mjs, tailwind.config.ts, tsconfig.json
- pyproject.toml, requirements*.txt, Makefile, docker-compose.yml

Environment:
- .env, .env.* (NEVER edit, only move to graveyard if truly dead)

Documentation:
- README.md, CONTRIBUTING.md, LICENSE
- AGENTS.md, CLAUDE.md

Testing:
- __tests__/*, tests/*, conftest.py

Data/Config:
- .wiki/, config/, data/, logs/, papers/, skills/, prompts/, scripts/
- supabase/*

Infrastructure:
- .git/, .github/, .vscode/, .cursor/
- .pre-commit-config.yaml, .gitmodules
```

---

## Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 0: Git Checkpoint + Graveyard Setup + Log Init       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Pass 1 — Static Import Analysis                   │
│   - Find .py files never imported                          │
│   - Find non-Python files never referenced                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Pass 2 — Runtime/Dynamic Usage Check               │
│   - Parse AST for dynamic imports                          │
│   - Check main entry points for usage                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: Pass 3 — Future Use Check                         │
│   - Search TODO/FIXME/XXX comments                         │
│   - Check documentation references                         │
│   - Check roadmap files                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGES 4-6: Pattern Hunters                                 │
│   - Unused agents, handlers, core modules                 │
│   - Unused tools, libraries                                │
│   - Orphaned test files                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 7: Move Confirmed Dead to Graveyard                  │
│   - mv (NOT rm) to _graveyard/YYYYMMDD/                   │
│   - Log each file in CLEANUP_LOG.md                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 8: Cleanup + Final Commit                            │
│   - Update .gitignore                                      │
│   - Clean cache files                                      │
│   - Git commit with full log                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive
- Clean repository with no dead files
- Reversible process (graveyard rollback)
- Full audit trail in CLEANUP_LOG.md
- 3-pass confirmation prevents accidental deletion

### Negative/Risks
- Some analysis may produce false positives (file referenced by string, not import)
- Manual review required at each pass
- 30-day retention uses disk space for dead files

### Mitigation
- Conservative whitelist (when in doubt, don't delete)
- Manual verification step before each deletion
- Git checkpoint before any changes

---

## Retention Policy

| Location | Retention | Deletion Method |
|----------|-----------|-----------------|
| `_graveyard/YYYYMMDD/` | 30 days | `find _graveyard -type f -mtime +30 -delete` |
| `CLEANUP_LOG.md` | Permanent | Never delete |

---

## Files Modified/Created

| File | Action |
|------|--------|
| `_graveyard/20260411/` | Created (directory) |
| `CLEANUP_LOG.md` | Created |
| `.gitignore` | May be updated |
| `[dead_files]` | Moved to graveyard |

---

## Rollback Procedure

```bash
# 1. Restore from git
git checkout HEAD -- .

# 2. Restore specific file from graveyard
mv _graveyard/20260411/<filename> .

# 3. Verify restoration
git status
```

---

## Related Decisions

- None (this is a standalone cleanup operation)

---

## Review Triggers

After this operation, the following should be verified:
1. Bot still starts: `python main.py`
2. Tests still pass: `pytest tests/ -x --asyncio-mode=auto -q`
3. No import errors on startup
