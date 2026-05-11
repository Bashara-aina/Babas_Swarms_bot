# Self Review — obsidian-mind /om-self-review

## What It Does

Writes a self-assessment for review season.

## When to Use

During performance review cycles.

## Usage

```
/om-self-review
Cycle: 2026-Q2
```

## Expected Output

```
Self Review — 2026-Q2
=====================

Projects Completed:
1. Auth Refactor — designed and implemented new auth system
2. Error Monitoring — added observability to all services
3. API Contract — defined and documented API contracts

Competencies Demonstrated:

System Design (Level 3 → Level 4)
- Led auth refactor architecture
- Designed extensible error handling system
- Evidence: work/active/auth-refactor, work/incidents/

Communication (Level 3 → Level 3)
- Ran 5+ API review sessions
- Documented 3 major decisions with ADRs
- Evidence: brain/Key Decisions/, work/1-1/

Wins:
- Sarah praised auth architecture
- Reduced P1 incidents by 50%
- Shipped error monitoring 2 weeks ahead of schedule

Growth Areas:
- Want to improve documentation
- Plan to mentor junior engineers

Evidence Sources:
- perf/Brag Doc.md
- brain/Key Decisions/
- work/1-1/
- Git log
```

## Notes for Claude

- Aggregate from perf/Brag Doc.md
- Use work/active/ for project evidence
- Use brain/Key Decisions/ for decision evidence
- Use work/1-1/ for feedback evidence
- Check git log for commit summary
- Link all evidence to source notes
