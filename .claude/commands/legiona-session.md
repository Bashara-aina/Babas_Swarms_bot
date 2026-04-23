# Legiona Session Architecture

## For SHORT tasks (< 30 tool calls expected)
Single session. Run normally.

## For LONG tasks (architecture, full-feature, refactor)
Use multi-session protocol:
1. **Session 1**: Plan → write SESSION_SUMMARY.md → /clear
2. **Session 2**: Implement → append to SESSION_SUMMARY.md → /clear
3. **Session 3**: Integrate + test → done

## Starting a continued session
```
Continue Legiona task. Read SESSION_SUMMARY.md and
lib/legiona/memory/global_memory.md before starting.
```

## Before each session
1. Read `lib/legiona/memory/global_memory.md` — cross-session facts
2. Read `lib/legiona/memory/rules.md` — session-evolved rules
3. Run `make legiona-evolve` to extract one new rule from last session

## After each session
Run: `make legiona-evolve`
This extracts one new rule from your session and patches the rules system.

## Parallel Worktree Protocol

When a Legiona task requires parallel sub-agents running simultaneously in separate worktrees:

### When to split
Split when: 3+ independent subtasks that each take >5 tool calls and none depends on another's output.

### How to split
```bash
# From swarm-bot root:
cd /home/newadmin/.claude/lib
python cli.py worktree create legiona-task-<name>
python cli.py worktree create legiona-task-<name>-2  # etc.
```

### Coordination
- **One coordinator** (main session): owns the plan, assigns sub-tasks, assembles final result.
- **Sub-workers** (worktree sessions): execute assigned subtask, write output to `SESSION_SUMMARY.md` in their worktree.
- **Main session**: reads all SESSION_SUMMARY.md files, synthesizes into deliverable.

### Rules
- Never split mid-logical-unit — a function or a single file = one unit.
- Sub-workers read `global_memory.md` and `rules.md` before starting.
- Sub-workers must signal completion by writing to `SESSION_SUMMARY.md` with a DONE marker.
- Coordinator does final integration test before declaring done.

### Anti-patterns
- ❌ Splitting a single file across worktrees (merge conflict hell)
- ❌ Not writing SESSION_SUMMARY before abandoning a sub-worker
- ❌ More than 3 parallel sub-workers (coordination cost exceeds parallelization gain)

---

## Legiona Memory Files
| File | Scope | Updated by |
|------|-------|------------|
| `lib/legiona/memory/rules.md` | Session | `evolve()` after each run |
| `lib/legiona/memory/global_memory.md` | Cross-session | `evolve()` syncs here too |
| `.opencode/memory/` | OpenCode system | OpenCode agents |
