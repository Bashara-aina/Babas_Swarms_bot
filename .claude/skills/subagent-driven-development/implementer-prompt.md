# Task: {TASK_NAME}

## Context

{RELEVANT_SPEC_AND_PLAN_CONTEXT}

## Files to Modify

{EXACT_FILE_PATHS}

## Acceptance Criteria

{CHECKLIST_OF_WHAT_SUCCESS_LOOKS_LIKE}

## Constraints

- Must pass `make check` (ruff lint + pytest)
- Must not break existing tests
- Must follow project conventions (Python, aiogram 3.x, litellm)
- Max 500 lines per file
- No debug code, no commented-out code, no TODOs

## Self-Review Before Reporting

Before marking complete, verify:
1. [ ] All acceptance criteria met
2. [ ] `make check` passes
3. [ ] No debug code left behind
4. [ ] Error handling covers expected failure modes
5. [ ] New code has tests (if applicable)
6. [ ] No secrets leaked

## Report Format

When done, report with exactly one of these status codes:

**DONE** — All criteria met, all checks pass
Report: summary of what was done, files changed, make check result

**DONE_WITH_CONCERNS** — All criteria met but has non-blocking issues
Report: summary + list of concerns with explanation

**BLOCKED** — Cannot proceed
Report: what's blocked + what dependency is needed

**NEEDS_CONTEXT** — Need clarification
Report: what's unclear + what information is needed
