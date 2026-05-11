# Review Brief — obsidian-mind /om-review-brief

## What It Does

Generates a review brief by aggregating all evidence for a review period.

## When to Use

Before performance reviews, 1:1s with manager, or peer reviews.

## Usage

```
/om-review-brief manager
Cycle: 2026-Q2
Person: Sarah Chen
```

## Expected Output

```
Review Brief — Sarah Chen — 2026-Q2
====================================

Competency: System Design
Evidence:
- [[work/incidents/2026-04-15-cache-outage]] — Led incident response
- [[work/active/auth-refactor]] — Designed scalable auth system
- [[perf/brag/2026-Q2]] — Sarah praised architecture

Rating: Exceeds Expectations

Competency: Communication
Evidence:
- [[work/1-1/2026-05-01-sarah]] — Clear status updates
- [[work/incidents/2026-04-15]] — Effective incident comms

Rating: Meets Expectations

Summary:
Sarah has demonstrated strong system design skills and effective
communication. Key wins include the auth architecture and incident response.
```

## Notes for Claude

- Query perf/competencies/ for the competency framework
- Aggregate evidence from work notes' backlinks
- Read perf/brag/ for win documentation
- Check org/people/ for 360 feedback
- Use QMD to find related notes if available
