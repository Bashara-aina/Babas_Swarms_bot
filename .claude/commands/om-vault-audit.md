# Vault Audit — obsidian-mind /om-vault-audit

## What It Does

Deep vault maintenance check:

1. **Orphan Detection** — Find notes with no incoming or outgoing links
2. **Broken Links** — Check for dead wikilinks
3. **Stale Content** — Find notes not updated in 30+ days
4. **Frontmatter Check** — Verify all work notes have required fields
5. **Index Sync** — Verify brain/Memories.md is current

## When to Use

Weekly or when you say "audit", "vault health", or "check the wiki".

## Expected Output

```
Vault Audit — 2026-05-08
=======================

Orphan Notes:
- wiki/notes/untitled.md (delete or link)
- work/thinking/old-idea.md (promote or delete)

Broken Links:
- None ✓

Stale Notes (30+ days):
- brain/Old Pattern.md (last updated 2026-03-01)
- work/incidents/old-incident.md (last updated 2026-02-15)

Frontmatter Issues:
- work/active/missing-status.md (missing 'status' field)

Index Sync:
- brain/Memories.md needs update for new topic "Redis Migration"

Actions Needed:
1. Delete or link 2 orphan notes
2. Update or archive 2 stale notes
3. Fix frontmatter in 1 work note
```

## Notes for Claude

- Run Obsidian search to find orphans: notes with no links
- Use Obsidian MCP to check frontmatter
- Run the wiki_health.py script from .claude/scripts/
- Update compile_state.json after audit
