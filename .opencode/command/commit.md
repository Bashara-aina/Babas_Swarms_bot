---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [files...]
description: "Stage and commit with structured message. Auto-generates conventional commit. Usage: /commit or /commit <files...>"
---

# /commit — Stage and commit

Stage files and create a conventional commit message.

## Usage
```
/commit
/commit file1.py file2.py
/commit --all
```

## Workflow
1. Shows staged changes
2. Auto-generates commit message (conventional format)
3. Reports commit SHA

## Conventional Commit Format
```
<type>(<scope>): <subject>

<body>

Closes #<issue>
```

Types: feat, fix, docs, style, refactor, test, chore, perf

## Pre-commit Checks
Before committing, always verify:
- Tests pass: `pytest tests/ -x --asyncio-mode=auto -q`
- No secrets committed: check .env, credentials
- Diff looks correct: `git diff --staged --stat`

## Swarm-Bot Constraints
- Never commit .env, secrets.json, credentials
- Config files: use os.getenv(), not hardcoded values
- Test files should accompany code changes
