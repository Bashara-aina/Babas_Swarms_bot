---
name: multi-session-worktrees
description: Git-worktree-based isolation for running multiple Claude Code and OpenCode sessions simultaneously on the same repo
tags: [infrastructure, git, coordination, claude-code, opencode]
created: 2026-04-16
updated: 2026-04-16
author: Bashara + Legion
wikilinks:
  - [[entities/legion]]
  - [[architecture/legion-module-map]]
reviewers: []
status: active
---

# Multi-Session Worktree System

## TL;DR

A git-worktree-based isolation system that lets multiple Claude Code / OpenCode sessions operate on the same repo simultaneously without file or git conflicts. Each session has its own git branch + worktree directory, coordinated through a shared `registry.json`. Sessions are aware of each other via system prompt injection.

## Architecture

```
~/.claude/
├── lib/                              # Core coordination library (~/.claude/lib)
│   ├── worktree_manager.py             # Git worktree CRUD
│   ├── session_registry.py            # Registry + heartbeat + dead session detection
│   ├── advisory_lock.py              # Advisory file locking
│   ├── merge_coordinator.py          # Branch analysis + auto-merge
│   ├── cli.py                        # Unified CLI (11 subcommands)
│   ├── awareness_prompt.py           # System prompt awareness block generator
│   └── heartbeat.py                   # Background heartbeat daemon
├── worktrees/                         # Worktree root
│   ├── registry.json                  # Shared coordination state
│   ├── main/                        # Shared trunk worktree
│   └── session-<uuid>/              # Per-session isolated worktree
└── .local/bin/
    ├── cc                           # Claude Code launcher
    └── oc                           # OpenCode launcher
```

## How It Works

**Isolation:** Each session gets its own git branch (`session-<uuid>`) and worktree directory. Commits go to the session branch, never touching main until explicitly merged.

**Coordination:** A central `registry.json` tracks active sessions, file locks, and heartbeats. The registry is backed up on every write to `.bak`.

**Advisory locking:** Sessions announce intent to edit files via `advisory_lock.acquire()`. Any session CAN edit a locked file — locks are advisory (visibility), not enforced (safety). If a session crashes, its locks expire after 5 minutes of no heartbeat.

**Awareness:** Before editing any file, call `awareness_prompt.py` to generate a block showing other sessions, what they're editing, and any lock warnings. Paste this into your system prompt.

**Merging:** Run `cli.py analyze <session>` before merging. The merge coordinator shows which files are auto-mergeable and which need manual resolution.

## Usage

```bash
# Initialize (already done for swarm-bot)
python ~/.claude/lib/cli.py init --repo /home/newadmin/swarm-bot --root ~/.claude/worktrees

# Create a session worktree
python ~/.claude/lib/cli.py create session-A --task "Implementing auth module"

# List active sessions
python ~/.claude/lib/cli.py list

# Lock a file before editing
python ~/.claude/lib/cli.py lock session-A main.py

# Check locks
python ~/.claude/lib/cli.py locks

# Generate awareness block (paste into system prompt)
python ~/.claude/lib/awareness_prompt.py --session session-B

# Analyze merge readiness
python ~/.claude/lib/cli.py analyze session-A

# Merge to main
python ~/.claude/lib/cli.py merge session-A

# Start heartbeat daemon (run as background process)
python ~/.claude/lib/heartbeat.py session-A --registry ~/.claude/worktrees/registry.json &

# Launch Claude Code in worktree
~/.local/bin/cc session-A
```

## Advisory vs Enforced Locking

**Advisory was chosen intentionally.** Enforced locking creates dangerous failure modes: if a session crashes while holding an enforced lock, the file is permanently locked until manual intervention. Advisory locking means sessions SEE warnings but can override when necessary — coordination through visibility, not force.

## Current Status

System is live. Worktrees root initialized at `~/.claude/worktrees/`. `~/.local/bin/cc` and `~/.local/bin/oc` are executable and ready for use. All 38 unit tests pass.
