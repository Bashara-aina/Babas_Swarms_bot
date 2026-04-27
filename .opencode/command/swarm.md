---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [task]
description: "Swarm mode: coordinate multiple agents on a complex task with different roles."
---

# /swarm — Multi-agent orchestration

Orchestrate multiple specialized agents to work on different aspects of a complex task.

## Usage
```
/swarm implement new agent type
/swarm debug LLM reliability issue
/swarm optimize memory recall latency
```

## Swarm Roles
| Role | Specialization |
|------|---------------|
| planner | Decompose task, coordinate |
| worker | Implement code changes |
| reviewer | Quality assurance |
| researcher | Investigation, web search |

## How /swarm Works
1. **Planner** decomposes task into subtasks
2. **Worker** agents execute subtasks in parallel
3. **Reviewer** checks each subtask
4. **Planner** synthesizes and integrates

## Swarm-Bot Agent System
- **@planner** — task decomposition, never edits files
- **@worker** — executes code changes
- **@reviewer** — reviews before commit
- **@wikibot** — writes session summaries

## Coordination
- Agents communicate via shared context
- Planner tracks progress
- Reviewer approves before next step

## Constraints
- Task must be complex enough to warrant multiple agents
- Clear role separation required
- Planner stays in control

## When NOT to Use /swarm
- Simple, single-file changes
- Tasks under 30 minutes
- When a single agent can handle it
