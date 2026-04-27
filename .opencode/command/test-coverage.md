---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [module-or-path]
description: "Test coverage analysis. Shows which parts of code have tests and which are untested."
---

# /test-coverage — Coverage analysis

Analyze test coverage for a module or the entire codebase.

## Usage
```
/test-coverage
/test-coverage handlers/ai.py
/test-coverage core/intent_router.py
```

## Coverage Report
```
## COVERAGE_SUMMARY
Total: 65% (4,521 / 6,954 lines)

## BY_MODULE
handlers/ai.py: 85% ████████▓
core/intent_router.py: 92% █████████▓
core/memory/memory_manager.py: 71% ███████▒▒
llm_client.py: 60% ██████▒▒▒

## UNTCOVERED
- core/memory/memory_manager.py:203-215
- core/intent_router.py:89-95
```

## Coverage Thresholds
| Coverage | Status |
|----------|--------|
| 90%+ | Excellent |
| 80-89% | Good |
| 60-79% | Needs improvement |
| <60% | Critical |

## How to Improve Coverage
1. Identify untested functions
2. Write tests for critical paths
3. Add edge case tests
4. Remove dead code

## Command
```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
```

## Swarm-Bot Coverage Priorities
1. llm_client.py (core LLM logic)
2. core/intent_router.py (routing)
3. core/memory/memory_manager.py (memory)
4. handlers/ (user-facing)
