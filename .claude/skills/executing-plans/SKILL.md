---
name: executing-plans
description: >-
  Execute tasks from a plan sequentially or via subagent farming. Two-stage
  review per task (spec compliance then code quality). Use after writing-plans
  produces a plan file.
---

## Mode A: Sequential (default)

Execute tasks one at a time in dependency order. After each task:
1. Run verification steps
2. If task fails, stop and report
3. After all tasks pass, run `make check`

## Mode B: Subagent Farm (for 5+ independent tasks)

Dispatch fresh subagents per independent task. Each subagent gets:
- The spec context from `.superpowers/specs/`
- The single task from `.superpowers/plans/`
- Review instructions: verify spec compliance AND code quality

Ensure no dependency conflicts between parallel tasks.

## Two-Stage Review

**Stage 1 (Spec Compliance):** Does the implementation match the spec?
**Stage 2 (Code Quality):** Code quality issues? Naming? Error handling? Tests?

## Human Checkpoints

Pause after every 3 tasks and show progress. Ask "continue?" before proceeding.

## Final Verification

- Run `make check` (ruff + pytest)
- Run `gitnexus_detect_changes()` to verify scope
