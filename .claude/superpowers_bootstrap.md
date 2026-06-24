---
name: superpowers_bootstrap
description: Superpowers SDLC methodology -- auto-injected at session start
mode: bootstrap
hidden: true
---

# SUPERPOWERS SDLC METHODOLOGY -- ACTIVE

## Workflow Priority
1. ALWAYS check available skills first (they are listed in system reminders)
2. Follow: brainstorming -> writing-plans -> executing-plans -> tdd -> requesting-code-review -> finishing-a-development-branch
3. When uncertain or requirements are ambiguous -> run brainstorming
4. When design is approved -> run writing-plans
5. When tasks are defined -> run executing-plans
6. Before asking for human review -> run requesting-code-review
7. When branch is complete -> run finishing-a-development-branch

## Data Locations
- Specs: .superpowers/specs/
- Plans: .superpowers/plans/
- Review artifacts: .claude/reviews/
- Observations: .superpowers/homunculus/observations/

## Red Flags (slow down when these appear)
- You haven't read the relevant files yet
- You're modifying more than 3 files without a plan
- Requirements are ambiguous
- There's no test for the code you're writing
- You haven't checked gitnexus_impact for changed symbols
