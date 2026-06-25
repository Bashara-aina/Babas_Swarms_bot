---
name: finishing-a-development-branch
description: >-
  Complete a development branch: verify tests, check scope, present options,
  archive artifacts. Use when all tasks in a plan are complete.
---

## Checklist

1. **Verify tests** — run `make check`. If failing, list failures and do not proceed.
2. **Check scope** — run `gitnexus_detect_changes()` to verify scope matches the plan.
3. **Clean up** — remove temporary files, debug logs, TODO markers.
4. **Archive artifacts** — move spec and plan from `.superpowers/specs/` and `.superpowers/plans/` to `.superpowers/archived/` with completion timestamp.
5. **Update graph** — run `graphify update .` if graph exists.
6. **Present options** to user:
   - Merge into main
   - Create PR (`gh pr create`)
   - Keep branch for later
   - Discard branch
7. **Prompt** — "What would you like to do next?"
