# Prepare for 1:1 — obsidian-mind /om-prep-1on1

## What It Does

Prepares context for an upcoming 1:1 meeting.

## When to Use

Before a 1:1 with your manager, peer, or reports.

## Usage

```
/om-prep-1on1
Person: Sarah Chen
```

## Expected Output

```
Prep for 1:1 with Sarah Chen
============================

Last 1:1: 2026-05-01 (7 days ago)
Last 1:1 Takeaways:
- Happy with auth progress
- Wanted error monitoring before release
- Action: Add error monitoring → Done

Open Items from Previous 1:1s:
- [X] Add error monitoring — Done
- [ ] Schedule API contract review — Pending
- [ ] Send revised timeline — Pending

Recent Wins (since last 1:1):
- Deployed error monitoring
- Auth refactor complete
- Sarah praised architecture (2026-05-05)

Recent Decisions:
- Defer Redis migration to Q2
- Add circuit breakers to cache

People & Context on Sarah:
- Role: Engineering Manager
- Team: Platform Team
- Last flagged: observability concerns
- Key interests: system reliability, documentation

Suggested Agenda:
1. Redis migration Q2 scope (5 min)
2. API contract review meeting (10 min)
3. Career growth / leveling (10 min)
4. Any blockers? (5 min)

Notes from org/people/sarah.md:
- Prefers async updates over long meetings
- Values concrete examples over abstract discussion
```

## Notes for Claude

- Read org/people/{Person}.md for context
- Read previous 1:1 notes from work/1-1/
- Parse action items from previous notes
- Aggregate wins and decisions since last 1:1
- Use brain/Memories.md to find related topics
