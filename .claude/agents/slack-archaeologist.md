---
name: slack-archaeologist
model: deepseek-v4-flash
description: Deep scan of Slack channels/DMs for evidence used by /om-incident-capture.
type: agent
---

# Slack Archaeologist Subagent

## Purpose

Deep scan of Slack channels/DMs for evidence. Used by /om-incident-capture.

## Invoked By

- `/om-incident-capture` — to reconstruct incident timeline
- `/om-peer-scan` — for review prep

## How It Works

1. Takes a Slack channel/DM URL or name
2. Uses Hermes MCP to read conversation history
3. Reconstructs timeline, decisions, and people involved
4. Outputs structured notes for vault ingestion

## Usage

```
/slack-archaeologist
Channel: #incidents
Date Range: 2026-05-01 to 2026-05-08
Focus: Incident response for cache crash
```

## Output Format

```
# Slack Archaeological Report

Channel: #incidents
Date Range: 2026-05-01 to 2026-05-08

## Timeline

| Time | User | Message |
|------|------|---------|
| 10:00 | alice | Alert: cache service down |
| 10:01 | bob | Investigating |
| 10:05 | sarah | Scaling up cache instances |
| 10:30 | bob | Root cause: memory exhaustion |
| 11:00 | sarah | Fix deployed |

## Key Decisions Made

1. Scale up cache instances (10:05) — Sarah
2. Add memory limits (10:45) — agreed in thread

## People Involved

- alice — on-call, triggered alert
- bob — investigated, identified root cause
- sarah — led fix, made scaling decision

## Quotes for Evidence

> "Root cause is memory exhaustion in cache service" — bob (10:30)
> "Scaling up instances and adding memory limits" — sarah (10:45)

## Suggested Vault Actions

- Create incident note: [[work/incidents/2026-05-08-cache-crash]]
- Update people: [[org/people/alice]], [[org/people/bob]], [[org/people/sarah]]
- Add lessons to: [[brain/Gotchas.md]]
```

## Notes for Claude

- Use Hermes MCP conversations_list and messages_read
- Reconstruct timeline in chronological order
- Extract key quotes verbatim
- Map Slack handles to org/people/ notes
- Identify decisions made in thread