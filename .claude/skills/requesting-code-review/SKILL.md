---
name: requesting-code-review
description: >-
  Pre-review checklist before asking for human review. Runs self-review, diff
  review, and impact analysis. Use before submitting changes for human review.
---

## Phase 1: Self-Review

Check all items before proceeding:
- [ ] All tests pass (`make check`)
- [ ] No debug code, console.log stubs, or TODO markers
- [ ] No commented-out code
- [ ] Error handling covers expected failure modes
- [ ] No secrets leaked (API keys, tokens, credentials)
- [ ] Files under 500 lines
- [ ] Naming consistent with project conventions
- [ ] New code has tests

## Phase 2: Diff Review

1. Read `git diff` and verify each hunk is intentional
2. Run `gitnexus_impact` on changed symbols — check for HIGH/CRITICAL warnings
3. Verify scope matches original plan

## Phase 3: Generate Review Artifact

Save review summary to `.claude/reviews/review-YYYY-MM-DD-HHmm.md`:
- Checklist pass/fail
- Diff summary (files changed, lines added/removed)
- Impact analysis results
- Any blocking issues

## Phase 4: Present to User

Show the review artifact and ask: "Ready for human review?"
If blocking issues remain, do NOT recommend human review.
