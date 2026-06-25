---
name: subagent-driven-development
description: >-
  Dispatch independent tasks to fresh subagents with two-stage review.
  Tracks progress in a durable ledger. Use for 2+ independent implementation
  tasks from a plan.
---

## Decision Tree

- 1 task → use executing-plans sequential mode
- 2-4 independent tasks → dispatch subagents, report back
- 5+ independent tasks → batch into waves of 4, dispatch per wave
- Tasks with dependencies → sequential only, no subagents

## Process

### 1. Prepare Task Briefs

For each independent task, create a brief file at `.superpowers/sdd/task-N/`:

```
.superpowers/sdd/task-N/
  brief.md       — The task from the plan, with spec context
  review.md      — Results (written by reviewer)
```

Use the template at `implementer-prompt.md` for each brief.

### 2. Dispatch Subagents

For each task, spawn a fresh Agent with:
- `subagent_type: "general-purpose"` (or specialized if needed)
- The implementer prompt with task brief embedded
- No knowledge of other tasks

### 3. Collect Results

Each subagent reports with a status code:
- **DONE** — Task complete, all verification passed
- **DONE_WITH_CONCERNS** — Complete but has non-blocking issues
- **BLOCKED** — Cannot proceed (dependency issue, missing context)
- **NEEDS_CONTEXT** — Needs clarification before proceeding

### 4. Two-Stage Review

**Stage 1 (Spec Compliance):** Does implementation match the spec?
- Run per `task-reviewer-prompt.md`
- Check all acceptance criteria are met

**Stage 2 (Code Quality):** Is the code maintainable?
- Run per `task-reviewer-prompt.md`
- Check naming, error handling, test coverage

### 5. Update Progress Ledger

Update `.superpowers/sdd/progress.md`:

```markdown
# SDD Progress — YYYY-MM-DD

| Task | Status | Reviewer Notes |
|------|--------|----------------|
| Task 1: X | ✅ DONE | — |
| Task 2: Y | ⚠️ DONE_WITH_CONCERNS | Missing edge case in validation |
| Task 3: Z | ❌ BLOCKED | Needs auth middleware |
```

### 6. Merge or Iterate

- All DONE → merge branches, run `make check`, proceed to code review
- Any DONE_WITH_CONCERNS → fix concerns or document as known issues
- Any BLOCKED → resolve blocker and re-dispatch
- Any NEEDS_CONTEXT → clarify and re-dispatch

## Status Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| DONE | Complete, verified | Merge |
| DONE_WITH_CONCERNS | Complete, non-blocking issues | Document & merge |
| BLOCKED | Cannot proceed | Resolve dependency |
| NEEDS_CONTEXT | Needs clarification | Clarify & re-dispatch |

## Verification

- Run `make check` after merging all task branches
- Run `gitnexus_detect_changes()` to verify scope
