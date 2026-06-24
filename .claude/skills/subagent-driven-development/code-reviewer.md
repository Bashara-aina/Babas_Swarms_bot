# Final Code Review: {BRANCH_NAME}

## Scope

Review the entire branch diff against {BASE_BRANCH}.

## Process

1. Read the complete `git diff {BASE_BRANCH}...HEAD`
2. Check each file for issues
3. Run `gitnexus_detect_changes()` to verify scope
4. Run `make check` to verify tests pass

## Checklist

- [ ] All hunks are intentional and necessary
- [ ] No unrelated changes mixed in
- [ ] Error handling covers expected failures
- [ ] No secrets, debug code, or TODOs
- [ ] Naming consistent with project conventions
- [ ] Tests exist for new functionality
- [ ] No files over 500 lines
- [ ] `gitnexus_detect_changes()` shows expected scope only

## Report Format

```
## Summary
N files changed, +M -L lines

## Changes
- file.py: brief description of change

## Issues
- None

## Verdict
APPROVED | APPROVED_WITH_COMMENTS | CHANGES_REQUESTED
```
