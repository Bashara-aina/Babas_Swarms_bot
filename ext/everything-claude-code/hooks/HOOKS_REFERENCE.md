---
title: Everything Claude Code Hooks Reference
type: reference
status: active
tags: [ecc, hooks, quality, automation]
created: 2026-04-13
updated: 2026-04-13
summary: ECC hook system documentation — 17 hooks for pre/post-tool quality enforcement in Claude Code. Concepts to guide future swarm-bot middleware implementation.
wikilinks: [[ext/everything-claude-code/__init__]]
confidence: high
source: https://github.com/affaan-m/everything-claude-code
---

# ECC Hooks Reference

ECC provides 17 event-driven hooks that fire before or after Claude Code tool
executions. These enforce code quality, catch mistakes early, and automate
repetitive checks. Source: `hooks/hooks.json` (JSON Schema: claudecode-settings).

## Hook Types

| Type | When | Can Block? |
|------|------|------------|
| **PreToolUse** | Before tool executes | ✅ Yes (exit 2 = block, exit 0 = warn) |
| **PostToolUse** | After tool completes | ❌ No (output analysis only) |
| **Stop** | After each response | ❌ No |
| **SessionStart/SessionEnd** | Session lifecycle | ❌ No |
| **PreCompact** | Before context compaction | ❌ No |

## Hook Inventory (17 hooks)

### PreToolUse Hooks

#### Bash Commands

| Hook ID | Matcher | Behavior | Exit |
|---------|---------|----------|------|
| `pre:bash:block-no-verify` | `Bash` | Blocks `git commit --no-verify` etc. | 2 (block) |
| `pre:bash:auto-tmux-dev` | `Bash` | Auto-starts dev servers in tmux | 0 (warn) |
| `pre:bash:tmux-reminder` | `Bash` | Reminds to use tmux for long commands | 0 (warn) |
| `pre:bash:git-push-reminder` | `Bash` | Reminds to review changes before `git push` | 0 (warn) |
| `pre:bash:commit-quality` | `Bash` | Lint staged files, validate commit msg, detect secrets | 2 (block) |

#### Write/Edit Commands

| Hook ID | Matcher | Behavior | Exit |
|---------|---------|----------|------|
| `pre:write:doc-file-warning` | `Write` | Warns about non-standard `.md` files | 0 (warn) |
| `pre:edit-write:suggest-compact` | `Edit\|Write` | Suggests `/compact` every ~50 tool calls | 0 (warn) |

### PostToolUse Hooks

| Hook ID | Matcher | Behavior |
|---------|---------|----------|
| `post:bash:pr-logger` | `Bash` | Logs PR URL after `gh pr create` |
| `post:bash:build-analysis` | `Bash` | Background analysis after build commands |
| `post:edit-write:quality-gate` | `Edit\|Write\|MultiEdit` | Fast quality checks after edits |
| `post:edit-write:design-quality` | `Edit\|Write\|MultiEdit` | Warns on generic template-looking UI |
| `post:edit:prettier-format` | `Edit` | Auto-formats JS/TS with Prettier |
| `post:edit:tsc-check` | `Edit` | Runs `tsc --noEmit` after `.ts/.tsx` edits |
| `post:edit:console-log-warning` | `Edit` | Warns about `console.log` in edits |

## Swarm-Bot Implementation Notes

These hooks are Claude Code CLI-specific (Node.js hooks). For the swarm-bot
(Python/aiogram), similar quality enforcement can be implemented as:

### Potential Python Equivalents

1. **Pre-command quality check** — Before shell execution, validate command
   against allowlist (e.g., block `git push --force`, warn on `rm -rf`)

2. **Post-edit lint trigger** — After file edits via aiogram handler,
   run `black --check` or `ruff check` on modified files

3. **Session start/end hooks** — `on_startup()` / `on_shutdown()` in aiogram
   can perform initialization and cleanup tasks

4. **Pre-commit quality gate** — Before `git commit`, run linters via
   `asyncio.create_task()` in background

5. **console.log detector** — Regex search in edited files for debugging
   artifacts before responding

## Files

- `hooks.json` — Full hook configuration (JSON, 30KB)
- `README.md` — Hook documentation
- `HOOKS_REFERENCE.md` — This file

## See Also

[[ext/everything_claude_code/__init__]] — Integration module
