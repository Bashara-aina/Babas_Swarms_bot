# Git Safety Patterns

Safe git workflows and alternatives to destructive operations.

## Blocked Commands

These are blocked by guardrails:
- `git push` (all variants)
- `git reset --hard`
- `git clean -f` / `-fd`
- `git branch -D`
- `git checkout .`
- `git restore .`

## Safe Alternatives

| Instead of | Use |
|-----------|-----|
| `git push --force` | `git push --force-with-lease` |
| `git reset --hard` | `git reset --soft` (keeps changes staged) |
| `git clean -f` | `git stash` (saves changes) |
| `git branch -D` | `git branch -d` (safe delete) |
| `git checkout .` | `git restore .` (safer) |
| `git restore .` | `git checkout -- .` (traditional) |

## force-with-lease

Better than `--force` — fails if someone else pushed to the branch:

```bash
git push --force-with-lease origin main
```

## Undoing Things Safely

### Undo Last Commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Undo Last Commit (unstage changes)
```bash
git reset HEAD~1
```

### Restore Single File
```bash
git checkout -- path/to/file.txt
# or
git restore path/to/file.txt
```

### Save Work Temporarily
```bash
git stash
# later...
git stash pop
```

## Recovery

If you accidentally `reset --hard`:

1. `git reflog` — shows history of where HEAD was
2. `git checkout <commit-hash>` — recover to that point
3. `git branch backup` — create branch before trying recovery