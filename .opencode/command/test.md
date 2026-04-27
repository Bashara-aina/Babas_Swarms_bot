---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [module-or-path] [--coverage]
description: "Run tests. Without args: all tests. With path: tests for specific module."
---

# /test — Run tests

Execute the test suite.

## Usage
```
/test
/test handlers/ai.py
/test core/intent_router.py --coverage
/test test_memory.py -v
```

## Test Framework
- **Framework**: pytest + pytest-asyncio
- **Mode**: auto (async detection)
- **Flags**: -x (stop on first failure), -v (verbose), -q (quiet)

## Commands
```bash
# All tests
pytest tests/ -x --asyncio-mode=auto -q

# With verbose output
pytest tests/ -x --asyncio-mode=auto -v

# With coverage
pytest tests/ --cov=. --cov-report=term

# Specific test file
pytest tests/test_memory.py -x -v

# Specific test function
pytest tests/test_memory.py::test_recall -x -v

# Pattern match
pytest tests/ -k "memory" -x -v
```

## Swarm-Bot Test Conventions
```
tests/
├── handlers/
│   └── test_ai.py
├── core/
│   └── test_intent_router.py
│   └── test_soul_engine.py
├── agents/
│   └── test_agents.py
├── tools/
│   └── test_browser_tool.py
└── test_legion_callback_bridge.py
```

## Async Test Pattern
```python
import pytest

@pytest.mark.asyncio
async def test_memory_recall():
    result = await memory_manager.recall("query")
    assert result is not None
```

## Output Format
```
## TEST_RESULTS
<N> passed, <M> failed

## FAILURES
- test_file.py::test_name — AssertionError: expected X, got Y

## VERIFICATION
<final status>
```
