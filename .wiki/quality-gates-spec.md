---
title: Quality Gates Spec
domain: testing
impact_score: 8
last_updated: 2026-04-12
injects_into: ci, development, deployment
tokens_estimated: 490
---

# QUALITY GATES SPEC

## ONE-LINE SUMMARY
CI/CD quality checks: linting, type checking, test execution, and coverage requirements for Legion.

## GATES OVERVIEW

| Gate | Tool | Threshold | Fail On |
|------|------|-----------|---------|
| Lint | ruff | 0 errors | No (--exit-zero) |
| Type Check | mypy | Strict | No |
| Unit Tests | pytest | 100% pass | Yes |
| Coverage | pytest-cov | ≥10% | No (fail_ci_if_error: false) |

---

## GATE 1: LINT (ruff)

### CI Configuration
```yaml
- name: Lint with ruff
  run: |
    ruff check \
      main.py llm_client.py router.py agents.py task_orchestrator.py computer_agent.py \
      handlers/ core/ bridges/ tests/ \
      --select E,F,W --ignore E501 --exit-zero
```

### Rules
- `E,F,W` — errors, failures, warnings (no style-only W503)
- `E501` ignored (line-length, handled by formatter)
- `--exit-zero` — lint errors do not block merge

### Local Run
```bash
ruff check . --select E,F,W --ignore E501
```

---

## GATE 2: TYPE CHECK (mypy)

### CI Configuration
```yaml
# .github/workflows/typecheck.yml
- name: mypy
  on: [push, pull_request]
  jobs:
    typecheck:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: "3.11" }
        - run: pip install mypy
        - run: mypy . --ignore-missing-imports
```

### Constraints
- `--ignore-missing-imports` — no stub files required
- Python 3.11 minimum
- Strict mode NOT enforced (would require extensive type annotations)

---

## GATE 3: UNIT TESTS (pytest)

### CI Configuration
```yaml
- name: Run tests
  env:
    TELEGRAM_BOT_TOKEN: "0:test"
    ALLOWED_USER_ID: "12345"
  run: |
    python -m pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing \
      --ignore=tests/test_computer_control.py \
      -x
```

### Environment Variables (Test Secrets)
```
TELEGRAM_BOT_TOKEN=0:test        # dummy token for bot init
ALLOWED_USER_ID=12345            # dummy user ID for auth checks
```

### Key Flags
- `-x` — stop on first failure
- `-v` — verbose output
- `--cov=.` — coverage from project root
- `--cov-report=xml` — Cobertura XML for codecov
- `--cov-report=term-missing` — terminal report with missing lines
- `--ignore=tests/test_computer_control.py` — excluded (requires display)

### Async Mode
```bash
pytest tests/ -x --asyncio-mode=auto -q
```
`asyncio_mode = "auto"` is configured via pytest section in pyproject.toml or conftest.py.

---

## GATE 4: COVERAGE

### Minimum Threshold
```yaml
--cov=. --cov-report=xml --cov-report=term-missing
# Excluded from coverage: tests/*, site-packages, setup.py
```

### Threshold Reality
Minimum coverage: **10%** (currently enforced only in CI gate, not as hard requirement).

### Actual Coverage Areas

| Module | Est. Coverage |
|--------|--------------|
| core/ | 40-60% |
| agents/ | 20-40% |
| handlers/ | 10-20% |
| tools/ | 5-15% |
| swarms_bot/ | 20-40% |
| legion/ | 50-70% |

### Coverage Gaps
- handlers/ (45+ routers) — minimal smoke tests
- tools/ (65+ tools) — sparse coverage
- memory/Mem0 integration — limited tests

---

## INTEGRATION TEST SUITE

### Dedicated Integration Job
```yaml
- name: Run v5 integration tests
  env:
    TELEGRAM_BOT_TOKEN: "0:test"
    ALLOWED_USER_ID: "12345"
  run: python -m pytest tests/test_v5_integrations.py -v --tb=short
```

### Scope
- OpenAI Agents bridge handoffs
- Swarm topologies (sequential, mixture, graph, spreadsheet)
- OWL agent, AG2 research pipeline
- Code execution sandbox
- Agent response model validation
- MiroFish task complexity scoring
- Config YAML validation

---

## SMOKE TESTS (No pytest required)

`tests/test_main.py` contains standalone smoke tests runnable without pytest infrastructure:
```bash
python -m pytest tests/test_main.py -v
# or directly:
python tests/test_main.py
```

Tests critical imports, config loading, handler registration, core module accessibility.

---

## PRE-COMMIT HOOKS

No pre-commit hook configured. Current CI does not block on lint errors (`--exit-zero`).

### Recommended Hook (if added)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

---

## QUALITY GATE WORKFLOW

```
push/pull_request
    │
    ├─► lint (ruff) ──────── warnings only
    │
    ├─► typecheck (mypy) ─── strict but non-blocking
    │
    ├─► tests (pytest) ───── MUST pass 100%
    │       │
    │       ├─► coverage.xml ──► codecov (advisory)
    │       │
    │       └─► term-missing ──► human review
    │
    └─► integration tests ── separate job
```

---

## FAILURE RESPONSE

| Gate | On Failure |
|------|-----------|
| ruff | Log warning, continue |
| mypy | Log errors, continue |
| pytest | Block merge, show failure trace |
| coverage | Log, continue (fail_ci_if_error: false) |

---

## RECOMMENDED IMPROVEMENTS

1. **Raise coverage threshold to 70%** — current 10% is placeholder
2. **Add pre-commit hooks** — catch issues before CI
3. **Enable ruff --exit-zero removal** — make lint blocking
4. **Add security scan step** — bandit or safety
5. **Add mutation testing** — verify test quality (mutmut)
6. **Add benchmark tests** — catch performance regressions
