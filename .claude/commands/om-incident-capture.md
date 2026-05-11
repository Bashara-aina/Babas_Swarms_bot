# Incident Capture — obsidian-mind /om-incident-capture

## What It Does

Captures an incident from Slack, chat, or description into structured incident notes.

## When to Use

After an incident, outage, or production issue.

## Usage

```
/om-incident-capture
Ticket: INC-1234
Severity: high
Role: Backend Lead
Timeline:
- 10:00 — Alert triggered
- 10:05 — Investigation started
- 10:30 — Root cause identified
- 11:00 — Fix deployed

What Happened:
The cache service crashed due to memory exhaustion.

Impact:
- 500 errors for 30 minutes
- ~1000 users affected

Resolution:
Scaled up cache instances and added memory limits.

Lessons:
- Need monitoring on cache memory
- Should have had circuit breakers
```

## Expected Actions

1. Create note at `work/incidents/YYYY-MM-DD-{slug}.md` using incident template
2. Create deep-dive note in `work/incidents/` if needed
3. Add to `perf/evidence/` if relevant to performance
4. If any people involved → update their org/people/ notes
5. Add lessons to brain/Gotchas.md if novel

## Notes for Claude

- Always create root cause analysis section
- Link to related work notes and projects
- Add to Perf Evidence if it demonstrates a competency
- Update brain/Gotchas.md with preventive lessons
