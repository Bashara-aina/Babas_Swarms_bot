# Morning Kickoff — obsidian-mind /om-standup

## What It Does

Loads context from the vault for a productive morning start:

1. Reads **brain/North Star.md** — goals and focus areas
2. Reads **work/active/** — current projects
3. Reads open tasks from **work/** notes
4. Runs `git log --oneline -10` — recent changes
5. Summarizes: "You have N active projects. X is blocked on Y. Your 1:1 with Z is at TIME."

## When to Use

At the start of every session, or when you say "start", "standup", or "kickoff".

## Expected Output

```
Morning Kickoff
==============

Active Projects: 2
- Project Alpha — blocked on API contract review
- Project Beta — on track

Recent Changes:
- abc1234 feat: add user authentication
- def5678 fix: resolve memory leak

Open Tasks:
- [ ] Complete API contract for Alpha
- [ ] Review PR #45

Your 1:1 with Sarah is at 2pm — last session she flagged observability concerns.
```

## Notes for Claude

- Use Obsidian MCP to read the vault notes
- Parse frontmatter for status and project info
- Keep the output scannable and actionable
