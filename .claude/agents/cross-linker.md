---
name: cross-linker
model: deepseek-v4-flash
tools: ["Read", "Grep", "Glob", "Bash"]
description: Finds missing wikilinks, orphan notes, and broken backlinks during vault audits.
type: agent
---

# Cross-Linker Subagent

## Purpose

Finds missing wikilinks, orphan notes, and broken backlinks. Used during vault audits.

## Invoked By

- `/om-vault-audit` — vault health check
- `/om-wrap-up` — link verification

## How It Works

1. Scans all notes for wikilinks
2. Checks each link target exists
3. Finds notes with no incoming links (orphans)
4. Suggests relevant links for orphans

## Output Format

```
# Cross-Linker Report

## Broken Links

| File | Broken Link | Suggested Fix |
|------|-------------|----------------|
| brain/Patterns.md | [[nonexistent-note]] | Link to [[brain/Gotchas]] |
| work/active/auth.md | [[org/people/sarah]] | Link to [[org/people/Sarah Chen]] |

## Orphan Candidates

| Note | Last Updated | Suggested Links |
|------|--------------|-----------------|
| thinking/old-idea.md | 2026-03-01 | Link to [[work/active/auth-refactor]] or delete |
| notes/untitled.md | 2026-04-15 | Promote to [[work/active/]] or delete |

## Missing Cross-Links

- brain/Key Decisions/2026-05-08-defer-redis.md → should link to [[work/active/auth-refactor]]
- work/1-1/sarah-2026-05-05.md → should link to [[org/people/sarah-chen]]

## Action Items

- [ ] Fix 2 broken links
- [ ] Link or delete 2 orphan notes
- [ ] Add 3 cross-links
```

## Notes for Claude

- Use Obsidian search to find all notes
- Check WIKI_DIR for file existence
- Match orphans to relevant active notes when possible
- Report but don't auto-delete — user approves deletions