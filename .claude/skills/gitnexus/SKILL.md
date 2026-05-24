---
name: gitnexus
description: "Use when you need GitNexus code intelligence - querying the code knowledge graph, understanding code relationships, impact analysis, debugging execution flows, or exploring codebase architecture. Examples: \"How does X work?\", \"What calls this function?\", \"Show me the auth flow\", \"What breaks if I change X?\"."
---

# GitNexus MCP Server

Code intelligence via GitNexus knowledge graph.

## When to Use This MCP

- Understanding code architecture and execution flows
- Impact analysis before making changes
- Debugging by tracing execution paths
- Finding callers/callees of functions
- Querying code relationships

## Tools

| Tool | Use |
|------|-----|
| `query` | Find code by concept/execution flow |
| `context` | 360° view of a symbol (callers, callees) |
| `impact` | Blast radius analysis before changes |
| `detect_changes` | Pre-commit scope check |
| `rename` | Safe multi-file symbol renaming |
| `cypher` | Custom graph queries |

## Quick Examples

```
gitnexus_query({query: "auth validation", limit: 5})
gitnexus_context({name: "validateUser"})
gitnexus_impact({target: "validateUser", direction: "upstream"})
gitnexus_detect_changes({scope: "staged"})
```

## Resources

| Resource | Use |
|----------|-----|
| `gitnexus://repo/swarm-bot/context` | Codebase overview |
| `gitnexus://repo/swarm-bot/clusters` | Functional areas |
| `gitnexus://repo/swarm-bot/processes` | Execution flows |
| `gitnexus://repo/swarm-bot/process/{name}` | Step-by-step trace |
