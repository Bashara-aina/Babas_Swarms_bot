---
description: >-
  Analyze test coverage for code changes. Identifies gaps, missing edge cases,
  and suggests additional tests. Use after any significant code change to ensure
  adequate test coverage.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /test-coverage — Test Coverage Analysis

## WHEN TO USE

Use `/test-coverage` when:
- Code change adds new functionality
- Refactoring changes function signatures
- Bug fix requires test addition
- Pre-PR review for test completeness
- After adding critical path code

## WHAT IT CHECKS

### Coverage Analysis
- What files have tests
- What functions/methods are tested
- What lines are covered by tests
- What lines are NOT covered

### Edge Case Analysis
- Null/None inputs tested?
- Empty collections tested?
- Boundary conditions tested?
- Error paths tested?
- Concurrent access tested?

### Integration Analysis
- Unit tests for pure functions
- Integration tests for API calls
- End-to-end tests for critical flows

## USAGE

```
/test-coverage [file or module]
/test-coverage --full
/test-coverage --diff
```

## EXAMPLES

### Analyze specific file
```
/test-coverage handlers/ai.py
```

Output:
```
## TEST COVERAGE: handlers/ai.py

Coverage: 78% (142/182 lines)
Missing coverage:
- line 45-47: error handling path
- line 89-92: timeout recovery
- line 156-160: empty message edge case

Edge cases not tested:
- ❌ Null message text
- ❌ Message with special characters
- ✅ Rate limit handling
- ❌ Concurrent handler calls

Suggested tests:
1. test_handle_empty_message
2. test_handle_special_chars
3. test_rate_limit_recovery
4. test_concurrent_handlers
```

### Full project coverage
```
/test-coverage --full
```

Output:
```
## FULL PROJECT COVERAGE

Overall: 67%
By module:
- core/: 72%
- handlers/: 78%
- tools/: 54%
- agents/: 45%

Critical gaps:
⚠️ tools/briefing.py: 34% coverage
⚠️ agents/worker.py: 41% coverage

Files with no tests:
- tools/ruflo/server.js
- tools/n8n_bridge.py
```

### Coverage diff (changes only)
```
/test-coverage --diff
```

Output:
```
## COVERAGE DIFF: recent changes

Files changed: handlers/ai.py, core/intent_router.py
New coverage: +23 lines
Lost coverage: -0 lines (good!)

New edge cases covered:
- ✅ Empty message handling
- ✅ Message too long truncation

New edge cases missing:
- ⚠️ Intent classification timeout
```

## ANALYSIS STEPS

### Step 1 — Discover Tests
```bash
find . -name "test_*.py" -o -name "*_test.py"
pytest --collect-only -q
```

### Step 2 — Run Coverage
```bash
pytest --cov=. --cov-report=term-missing -q
# or for specific file
pytest --cov=handlers --cov-report=term-missing handlers/ -q
```

### Step 3 — Gap Analysis
```
For each uncovered function:
1. Identify what it does
2. Determine what inputs it accepts
3. List edge cases
4. Check if edge case is tested
```

### Step 4 — Report
```
## Test Coverage Gaps

### Critical Path Coverage
[each gap with file:line, what should be tested]

### Edge Case Coverage
[each gap with scenario and suggested test]

### Integration Coverage
[each gap with integration points]
```

## ANTI-HALLUCINATION RULES

1. **Run tests first** — don't assume coverage numbers
2. **Cite actual output** — paste pytest-cov output
3. **Show actual uncovered lines** — cite file:line
4. **Be specific** — each gap needs exact scenario and test suggestion
5. **Distinguish coverage from quality** — high coverage ≠ good tests

## COVERAGE THRESHOLDS

| Coverage | Rating | Recommendation |
|----------|--------|----------------|
| 90%+ | ✅ Excellent | Approve |
| 70-89% | ✅ Good | Minor improvements suggested |
| 50-69% | ⚠️ Adequate | Changes required for critical paths |
| <50% | ❌ Poor | Block until coverage improved |

## STATUS
```
TEST COVERAGE STATUS: ✅ ADEQUATE | ❌ GAPS FOUND | ❌ INSUFFICIENT
Coverage: [X]%
Critical gaps: [N]
Suggested additions: [list]
```
