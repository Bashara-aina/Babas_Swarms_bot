# /swarm — Claude Code Multi-Agent Swarm

**Usage:** `/swarm <task>`

Executes a task using multiple specialized agents that are auto-selected based on capability matching, with sub-agent spawning for complex tasks.

## How It Works

1. **Capability Analysis** — The task is tokenized and matched against 13 capability domains
2. **Agent Selection** — Top-k agents selected by weighted keyword overlap (capabilities × 3.0 + description × 1.0 + exact match bonus)
3. **Concurrent Execution** — Selected agents run in parallel via asyncio.gather
4. **Sub-agent Spawning** — Each agent spawns 3-8 focused sub-agents based on task complexity (word count: >80→8, >40→5, else→3)
5. **Synthesis** — A final synthesis agent merges all outputs

## Capability Domains

| Capability | Keywords |
|------------|----------|
| python | python, django, flask, fastapi, async, pandas |
| javascript | javascript, node, react, vue, typescript |
| cuda | cuda, gpu, kernel, nvidia, tensor |
| debug | debug, bug, fix, traceback, error |
| fastapi | fastapi, api, rest, endpoint, middleware |
| react | react, frontend, ui, component, hook |
| database | sql, postgres, query, schema |
| security | security, vulnerability, pentest, audit |
| solidity | solidity, smart-contract, ethereum |
| research | research, paper, arxiv, academic |
| design | design, ui, ux, interface |
| devops | devops, ci, docker, kubernetes |
| data | data, analytics, ml, machine-learning |

## Examples

```
/swarm implement JWT auth in FastAPI with PostgreSQL
/swarm audit this smart contract for reentrancy bugs
/swarm research Mamba SSM papers for video understanding
```

## Implementation

The swarm skill (`~/.claude/skills/swarm.py`) exports:
- `select_capabilities(task)` — scores all 13 domains
- `estimate_complexity(task)` — returns sub-agent count (3-8)
- `execute(task)` — returns formatted execution plan

Agents are spawned using Claude Code's built-in `Agent` tool with:
- `model`: claude-sonnet-4-5 (configurable)
- `tools`: all available (Bash, Read, Write, Edit, Glob, Grep, etc.)
- `subagent_type`: general-purpose

Sub-agents receive focused task slices:
1. Key technical decisions required
2. Potential failure modes
3. Implementation plan with file structure
4. Dependencies and ordering
5. Acceptance criteria

Max recursion depth: 2 (prevents infinite spawning)
