# ADR-091 — Looping / Swarm Commands with Time Bounds

**Date:** 2026-04-24
**Status:** Accepted
**Theme:** Loop Commands, Swarm Enhancement

## Context

The user wanted OpenCode to understand looping commands like:
```
/swarm build literaly everything and do not stop until 12 hours of looping improving everything. do not stop until then. the 12 hours looping of improvement is strict. If you are feeling already done, reiterate and looping again until 12 hours is finish.
```

Previously `/loop` supported only defaults (25 iters, 30min, $0.50) with no way to specify duration. `/swarm` was one-shot only.

## Decision

Add `--hours` flag to both `/loop` and `/swarm`, and `--iters` to `/loop` for fine-grained control. When `--hours` is passed to `/swarm`, it delegates to the autonomous loop engine with appropriately scaled bounds.

### Changes

**`core/swarm_args.py`** — Added `hours: float` field to `SwarmCommandArgs`; parse `--hours=N` and `--hours N` flags.

**`handlers/ai.py`** — Two modifications:
1. `cmd_swarm`: If `--hours` is set, route to `run_autonomous_loop()` instead of one-shot swarm, with scaled bounds (50–500 iters, $2–$50 cap).
2. `cmd_loop`: Added `_parse_loop_args()` to handle `--hours=N` and `--iters=N` flags. LoopConfig scales max_iterations and cost_ceiling based on hours.

### Scaling Table

| Hours | Max Iterations | Cost Cap |
|-------|----------------|----------|
| ≤1    | 25–50          | $0.50–$2 |
| ≤4    | 50–100         | $2–$5    |
| ≤8    | 100–200        | $5–$15   |
| ≤12   | 200–500        | $15–$50  |
| >12   | 500            | $50      |

### Usage Examples

```
/loop --hours=12 "improve cekwajar 100x"
/swarm --hours=12 "build literally everything"
/loop --hours=2 --iters=100 "benchmark analysis"
```

## Consequences

- **Positive:** User can now specify extended autonomous loops with proper safety bounds.
- **Neutral:** `/swarm --hours=N` behavior differs from one-shot swarm (loop engine vs multi-agent team).
- **Positive:** Progress notifications every 10 iterations keep user informed.