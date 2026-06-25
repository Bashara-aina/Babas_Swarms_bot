---
name: using-git-worktrees
description: >-
  Use git worktrees to work on multiple branches simultaneously.
  Detects existing worktrees, guards against submodules, and prefers native
  Claude Code worktree tool over raw git.
---

## Detection

Before creating a worktree, check if one already exists:

```
git worktree list
```

If a worktree for the target branch already exists, use it instead of creating a new one.

## Guard: Submodules

If the repo uses submodules, DO NOT use git worktrees. Submodules in worktrees are fragile and error-prone. Use `git stash` + `git checkout` instead.

To check: `git submodule status`

## Priority: Native Tool First

Prefer `EnterWorktree` tool over raw `git worktree add`:

- `EnterWorktree({name: "branch-name"})` — creates worktree and switches session
- `ExitWorktree({action: "keep"|"remove"})` — exits and optionally cleans up

Only use raw `git worktree add` if the native tool is unavailable or insufficient.

## Directory Priority

Worktrees should go in `.claude/worktrees/` (Claude Code convention).

When using `EnterWorktree`, the worktree is automatically placed there.

## Cleanup

- After merging a worktree branch, remove the worktree: `ExitWorktree({action: "remove"})`
- If work is paused and you want to keep it: `ExitWorktree({action: "keep"})`
- Prune stale worktree references: `git worktree prune`
