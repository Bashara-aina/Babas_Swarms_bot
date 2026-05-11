# People Profiler Subagent

## Purpose

Bulk creates or updates person notes from profile data (Slack, GitHub, etc.).

## Invoked By

- `/om-incident-capture` — after incident creates people notes
- `/om-dump` — when new person mentioned

## How It Works

1. Takes person profile data (name, role, team, contact)
2. Checks if org/people/[slug].md exists
3. Creates or updates note with consistent frontmatter
4. Links to related work notes

## Input Format

```
/people-profiler
Name: Sarah Chen
Role: Engineering Manager
Team: Platform Team
Contact: sarah@company.com
Context: Met at 1:1, interested in system reliability
```

## Expected Actions

1. Create/update `org/people/sarah-chen.md` with template
2. Add context about the person
3. Link to any related work notes
4. Update org/People & Context.md index if new person

## Output Format

```
# People Profiler

## Updated: Sarah Chen

Note: [[org/people/sarah-chen.md]]
Created: 2026-05-01
Last Updated: 2026-05-08

Key Interactions:
- 2026-05-05: 1:1 — praised auth, wanted error monitoring
- 2026-05-01: Initial meeting

Links Added:
- [[work/active/auth-refactor]]
- [[work/1-1/sarah-chen-2026-05-05]]

Index Updated: [[org/People & Context.md]]
```

## Notes for Claude

- Always use person template
- Normalize name to lowercase slug for filename
- Add at least one link to related work
- Update People & Context.md MOC