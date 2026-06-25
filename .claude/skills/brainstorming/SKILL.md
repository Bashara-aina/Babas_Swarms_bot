---
name: brainstorming
description: >-
  Socratic design refinement before coding. Explores user intent, requirements,
  and design before any implementation. Use when creating features, building
  components, adding functionality, or modifying behavior.
---

Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it.

## Checklist

Complete these items in order:

1. **Explore project context** — check files, docs, recent commits. If modifying existing code, run `gitnexus_impact` on affected symbols.
2. **Ask clarifying questions** — one at a time. Understand purpose, constraints, success criteria.
3. **Propose 2-3 approaches** — with trade-offs and your recommendation.
4. **Present design** — in sections scaled to their complexity. Get user approval after each section.
5. **Write spec** — save to `.superpowers/specs/YYYY-MM-DD--design-slug.md` using the template below.
6. **Self-review spec** — check for placeholders, contradictions, ambiguity, scope.
7. **User reviews written spec** — ask user to review before proceeding.
8. **Transition to implementation** — invoke `writing-plans` skill. Do NOT invoke any other skill.

## Spec Template

```markdown
# Title

**Date:** YYYY-MM-DD
**Status:** Draft

## Problem Statement
What are we solving and why?

## Chosen Approach
Which approach was selected and why were alternatives rejected?

## Architecture
Modules, components, and their responsibilities.

## Data Flow
How data moves through the system.

## Files to Create/Modify
- `path/to/file` — what changes

## Open Questions
- [ ] Question 1
- [ ] Question 2

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

## Key Principles
- One question at a time
- Propose 2-3 approaches before settling
- YAGNI ruthlessly — remove unnecessary features
- Incremental validation — present design, get approval before moving on
