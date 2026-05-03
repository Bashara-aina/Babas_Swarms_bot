---
title: Readme
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Architecture Decision Records (ADR)
# =====================================
# Index of all ADRs for the swarm-bot project.
# Each ADR documents a significant architectural decision.
# Format: ADR-[NNN]-[short-slug].md

## INDEX (newest first)

| Date | ID | Title | Status |
|------|----|-------|--------|
| 2026-04-12 | ADR-001 | Anti-Slop UI System | Active |
| 2026-04-13 | ADR-002 | Async Error Handling | Active |
| 2026-04-13 | ADR-003 | Dual Router Conflict Resolution | Active |
| 2026-04-13 | ADR-004 | Minimax Over Claude for Primary Model | Active |
| 2026-04-13 | ADR-005 | OpenCode Integration | Active |
| 2026-04-13 | ADR-006 | Wiki Build Strategy | Active |
| 2026-04-13 | ADR-007 | Circuit Breaker Design | Active |
| 2026-04-13 | ADR-008 | Consolidate Agent Registries | Active |
| 2026-04-13 | ADR-009 | GSA Voice Implementation | Active |
| 2026-04-13 | ADR-010 | OpenCode Agents Autostart | Active |
| 2026-04-13 | ADR-011 | API Key Fix | Active |
| 2026-04-13 | ADR-012 | Archive Cekwajar Planning | Active |
| 2026-04-13 | ADR-013 | Coding References Pipeline | Active |
| 2026-04-13 | ADR-014 | Legion Fix Identity Search | Active |
| 2026-04-13 | ADR-015 | Phase 2 Implementation | Active |
| 2026-04-13 | ADR-016 | Smoke Test Results | Active |
| 2026-04-13 | ADR-017 | Legion Bot Smoke Testing | Active |
| 2026-04-13 | ADR-018 | Legion Bot GitHub Issue #57553939 | Active |

## DECISION DOMAINS

### Memory Architecture
- ADR-001 through ADR-005 cover memory system choices

### Bot Architecture
- ADR-006 through ADR-010 cover Legion bot core design

### OpenCode Integration
- ADR-005, ADR-010, ADR-014, ADR-017

### Infrastructure
- ADR-007 (circuit breaker), ADR-008 (agent registries), ADR-011 (security)

## HOW TO ADD A NEW ADR

1. Create file: `.wiki/decisions/ADR-[NNN]-[short-slug].md`
2. Use this frontmatter template:
   ```yaml
   ---
   id: ADR-[NNN]
   title: [Full Title]
   date: YYYY-MM-DD
   status: proposed | accepted | superseded | deprecated
   tags: [relevant, tags]
   affects: [what this decision impacts]
   ---
   ```
3. Add entry to this index table above
4. Run: python3 .claude/scripts/update_compile_state.py
5. Git commit with message: `docs(adr): ADR-[NNN] [short description]`

## DECISION QUALITY CRITERIA

A good ADR:
- States the problem being solved (not the solution)
- Lists all considered alternatives with pros/cons
- Explains the final decision and its rationale
- Notes any future implications or rollback conditions
- Is no longer than 500 words (prefer 200-300)

## MAINTENANCE

- Review superseded ADRs annually
- Mark deprecated decisions with rationale
- Link related ADRs via wikilinks in each document
