---
title: ci-cd-pipeline
domain: deployment-cicd
impact_score: 8
last_updated: 2026-04-12
injects_into: system
tokens_estimated: 490
---

# CI/CD Pipeline

## ONE-LINE SUMMARY
GitHub Actions runs lint + test on Python 3.11/3.12, uploads coverage to Codecov, runs mypy on every push/PR, and creates GitHub Releases on version tags.

## FACTS

### Workflows

#### `.github/workflows/ci.yml` — Main CI
Triggers: push to main, pull_request to main
Matrix: Python 3.11, 3.12

Steps:
1. `actions/checkout@v6`
2. `actions/setup-python@v6` with pip cache
3. Install deps: `pip install --use-deprecated=legacy-resolver --prefer-binary -r requirements.txt` + pytest pytest-asyncio pytest-cov ruff
4. **Lint**: `ruff check` on main.py, llm_client.py, router.py, agents.py, task_orchestrator.py, computer_agent.py, handlers/, core/, bridges/, tests/ — selects E,F,W, ignores E501, exit-zero
5. **Test**: `pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing --ignore=tests/test_computer_control.py -x`
6. **Coverage upload**: codecov/codecov-action@v6 with coverage.xml

Test env vars: TELEGRAM_BOT_TOKEN="0:test", ALLOWED_USER_ID="12345"

#### `.github/workflows/typecheck.yml` — Mypy
Triggers: push, pull_request (no branch filter)
Runs on: ubuntu-latest, Python 3.11
Steps: checkout@v4, setup-python@v5, pip install mypy, mypy . --ignore-missing-imports

#### `.github/workflows/release.yml` — Release
Triggers: push with tag v*.*.*
Steps:
1. checkout with fetch-depth: 0
2. Extract changelog for tag via awk ("## [TAG]", "## [v]")
3. Create GitHub Release via softprops/action-gh-release@v2 with changelog notes

#### `.github/workflows/copilot-masterprompt.md` — Copilot workspace
Confirms Copilot workspace prompt sync (purpose unclear from filename)

### What's NOT in CI
- No deployment step (no `scp`, `rsync`, `ssh`, or docker push)
- No systemd service reload
- No database migration step
- No integration tests against live Telegram API
- No security scanning (bandit, safety)
- No dependency audit (pip-audit)
- No coverage threshold enforcement (--cov-fail-under)
- No mypy strict mode (--ignore-missing-imports only)

### Rollback Mechanism
- GitHub Releases are the rollback artifact
- Tag format: v*.*.* (e.g., v1.2.3)
- Changelog extracted from CHANGELOG.md between version headers
- No automated rollback to previous tag
- Manual rollback: `git checkout v1.2.2 && systemctl restart legion`

### Production Deployment (Manual)
```bash
# On the server (newadmin@linuxpc)
cd /home/newadmin/swarm-bot
git pull          # fetch latest
pip install -r requirements.txt  # update deps
systemctl restart legion  # restart service
```

## LEGION BEHAVIOR RULES
1. CI must pass on main before merging — PRs blocked by failing checks
2. Ruff lint uses --exit-zero so lint errors do not fail CI (legacy behavior)
3. Test coverage is uploaded to Codecov but no minimum threshold is enforced
4. Release is triggered by git tag push — no semantic version enforcement
5. CI test tokens are dummy values — tests cannot send real Telegram messages
6. typecheck.yml uses mypy with --ignore-missing-imports — many type errors silently ignored

## EXAMPLES
Bashara cuts a release:
```bash
git tag v1.2.3 && git push origin v1.2.3
```
GitHub Actions detects tag, runs release.yml, creates GitHub Release with auto-extracted changelog

Bashara rolls back:
```bash
git checkout v1.2.2 && systemctl restart legion
```

## ANTI-PATTERNS
1. --exit-zero in ruff means lint errors never fail CI — code quality degrades over time
2. No deployment automation — server requires manual git pull + pip install + restart
3. No coverage threshold — new code can have 0% coverage and still pass CI
4. No integration tests — test_computer_control.py is excluded, others use mock Telegram tokens
5. typecheck.yml uses ignore-missing-imports — mypy is essentially advisory only

## GAPS
1. **No CI deployment step** — server update requires SSH access and manual commands
2. **No canary/blue-green** — single-server, zero redundancy
3. **No rollback automation** — must manually checkout git tag and restart
4. **No security scanning** — no bandit, pip-audit, or CVE checks
5. **No coverage enforcement** — codecov uploads but doesn't gate
6. **No mypy strict mode** — --ignore-missing-imports hides real type errors
7. **No Docker containerization** — bot runs directly on host with venv

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Judge note: Functional CI pipeline with good coverage and testing, but no automation, no security scanning, and ruff --exit-zero weakens lint quality.
