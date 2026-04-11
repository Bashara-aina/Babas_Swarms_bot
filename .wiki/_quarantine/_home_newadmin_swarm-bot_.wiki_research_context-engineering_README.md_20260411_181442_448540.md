---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/context-engineering/README.md",
  "reason": "daily_fast_scan: score=0.050 < 0.3",
  "score": 0.05,
  "quarantined_at": "2026-04-11T18:14:42.448561"
}
---

# Awesome Context Engineering

Source: https://github.com/yzfly/awesome-context-engineering

## What This Is
A curated collection of resources, papers, tools, and best practices for Context Engineering — the art and science of filling the LLM context window with the right information at each step of an agent's trajectory.

## Why Legion Cares
- **Wiki retrieval**: Legion's `_wiki_layer()` is a context engineering problem — this repo teaches how to retrieve + generate optimally
- **Performance optimization**: KV-Cache, context compression, and pruning techniques directly apply to Legion's 800ms budget for parallel context gathering
- **Memory tiers**: How to wire working/episodic/semantic memory across context windows

## Key Concepts
- **Context Retrieval**: RAG, knowledge graphs, vector stores — what to retrieve and when
- **Context Processing**: KV-Cache optimization, append-only context for cache validity
- **Context Compression**: Pruning, summarization, distillation for large contexts
- **Context Isolation**: Separate context spaces per concern (emotion, memory, skills)
- **MCP (Model Context Protocol)**: Standardizes context sharing between tools and agents

## Detailed Pages (for depth)
- `.wiki/research/agent-intelligence/CONTEXT-ENGINEERING-GUIDE.md` — Legion-specific context patterns
- `.wiki/research/agent-intelligence/MEMORY-ARCHITECTURE-GUIDE.md` — how to wire memory to context
- `.wiki/tools/MCP-SERVERS-AVAILABLE.md` — MCP servers for context management
