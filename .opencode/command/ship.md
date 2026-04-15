---
description: >-
  Deployment workflow from code completion through PR creation. Use when:
  "ship", "deploy", "push to main", "create a PR", "land this". Runs pre-flight
  checks, merges base branch, runs tests, adversarial review, generates changelog,
  bumps version, and creates the PR. Ensures nothing ships broken.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, AskUserQuestion
argument-hint: [optional: branch to ship, defaults to current]
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---

# /ship — Deployment Pipeline

## VOICE

Sound like a builder who ships. Be direct about what's wrong and what needs to be fixed before shipping. The Completeness Principle: boil the lake, don't ship half-done work.

## PREFLIGHT CHECKS

### Step 1 — Current State

```bash
git status
git branch --show-current
git log --oneline -5
```

### Step 2 — Verify Base Branch is Clean

```bash
git fetch origin $(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo "main")
git diff origin/$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo "main") --stat
```

If there are uncommitted changes: "Commit or stash changes before shipping."

### Step 3 — Test Bootstrap Check

```bash
# Check test framework exists
ls tests/ 2>/dev/null | head -5
# Check if pytest/pytest-asyncio available
python -c "import pytest; print('pytest ok')" 2>/dev/null || echo "pytest not found"
```

## STEP 1 — Merge Base Branch

```bash
BASE=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo "main")
git fetch origin $BASE --quiet
git merge origin/$BASE --no-edit 2>&1
```

If merge conflicts: Report conflicts and STOP. Do not proceed.

## STEP 2 — Run Test Suite

```bash
pytest tests/ -x --asyncio-mode=auto -q 2>&1
```

If tests fail: Report failure with full output. STOP. Do not ship with failing tests.

## STEP 3 — Coverage Audit

```bash
pytest tests/ --cov=. --cov-report=term-missing --asyncio-mode=auto -q 2>&1 | tail -20
```

If coverage drops: Report which files lack coverage. Decide if acceptable.

## STEP 4 — Plan Completion Audit

```bash
# Check TODOS.md for completed items
grep -n "\[x\]" TODOS.md 2>/dev/null | tail -10 || echo "No TODOs found"
```

Verify: Does the diff address what TODOS.md/items promised?

## STEP 5 — Adversarial Review (Quick)

```bash
git diff --stat | tail -1
```

If diff > 200 lines: Dispatch a quick adversarial review via Agent tool.

Prompt: "Review this diff for critical bugs, security issues, and edge cases. Be adversarial. Output: FINDINGS (list) or CLEAN."

## STEP 6 — Changelog + Version

### Update Changelog

```bash
# Check existing changelog
cat CHANGELOG.md 2>/dev/null | head -20 || echo "No CHANGELOG.md"
```

If changelog exists, prepend entry:

```markdown
## [Unreleased] — [YYYY-MM-DD]

### Added
- [feature description]

### Fixed
- [bug fix description]

### Changed
- [change description]
```

### Version Bump

Check current version:
```bash
grep -r "version" pyproject.toml setup.py package.json 2>/dev/null | grep -v "__pycache__"
```

Bump appropriately (patch for fixes, minor for features, major for breaking):
- Bug fix → patch (1.2.3 → 1.2.4)
- New feature → minor (1.2.3 → 1.3.0)
- Breaking change → major (1.2.3 → 2.0.0)

## STEP 7 — Push and PR

```bash
git add -A
git commit -m "[type]: [short description]

- [what changed]
- [why]"
git push origin HEAD
gh pr create --fill 2>&1 || echo "PR creation skipped (gh not authenticated)"
```

## OUTPUT FORMAT

```
SHIP REPORT: [branch]
═══════════════════════════════════

BASE MERGE: ✅ SUCCESS | 🔴 CONFLICTS
TESTS: ✅ PASS | 🔴 FAIL
COVERAGE: [N]% [ACCEPTABLE/DROP]
PLAN AUDIT: ✅ COMPLETE | ⚠️ GAPS
ADVERSARIAL: ✅ CLEAN | ⚠️ ISSUES FOUND
CHANGELOG: ✅ UPDATED | N/A
VERSION: [old] → [new]
PUSH: ✅ DONE | ⚠️ FAILED

PR: [URL or "manual creation needed"]

STATUS: ✅ SHIPPED | 🔴 BLOCKED | ⚠️ ISSUES FOUND
```

## ANTI-HALLUHALLUCINATION RULES

1. Verify every claim with command output
2. If tests fail, do not proceed — no exceptions
3. Report merge conflicts before attempting to fix
4. Paste actual test output and coverage numbers
5. Completeness: boil the lake, don't ship half-done work
