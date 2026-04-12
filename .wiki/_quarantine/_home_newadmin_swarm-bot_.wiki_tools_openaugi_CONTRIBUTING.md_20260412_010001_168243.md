---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/tools/openaugi/CONTRIBUTING.md",
  "reason": "daily_fast_scan: score=0.100 < 0.3",
  "score": 0.1,
  "quarantined_at": "2026-04-12T01:00:01.168270"
}
---

# Contributing to OpenAugi

Thanks for your interest in contributing.

## Setup

```bash
git clone https://github.com/openaugi/openaugi.git
cd openaugi
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Development

```bash
# Run tests
.venv/bin/python -m pytest tests/ -v

# Lint
.venv/bin/ruff check src tests

# Type check
.venv/bin/pyright src
```

## Pull Requests

- One focused change per PR
- Include tests for new functionality
- Run `pytest` and `ruff check` before submitting
- Keep PRs small — easier to review, faster to merge

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the system is structured.

## Code Style

- Python 3.12+
- Ruff for linting and formatting
- Pyright for type checking
- Pydantic for data models
- Keep it simple — no premature abstraction
