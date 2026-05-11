# Weekly Synthesis — obsidian-mind /om-weekly

## What It Does

Cross-session synthesis for the past week:

1. **North Star Alignment** — Check progress against goals in brain/North Star.md
2. **Patterns** — Identify recurring patterns from brain/Patterns.md and work notes
3. **Wins** — Tally wins from perf/Brag Doc.md since last weekly
4. **Decisions Made** — Review brain/Key Decisions.md
5. **Next Week Priorities** — Suggest based on blockers and goals

## When to Use

Weekly, or when you say "weekly", "weekly review", or "what did we do this week".

## Expected Output

```
Weekly Synthesis — Week of 2026-05-01 to 2026-05-08
==================================================

North Star Alignment:
[ ] Goal 1 — 80% complete
[X] Goal 2 — Done
[ ] Goal 3 — Blocked on X

Patterns Observed:
- API contract reviews take 2 days longer than expected
- 1:1s consistently surface blockers within 24h

Wins This Week:
- Auth architecture praised by Sarah
- Deployed error monitoring for Alpha
- Completed 3 PR reviews

Decisions Made:
- Defer Redis migration to Q2
- Add error monitoring before auth release

Next Week Priorities:
1. Complete API contract for Alpha
2. Schedule follow-up 1:1 with Sarah
3. Review Redis migration scope for Q2
```

## Notes for Claude

- Use Obsidian MCP to read notes from work/, brain/, perf/
- Scan git log for the week: `git log --since="1 week ago" --oneline`
- Parse work notes' frontmatter for status updates
- Update brain/North Star.md if goals changed
