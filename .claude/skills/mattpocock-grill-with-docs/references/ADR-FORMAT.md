# ADR Format

Architecture Decision Record format.

## Purpose

ADRs capture significant architectural decisions — the context, alternatives considered, and reasoning behind the choice.

## When to Write an ADR

Only when all three are true:
1. **Hard to reverse** — cost of changing later is meaningful
2. **Surprising without context** — future reader will wonder "why?"
3. **Result of real trade-off** — genuine alternatives existed

## Format

```markdown
# ADR-[NUMBER]: [Title]

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | deprecated | superseded

## Context

[What is the issue? What's the current state? Why is this being discussed?]

## Decision

[What is the decision that was made?]

## Alternatives

### Alternative 1: [Name]
[Description of the alternative]
**Pros:** [Pros]
**Cons:** [Cons]

### Alternative 2: [Name]
...

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Downside 1]
- [Downside 2]
```

## Example

```markdown
# ADR-001: Use event sourcing for Order aggregate

**Date:** 2024-01-15
**Status:** accepted

## Context

We need to track the full history of Order state changes for audit and debugging. The current approach of snapshots doesn't capture the sequence of events that led to current state.

## Decision

Use event sourcing for the Order aggregate. Order changes are captured as immutable events in an `OrderEvent` table.

## Alternatives

### Alternative 1: Snapshot-based history
Store current state plus change log in a single table.
- **Pros:** Simple to implement, familiar pattern
- **Cons:** Doesn't capture intent, hard to rebuild state at arbitrary points

### Alternative 2: Full event sourcing with CQRS
Separate read and write models with event bus.
- **Pros:** Maximum flexibility, great audit trail
- **Cons:** Higher complexity, eventual consistency challenges

## Consequences

### Positive
- Complete audit trail of all Order state changes
- Can rebuild Order state at any point in time
- Enables temporal queries ("what was this order like last week?")

### Negative
- Requires learning event sourcing patterns
- Event schema evolution (upcasting) adds complexity
```

## File Naming

```
docs/adr/
├── 0001-event-sourced-orders.md
├── 0002-postgres-for-write-model.md
└── ...
```

Use zero-padded numbers. Higher number = more recent decision.