# /swarm — Multi-Agent Swarm Orchestration

## What it does
`/swarm` runs a task across multiple specialized agents that are auto-selected based on capability matching, then synthesizes their findings into a unified response.

## How it works
1. **Capability Analysis** — Tokenizes the task and matches against known capability keywords
2. **Agent Selection** — Ranks agents by keyword overlap (capabilities × 3.0 + description × 1.0 + bonus for exact matches)
3. **Concurrent Execution** — Spawns top-k agents as independent async tasks
4. **Sub-agent Spawning** — Each selected agent can spawn 1-10 focused sub-agents for complex tasks (depth-limited to 2)
5. **Synthesis** — All outputs are merged by a synthesizer agent

## Usage
```
/swarm <task description>
```

## Examples
- `/swarm implement a FastAPI endpoint with JWT auth and PostgreSQL`
- `/swarm audit this Solidity smart contract for reentrancy vulnerabilities`
- `/swarm research the latest Mamba SSM papers for video understanding`

## Technical Notes
- Max depth: 2 (prevents infinite recursion)
- Sub-agents spawned via asyncio.gather for true concurrency
- Complexity heuristics: >80 words → 8 sub-agents, >40 words → 5 sub-agents, else → 3 sub-agents
- Each sub-agent gets a focused task slice (key decisions, failure modes, implementation plan, dependencies, acceptance criteria)
