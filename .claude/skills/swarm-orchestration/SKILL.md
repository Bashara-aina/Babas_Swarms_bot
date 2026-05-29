---
name: "Swarm Orchestration"
description: "Auto-trigger for: run agents in parallel, coordinate multiple agents, multi-agent workflow, swarm orchestration, use multiple agents, parallelize tasks, agent team, distribute work across agents, complex task needs multiple agents, build with swarm, deploy agent team, research with multiple agents, full-stack with frontend and backend agents, test with agent team, analyze with specialists. Use when scaling beyond single agents, implementing complex workflows, or building distributed AI systems. Activates automatically when task involves multiple agents, parallel execution, distributed AI, or swarm coordination."
---

# Swarm Orchestration

## What This Skill Does

Orchestrates multi-agent swarms using agentic-flow's advanced coordination system. Supports mesh, hierarchical, and adaptive topologies with automatic task distribution, load balancing, and fault tolerance.

## Auto-Execute (Native Claude Code Feel)

When invoked, this skill automatically selects and runs the best swarm pattern — no extra prompting needed:

```python
from core.orchestration.swarm_patterns import select_pattern, debate, voting, critique_refine

# Auto-select best pattern from task description
pattern = select_pattern(task)  # returns: "voting" | "critique_refine" | "debate" | None

# Auto-execute with anti-loop, convergence, and self-audit built-in
if pattern == "debate":
    result = await debate(task, debaters=[...], run_fn=...)
elif pattern == "voting":
    result = await voting(task, agents=[...], run_fn=...)
elif pattern == "critique_refine":
    result = await critique_refine(task, producer=..., critic=..., run_fn=...)
else:
    # Fall back to concurrent swarm topology
    result = await run_topology(task, topology="auto", agent_names=[...])
```

The swarm automatically:
- **Stops loops** — AntiLoopGuard fires after 2x same action, 3 identical results, or 8+ tool calls
- **Gates confidence** — ConfidenceGate blocks irreversible actions below 90%
- **Thinks between steps** — ThinkingProtocol injected between agent rounds
- **Labels evidence** — P1-P6 evidence hierarchy on all claims
- **Self-audits** — LEGIONA SELF-AUDIT footer on every output
- **Converges early** — 70% agreement triggers early termination in debate/voting
- **Preserves dissent** — Minority reports saved after consensus
- **Learns** — Sessions recorded to self-evolution engine

## Prerequisites

- agentic-flow v3.0.0-alpha.1+
- Node.js 18+
- Understanding of distributed systems (helpful)

## Quick Start

```bash
# Initialize swarm
npx agentic-flow hooks swarm-init --topology mesh --max-agents 5

# Spawn agents
npx agentic-flow hooks agent-spawn --type coder
npx agentic-flow hooks agent-spawn --type tester
npx agentic-flow hooks agent-spawn --type reviewer

# Orchestrate task
npx agentic-flow hooks task-orchestrate \
  --task "Build REST API with tests" \
  --mode parallel
```

## Topology Patterns

### 1. Mesh (Peer-to-Peer)
```typescript
// Equal peers, distributed decision-making
await swarm.init({
  topology: 'mesh',
  agents: ['coder', 'tester', 'reviewer'],
  communication: 'broadcast'
});
```

### 2. Hierarchical (Queen-Worker)
```typescript
// Centralized coordination, specialized workers
await swarm.init({
  topology: 'hierarchical',
  queen: 'architect',
  workers: ['backend-dev', 'frontend-dev', 'db-designer']
});
```

### 3. Adaptive (Dynamic)
```typescript
// Automatically switches topology based on task
await swarm.init({
  topology: 'adaptive',
  optimization: 'task-complexity'
});
```

## Task Orchestration

### Parallel Execution
```typescript
// Execute tasks concurrently
const results = await swarm.execute({
  tasks: [
    { agent: 'coder', task: 'Implement API endpoints' },
    { agent: 'frontend', task: 'Build UI components' },
    { agent: 'tester', task: 'Write test suite' }
  ],
  mode: 'parallel',
  timeout: 300000 // 5 minutes
});
```

### Pipeline Execution
```typescript
// Sequential pipeline with dependencies
await swarm.pipeline([
  { stage: 'design', agent: 'architect' },
  { stage: 'implement', agent: 'coder', after: 'design' },
  { stage: 'test', agent: 'tester', after: 'implement' },
  { stage: 'review', agent: 'reviewer', after: 'test' }
]);
```

### Adaptive Execution
```typescript
// Let swarm decide execution strategy
await swarm.autoOrchestrate({
  goal: 'Build production-ready API',
  constraints: {
    maxTime: 3600,
    maxAgents: 8,
    quality: 'high'
  }
});
```

## Memory Coordination

```typescript
// Share state across swarm
await swarm.memory.store('api-schema', {
  endpoints: [...],
  models: [...]
});

// Agents read shared memory
const schema = await swarm.memory.retrieve('api-schema');
```

## Advanced Features

### Load Balancing
```typescript
// Automatic work distribution
await swarm.enableLoadBalancing({
  strategy: 'dynamic',
  metrics: ['cpu', 'memory', 'task-queue']
});
```

### Fault Tolerance
```typescript
// Handle agent failures
await swarm.setResiliency({
  retry: { maxAttempts: 3, backoff: 'exponential' },
  fallback: 'reassign-task'
});
```

### Performance Monitoring
```typescript
// Track swarm metrics
const metrics = await swarm.getMetrics();
// { throughput, latency, success_rate, agent_utilization }
```

## Integration with Hooks

```bash
# Pre-task coordination
npx agentic-flow hooks pre-task --description "Build API"

# Post-task synchronization
npx agentic-flow hooks post-task --task-id "task-123"

# Session restore
npx agentic-flow hooks session-restore --session-id "swarm-001"
```

## Best Practices

1. **Start small**: Begin with 2-3 agents, scale up
2. **Use memory**: Share context through swarm memory
3. **Monitor metrics**: Track performance and bottlenecks
4. **Enable hooks**: Automatic coordination and sync
5. **Set timeouts**: Prevent hung tasks

## Troubleshooting

### Issue: Agents not coordinating
**Solution**: Verify memory access and enable hooks

### Issue: Poor performance
**Solution**: Check topology (use adaptive) and enable load balancing

## Learn More

- Swarm Guide: docs/swarm/orchestration.md
- Topology Patterns: docs/swarm/topologies.md
- Hooks Integration: docs/hooks/coordination.md
