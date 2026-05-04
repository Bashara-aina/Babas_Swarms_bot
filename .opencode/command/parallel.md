---
allowed-tools: Read,Bash,Grep,Glob,Write,Edit
argument-hint: <task> [subtask, subtask, ...]
description: "Run multiple independent subtasks in parallel. Each subtask runs as a separate agent."
---

# /parallel — Parallel task execution

Execute multiple independent tasks concurrently using subagents.

## Usage
```
/parallel "Write tests for memory" "Write tests for intent router" "Update docs"
/parallel task1, task2, task3
```

## When to Use
- Multiple independent files need changes
- Research + implementation can overlap
- Tests can run in parallel
- Documentation + code changes

## How it Works
1. Splits task into N independent subtasks
2. Runs each subtask as a separate agent
3. Waits for all to complete
4. Synthesizes results

## Constraints
- Subtasks must be truly independent
- Each subtask gets its own agent context
- Cannot share state between subtasks
- Maximum ~5 parallel agents

## Shared State (/tmp/)
For subtasks that need shared state, use /tmp/ as a coordination scratch space:
- `/tmp/parallel_<session_id>_<subtask_name>.json` — subtask result buffer
- Read results from /tmp/ after all subtasks complete
- Clean up /tmp/ files on swarm completion
- Do NOT use /tmp/ for critical data — agent crash can leave orphan files

## Failure Recovery
If a subtask agent fails:
1. Log the failure: `ruflo_task_status(task_id=<id>) → FAILED`
2. Attempt retry once with same agent
3. If second failure, mark task as FAILED and continue others
4. On final synthesis, report failed subtasks with error context

## Result Merge
After all subtasks complete:
1. Collect results from /tmp/ JSON buffers
2. For each subtask result, verify non-empty and valid JSON
3. Merge: later results override earlier for conflicting keys
4. If any subtask failed: include error summary, do not abort final output
5. Delete /tmp/ parallel scratch files after merge

## Swarm-Bot Parallel Patterns
```
/parallel "Add test for llm_client.py" "Add test for intent_router.py" "Add test for memory_manager.py"
```
(All test files are independent — safe to parallelize)

## Risks
- Duplicate work if tasks overlap
- Inconsistent style across files
- Harder to track full scope
