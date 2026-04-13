# ADR-089: Repository Cleanup 2026-04-12

**Date**: 2026-04-12  
**Status**: Accepted  
**Deciders**: @worker, @reviewer  

## Context

The repository had accumulated several categories of stale, consumed, and obsolete files:
- One-time master prompt files (LEGION_*.md consumed prompts)
- Duplicate AGENTS.md files in subdirectories
- Obsolete audit/report files (AUDIT_*, INTEGRATION_*, PRODUCTION_HARDENING_REPORT.md)
- Outdated prompts/master_v4.md
- Obsolete .github/workflows/copilot-masterprompt.md
- Entire _graveyard/ directory (backup files >30 days old)

## Decision

**Action**: Delete all identified stale files to reduce confusion and maintenance burden.

### Files Deleted

| Category | Files | Rationale |
|----------|-------|-----------|
| Consumed master prompts | LEGION_WIRING_AUDIT_PROMPT.md, LEGION_NIHONGO_MODE.md, LEGION_FIX_IDENTITY_SEARCH.md, LEGION_VOICE_UPGRADE.md, LEGION_OPENCODE_AUDIT.md, LEGION_WIKI_LOOP.md, LEGION_CLAWCODE_UPGRADE.md, LEGION_MCP_SKILLS_MASTER.md | One-time prompts consumed during implementation |
| One-time audit docs | AUDIT_NOW.md, AUDIT_REPORT.md, DEEP_AUDIT_2026-04-10.md, INTEGRATION_REPORT.md, INTEGRATION_RUN.txt, PRODUCTION_HARDENING_REPORT.md | Superseded by current documentation |
| Outdated prompts | prompts/master_v4.md | Replaced by current master prompt system |
| Obsolete workflows | .github/workflows/copilot-masterprompt.md | No longer used |
| Backup directory | _graveyard/ (entire directory) | Files >30 days old, no longer needed |
| Duplicate AGENTS.md | Multiple subdirectory copies | Redundant with root AGENTS.md |

### Files Retained

| File | Rationale |
|------|-----------|
| LEGION_MASTER.md | Active master reference, actively used |
| LEGION_PRODUCTION_HARDENING.md | Current production hardening documentation |
| skills/AGENTS.md | Legitimate context file describing skills directory |
| AGENTS.md (root) | Primary agent registry documentation |

## Consequences

### Positive
- Reduced file count by ~27 files
- Cleaner repository structure
- Less confusion about which docs are current

### Negative
- Historical context in deleted logs may be harder to trace
- Some audit history in .wiki/logs references deleted files

## Review Notes

- ✅ All specified files successfully deleted
- ✅ _graveyard/ directory removed
- ⚠️ prompts/__init__.py docstring references deleted master_v4.md (needs update)
- ✅ No code imports reference deleted files
- ✅ README.md updated appropriately
