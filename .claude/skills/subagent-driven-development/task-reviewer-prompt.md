# Task Review: {TASK_NAME}

## Stage 1: Spec Compliance

Check each acceptance criterion:
- [ ] Criterion 1 met
- [ ] Criterion 2 met
- [ ] All acceptance criteria covered

If any criterion is not met → mark as BLOCKED, do NOT proceed to Stage 2.

## Stage 2: Code Quality

### Critical (Must Fix)
- Security vulnerabilities (injection, XSS, secret exposure)
- Data loss risk
- Broken error handling that swallows exceptions
- Incorrect logic that produces wrong results

### Important (Should Fix)
- Naming that violates project conventions
- Missing error handling for expected failure modes
- Missing tests for new functionality
- Files over 500 lines
- Dead code or commented-out code

### Minor (Nice to Fix)
- Style inconsistencies not caught by linter
- Documentation gaps
- Non-idiomatic patterns

## Report

Use the status code from the implementer's report. If you found issues in Stage 2:

- If any Critical items → downgrade to DONE_WITH_CONCERNS and list them
- If any Important items left unfixed → downgrade to DONE_WITH_CONCERNS
- Minor items → mention but do not downgrade

## Calibration Rules

- Do NOT flag patterns that match existing code style
- Do NOT demand abstractions for single-use code
- Do NOT require error handling for impossible scenarios
- "Make this more robust" is not a valid concern without a specific scenario
