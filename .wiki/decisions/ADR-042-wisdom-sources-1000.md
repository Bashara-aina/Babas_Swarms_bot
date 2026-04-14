---
title: Adr 042 Wisdom Sources 1000
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: Review of 20 wiki domain files (wisdom/domains/) revealed systematic quality
  issues that must be addressed before the wisdom corpus can be considered authoritative.
wikilinks: []
confidence: medium
source: research
---
# ADR-042: Wisdom Sources Quality Requirements

## Status
Accepted: 2026-04-11

## Context
Review of 20 wiki domain files (wisdom/domains/) revealed systematic quality issues that must be addressed before the wisdom corpus can be considered authoritative.

## Issues Identified

### Blockers

#### 1. Skip List Violation
Multiple skip list authors appear as PRIMARY entries, violating explicit instruction:

| Author | Files | Skip List Reason |
|--------|-------|------------------|
| Charlie Munger | 08 | Mental models investor |
| Gary Klein | 03, 08 | Decision-making researcher |
| Howard Marks | 03, 19 | Investor/author |
| Howard Raiffa | 03 | Decision analyst |
| Annie Duke | 03, 19 | Decision poker player |
| Peter Thiel | 10, 18 | Startup investor |
| Eric Ries | 10, 12, 18 | Lean Startup author |
| Viktor Frankl | 08 | Meaning author |
| Jeff Bezos | 10 | Amazon founder |
| Elon Musk | 10 | Tech founder |
| Cal Newport | 18, 19 | Deep Work author |

**Note**: Aristotle, Feynman, Marcus Aurelius appear LEGITIMATELY in domains 06 (Physics), 09 (Communication - rhetorical example), 14 (Ethics), 15 (History) as foundational thinkers.

**Decision**: These names should NOT appear as standalone primary entries. They may appear in:
- Conflicts sections
- References within other entries
- Domain 06 (Physics) for Feynman
- Domain 14 (Ethics) for Aristotle
- Domain 15 (History) for Aristotle, Marcus Aurelius

#### 2. LEGION RULE Placeholder Text
753 instances of "do Y because Z" using literal placeholders instead of specific content.

**Affected Files**: 01, 03, 04, 05, 11, 12, 14, 15

**Correct Format Required**:
```
LEGION RULE: When [situation], do [specific action] because [specific mechanism].
```

**NOT**:
```
LEGION RULE: When [situation], do Y because Z ([explanation]).
```

## Requirements for Approval

### Must Have
1. No skip list names as primary entries
2. LEGION RULE properly formatted with specific Y and Z content
3. All required fields present (Author, Type, Year, Core Insight, LEGION RULE, Applied to Bashara, Conflicts)

### Should Have
1. Consistent entry format across all files
2. Verified source titles
3. No encoding artifacts

## Consequences

### If Not Fixed
- Wisdom corpus cannot be used as authoritative source for agent decisions
- LEGION RULES will produce meaningless guidance ("do Y because Z")
- Skip list names create inappropriate emphasis on certain thinkers

### When Fixed
- 1000+ sources will form reliable wisdom backbone
- LEGION RULES provide specific, actionable guidance
- Diverse, balanced intellectual foundations across 20 domains

## Review History
- 2026-04-11: Initial review - BLOCKERS identified
