# Legiona Parallel Worktree Protocol

## Quick Reference

Use parallel worktrees when a Legiona task has 3+ independent subtasks, each taking >5 tool calls.

## Protocol

### 1. Assess
Ask: "Are these subtasks truly independent? Can Subtask B start before Subtask A finishes?"

If **yes** → parallelize. If **no** → sequential.

### 2. Create worktrees
```bash
cd /home/newadmin/.claude/lib
python cli.py worktree create legiona-<taskname>-<subtask>
python cli.py worktree create legiona-<taskname>-<subtask2>
```

### 3. Assign
Main session: decompose task, assign each subtask to a worktree session. Write a brief `SESSION_SUMMARY.md` in each sub-worktree describing what it should do.

### 4. Execute in parallel
Each sub-worktree session:
1. Read `lib/legiona/memory/global_memory.md`
2. Read `lib/legiona/memory/rules.md`
3. Execute assigned subtask
4. Write results to `SESSION_SUMMARY.md` with DONE marker

### 5. Synthesize
Main session: read all sub-worktree `SESSION_SUMMARY.md` files, assemble into final deliverable, run integration checks.

## Coordination Rules

| Rule | Reason |
|------|--------|
| One coordinator, N sub-workers | Avoid split-brain conflicts |
| Write SESSION_SUMMARY before exiting | Enables recovery if a sub-worker crashes |
| Max 3 parallel sub-workers | Coordination cost scales with worker count |
| Never split a single file across workers | Merge conflicts |

## Worktree Exit
When a sub-worker is done:
```bash
cd /home/newadmin/.claude/lib
python cli.py worktree exit --keep  # keep worktree, just exit
```
