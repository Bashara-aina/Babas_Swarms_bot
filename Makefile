.PHONY: install test lint run docker clean format check

PYTHON := python3
PIP    := pip

## Install all dependencies
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov ruff pre-commit
	@echo "✅ dependencies installed"

## Run all tests with coverage
test:
	pytest tests/ -v --cov=. --cov-report=term-missing \
		--ignore=tests/test_computer_control.py

## Run tests fast (no coverage)
test-fast:
	pytest tests/ -x -q --ignore=tests/test_computer_control.py

## Lint with ruff
lint:
	ruff check . --select E,F,W --ignore E501

## Auto-fix lint issues
format:
	ruff check . --fix
	ruff format .

## Check everything (lint + test)
check: lint test

## Run the bot locally
run:
	$(PYTHON) main.py

## Start Redis + ChromaDB via Docker
docker:
	docker-compose up -d
	@echo "✅ Redis + ChromaDB running"

## Stop Docker services
docker-stop:
	docker-compose down

## Install pre-commit hooks
hooks:
	pre-commit install
	@echo "✅ pre-commit hooks installed"

## Clean cache and temp files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '.coverage' -delete
	find . -name 'coverage.xml' -delete
	find /tmp -name 'legion_*.png' -delete 2>/dev/null || true
	@echo "✅ cleaned"

## Show help
help:
	@echo ""
	@echo "Legion — Makefile targets:"
	@echo "  make install     Install all dependencies"
	@echo "  make test        Run tests with coverage"
	@echo "  make test-fast   Run tests without coverage"
	@echo "  make lint        Lint with ruff"
	@echo "  make format      Auto-fix lint issues"
	@echo "  make check       Lint + test"
	@echo "  make run         Start the bot"
	@echo "  make docker      Start Redis + ChromaDB"
	@echo "  make hooks       Install pre-commit hooks"
	@echo "  make clean       Remove cache and temp files"
	@echo ""
