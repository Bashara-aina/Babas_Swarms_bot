---
name: systematic-debugging
description: >-
  Structured 4-phase debugging process: reproduce, hypothesize, instrument,
  fix. Enhanced with spec cross-checking from the Superpowers workflow.
  Use when fixing bugs, investigating failures, or troubleshooting.
---

This skill extends the `diagnose` skill with Superpowers workflow integration.

## Pre-Debug: Spec Cross-Check

Before debugging, check if the code came from a plan:
1. Search `.superpowers/plans/` for relevant plan files
2. Search `.superpowers/specs/` for relevant spec files
3. If found, re-read the spec to confirm understanding of intended behavior

## Phase 1: Reproduce

1. Get the exact error message or failure output
2. Create minimal reproduction — one command, one script
3. Confirm the bug is real and consistent

## Phase 2: Hypothesize

1. List 2-3 possible root causes with evidence for each
2. Check `gitnexus_impact` on affected symbols
3. Rank hypotheses by likelihood

## Phase 3: Instrument

1. Add targeted logging or assertions
2. Run the reproduction to gather data
3. Confirm root cause

## Phase 4: Fix

1. Write the fix
2. Add regression test (RED → GREEN)
3. Run `make check`
4. If fix requires design change, recommend re-running `brainstorming`

## Post-Debug: Learn

Record what was learned to `.superpowers/homunculus/observations/` (if continuous learning is active).
