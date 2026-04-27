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

## Swarm-Bot Parallel Patterns
```
/parallel "Add test for llm_client.py" "Add test for intent_router.py" "Add test for memory_manager.py"
```
(All test files are independent — safe to parallelize)

## Risks
- Duplicate work if tasks overlap
- Inconsistent style across files
- Harder to track full scope
