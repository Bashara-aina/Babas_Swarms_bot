---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [pattern]
description: "Quality assurance. Run full test suite. Without args: all tests. With pattern: matching tests."
---

# /qa — Quality assurance

Run tests and provide quality analysis.

## Usage
```
/qa
/qa test_memory
/qa handlers/
/qa --coverage
```

## What it checks
- All tests pass
- Code coverage
- Lint/format issues
- Type errors

## Test Commands
```bash
# All tests
pytest tests/ -x --asyncio-mode=auto -q

# Specific pattern
pytest tests/ -k "memory" -x --asyncio-mode=auto -v

# With coverage
pytest tests/ --cov=. --cov-report=term

# Fast mode
pytest tests/ -x --asyncio-mode=auto -q --tb=short
```

## Test Location Convention
```
tests/
├── handlers/
│   └── test_ai.py
├── core/
│   └── test_intent_router.py
├── agents/
│   └── test_agents.py
└── test_legion_callback_bridge.py
```

## Output Format
```
## TEST_RESULTS
Passed: N  Failed: N  Errors: N

## COVERAGE
handlers/ai.py: 85%
core/intent_router.py: 92%

## ISSUES
- test_memory.py::test_recall — FAILING
- handlers/test_ai.py — missing coverage for edge case
```

## Constraints
- Tests must pass before shipping
- Do not skip failing tests
- Coverage should not decrease
