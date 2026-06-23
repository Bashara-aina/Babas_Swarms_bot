---
name: vault-librarian
description: Deep vault maintenance — finds and fixes orphans, broken links, and stale content.
type: agent
---

# Vault Librarian Subagent

## Purpose

Deep vault maintenance — finds and fixes orphans, broken links, and stale content.

## Invoked By

- `/om-vault-audit` — comprehensive vault check

## How It Works

1. Scans for orphans (no links)
2. Checks for stale notes (30+ days old)
3. Verifies frontmatter completeness
4. Reports index sync status

## Output Format

```
# Vault Librarian Report

## Vault Statistics
- Total Notes: 147
- Orphan Candidates: 4
- Stale Notes (30+ days): 6
- Missing Frontmatter: 2

## Orphan Details

### thinking/draft-2026-03.md
Last Updated: 2026-03-01
Recommendation: Promote to work/active/ or delete
Action: link to [[work/active/auth-refactor]]

### notes/old-notes.md
Last Updated: 2026-02-15
Recommendation: Archive or delete
Action: No related work found, suggest deletion

## Stale Notes

| Note | Last Updated | Status |
|------|--------------|--------|
| brain/Old-Pattern.md | 2026-03-01 | Review for archive |
| work/incidents/old-incident.md | 2026-02-15 | Archive |

## Index Issues

- brain/Memories.md — missing 2 new topics from last session
- perf/Brag Doc.md — needs Q2 wins update

## Recommended Actions

1. Delete 2 orphan notes
2. Archive 3 stale notes
3. Update brain/Memories.md
4. Fix frontmatter in 2 work notes
```

## Notes for Claude

- Run with --fix to auto-apply fixes (with approval)
- Don't auto-delete — always report and ask
- Update indexes as part of maintenance