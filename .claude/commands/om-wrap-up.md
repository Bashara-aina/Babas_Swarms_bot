# End of Day Wrap Up — obsidian-mind /om-wrap-up

## What It Does

Runs a session review checklist:

1. **Note Verification** — Checks that all notes created today have valid frontmatter and wikilinks
2. **Index Updates** — Updates brain/Memories.md if new topics were added
3. **Link Check** — Identifies notes without any links (orphans)
4. **Brag Spotter** — Scans conversation for uncaptured wins
5. **Suggestions** — Identifies improvements for next session

## When to Use

When you say "wrap up", "end of day", "done for today", or "shutdown".

## Expected Output

```
End of Day Wrap Up
=================

Notes Created/Updated Today:
- work/1-1/Sarah 2026-05-08.md ✓
- brain/Key Decisions/2026-05-08-defer-redis-migration.md ✓
- perf/Brag Doc.md ✓

Link Check:
- All notes have wikilinks ✓
- No orphan notes ✓

Uncaptured Wins:
- None found

Suggestions for Tomorrow:
- Follow up on error monitoring task for auth refactor
- Schedule API contract review meeting
```

## Notes for Claude

- Run the wiki_health.py script to check for orphans and broken links
- Update compile_state.json after wrap up
- If there are orphans, create links to relevant existing notes
- Write a session summary to /tmp/legion_session_summary.txt
