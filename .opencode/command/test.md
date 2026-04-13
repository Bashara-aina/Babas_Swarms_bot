---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [module-or-path] [--coverage] | core/agents | handlers/ | --coverage
description: Run tests for a specific module or full test suite with optional coverage report
---

# /test — Test Execution Command

## STEP 1 — Detect Test Framework

Check project for test framework:
```bash
ls tests/ 2>/dev/null | head -10
grep -r "pytest\|unittest\|asyncio" pyproject.toml requirements.txt 2>/dev/null | head -5
```

## STEP 2 — Run Tests

For a specific module:
```bash
pytest tests/test_intent_router.py -v --asyncio-mode=auto 2>/dev/null
pytest tests/ -k "test_name" -v 2>/dev/null
```

For full suite:
```bash
pytest tests/ -x --asyncio-mode=auto -q
```

With coverage:
```bash
pytest tests/ --cov=. --cov-report=term-missing --asyncio-mode=auto -q
```

## STEP 3 — Report Results

Report:
- Tests run / passed / failed
- Any failures with full traceback
- Coverage % if requested

## Special Rules

- If no tests exist for the module: report "No tests found for [module]"
- If tests fail: do NOT proceed with any contract that requires this module's tests to pass
- BUG_FIX contracts must include test output showing before/after state
