---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <query>
description: "Query GitNexus knowledge graph for code intelligence. Understand execution flows, symbol relationships, and blast radius."
---

# /codex — GitNexus code intelligence

Query the GitNexus knowledge graph for deep code understanding.

## Usage
```
/codex how does message routing work
/codex what calls get_fallback_chain
/codex show me the agent loop flow
/codex blast radius for IntentRouter
```

## What it does
- Searches execution flows by natural language query
- Returns process traces with symbol references
- Shows caller/callee relationships
- Maps blast radius for changes

## GitNexus MCP Tools Available
- `gitnexus_query` — find code by concept → returns execution flows
- `gitnexus_context` — 360° view of a symbol → callers, callees, processes
- `gitnexus_impact` — blast radius analysis → what breaks if you change X
- `gitnexus_cypher` — raw Cypher queries on the knowledge graph

## Workflow
```
1. /codex <question> → finds relevant processes/symbols
2. gitnexus_context on specific symbol → deep dive
3. READ gitnexus:// repo/process/{name} → full trace
```

## Index Staleness
If GitNexus reports index is stale, run:
```bash
npx gitnexus analyze
```

## Swarm-Bot Graph
- Repo: swarm-bot
- Symbols: 16,406
- Relationships: 38,324
- Processes: 300 execution flows
