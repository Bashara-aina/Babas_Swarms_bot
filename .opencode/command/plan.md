---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <task-or-module>
description: "Plan implementation. Analyzes task, identifies files, sequences steps, estimates risk."
---

# /plan — Implementation planning

Create a structured implementation plan for a task.

## Usage
```
/plan add webhook support
/plan implement retry mechanism
/plan optimize LLM fallback chain
```

## Planning Workflow — MANDATORY SEQUENCE

### Step 0 — Sequential Thinking (MANDATORY — do FIRST)
Before generating ANY plan, call the sequentialthinking tool:
```
Call sequentialthinking with:
  - thought: restate the planning goal in your own words
  - nextThoughtNeeded: true
Continue until nextThoughtNeeded: false.
This step prevents shallow decomposition — SKIP AT YOUR OWN RISK.
```

### Step 1 — Memory Search
Search mem0 for relevant past sessions:
```
mem0_search(user_id="bashara", query=<task_description>, limit=5)
build_mem0_context(memories, query=<task_description>)
Prepend context_block to your planning prompt.
```

### Step 2 — Read Context
Read AGENTS.md, .wiki/INDEX.md, recent git log, existing decisions.

### Step 3 — Write Task Log
```
touch .wiki/logs/planner-[YYYY-MM-DD]-[task-slug].md
```

### Step 4 — Generate Plan
Write CONTRACTS following the CONTRACT format.

## Planning Output
```
## TASK
<what needs to be built>

## FILES_TO_CHANGE
- file1.py (create/modify)
- file2.py (modify)
- tests/test_file1.py (add)

## SEQUENCE
1. Step 1 — what to do first (lowest risk)
2. Step 2 — core implementation
3. Step 3 — tests
4. Step 4 — integration

## RISK
- Scope creep potential
- Breaking changes
- Test coverage needed

## ESTIMATED_CHANGES
- N files
- M lines added / K lines removed
```

## Swarm-Bot Planning Considerations
- Telegram API rate limits
- LLM API cost and rate limits
- Memory system consistency
- Backward compatibility for handlers

## Constraints
- Plans are estimates, not guarantees
- Scope may change during implementation
- Re-plan if significantly off track
