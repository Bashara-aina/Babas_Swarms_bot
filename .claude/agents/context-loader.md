---
name: context-loader
model: deepseek-v4-flash
tools: ["Read", "Grep", "Glob", "Bash"]
description: Loads all vault context about a person, project, or concept used before deep work.
type: agent
---

# Context Loader Subagent

## Purpose

Loads all vault context about a person, project, or concept. Used before deep work.

## Invoked By

- Direct request: "Tell me about Sarah"
- Before starting work on a known project
- Before 1:1 prep: `/om-prep-1on1`

## How It Works

1. Takes a query (person name, project, or concept)
2. Searches brain/, work/, org/ for relevant notes
3. Aggregates findings into a coherent context brief

## Usage

```
Load context about: Sarah Chen
```

## Output Format

```
# Context: Sarah Chen

## Summary
Engineering Manager, Platform Team. Last接触 2026-05-05.

## Person Note
[[org/people/sarah-chen]] — role, team, relationship history

## Recent Interactions
- 2026-05-05: 1:1 — praised auth architecture, wanted error monitoring
- 2026-05-01: 1:1 — discussed Q2 priorities

## Active Projects
- Auth Refactor — Sarah is stakeholder
- Error Monitoring — Sarah requested

## Key Preferences
- Prefers async updates
- Values concrete examples
- Interested in system reliability

## Related Decisions
- Defer Redis migration to Q2 (Sarah mentioned)

## Evidence Links
- [[work/1-1/sarah-chen-2026-05-05]]
- [[perf/brag/2026-q2]] (praised auth)
```

## Notes for Claude

- Use QMD semantic search if available: `qmd query "Sarah Chen"`
- Read from: org/people/, work/1-1/, work/active/, brain/
- Aggregate across multiple notes
- Mark confidence level for facts from different sources