.PHONY: install test lint run docker clean format check verify threads-on threads-off threads-status threads-toggle eval-hallucination legiona-evolve legiona-rules legiona-eval legiona-optimize legiona-debate

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

## Verify all wiring is connected
verify:
	$(PYTHON) scripts/verify_wiring.py

## Run the bot locally
run:
	$(PYTHON) main.py

## Threads campaign mode toggles (CLI)
threads-on:
	$(PYTHON) scripts/threads_mode.py on

threads-off:
	$(PYTHON) scripts/threads_mode.py off

threads-toggle:
	$(PYTHON) scripts/threads_mode.py toggle

threads-status:
	$(PYTHON) scripts/threads_mode.py status

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
	@echo "  make verify      Verify all wiring is connected"
	@echo "  make run         Start the bot"
	@echo "  make threads-on  Enable Threads campaign mode + open browser"
	@echo "  make threads-off Disable Threads campaign mode"
	@echo "  make threads-toggle Toggle Threads campaign mode"
	@echo "  make threads-status Show Threads campaign mode"
	@echo "  make docker      Start Redis + ChromaDB"
	@echo "  make hooks       Install pre-commit hooks"
	@echo "  make clean       Remove cache and temp files"
	@echo "  make eval-hallucination Run RAGAS hallucination eval harness"
	@echo "  make legiona-eval    Run the full hallucination eval harness"
	@echo "  make legiona-optimize Show RAG chunk/top_k params"
	@echo "  make legiona-debate  Interactive 3-agent debate via CLI"
	@echo ""

## Run hallucination evaluation harness
eval-hallucination:
	$(PYTHON) lib/legiona/eval/hallucination_eval.py

## Run one M2.7 self-evolution cycle (reads last 5 sessions, proposes 1 new rule)
legiona-evolve:
	$(PYTHON) -c "from lib.legiona.self_evolve import evolve; evolve(last_n=5)"

## Print current evolved rules to stdout
legiona-rules:
	@$(PYTHON) -c "from lib.legiona.self_evolve import load_evolved_rules; r = load_evolved_rules(); print(r if r else '(no rules yet)')"

## Run the full hallucination eval harness
legiona-eval:
	$(PYTHON) lib/legiona/eval/hallucination_eval.py

## Optimize chunk overlap and top_k by running eval and printing suggestions
legiona-optimize:
	@echo "Current params:" && grep -E "CHUNK_|top_k|match_threshold" lib/legiona/rag_indexer.py lib/legiona/rag_retriever.py

## Interactive 3-agent debate via CLI
legiona-debate:
	@read -p "Question: " q; python -c \
	  "from lib.legiona.debate import debate_sync; \
	   r = debate_sync('$$q'); print('=== VERDICT ==='); print(r.answer)"
