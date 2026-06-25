---
name: dispatching-parallel-agents
description: >-
  Dispatch multiple parallel subagents for independent work.
  Decision flow for when to parallelize, agent prompt structure, and
  result collection.
---

## When to Parallelize

Dispatch parallel agents when ALL of these are true:
1. 2+ independent tasks (no dependency between them)
2. Each task takes 2+ minutes of work
3. Tasks modify different files (no merge conflicts expected)
4. You have context budget to spawn them

Do NOT parallelize when:
- Tasks modify the same files (sequential required)
- Tasks have implicit ordering constraints
- One task produces context the next needs
- You're near context limits

## Decision Flow

```
How many independent tasks?
├── 1 → sequential (executing-plans)
├── 2-4 → dispatch all in parallel
├── 5-8 → batch into 2 waves, 4 per wave
└── 9+ → batch into waves of 4, collect after each wave
```

## Agent Prompt Structure

Each parallel agent prompt must be self-contained:

```
1. Task description (what to do)
2. File paths (exactly which files to modify)
3. Acceptance criteria (how to verify success)
4. Constraints (project conventions, line limits, test requirements)
5. Report format (what to return)
```

Include enough context that the agent doesn't need to ask questions.

## Spawning Pattern

Use the Agent tool with `run_in_background: true` for fire-and-forget dispatch:

```json
{
  "name": "Agent",
  "arguments": {
    "description": "Short task description",
    "prompt": "Self-contained task prompt...",
    "subagent_type": "general-purpose",
    "run_in_background": true
  }
}
```

## Collecting Results

- Each agent reports when done (via completion notification)
- Review each result against acceptance criteria
- If any agent BLOCKED or FAILED, assess impact on dependent tasks
- If agents were dispatched in waves, don't start wave N+1 until wave N results are collected

## Post-Collection

- Run `make check` to verify no integration issues
- Run `gitnexus_detect_changes()` to verify scope
- Update progress ledger if using subagent-driven-development
