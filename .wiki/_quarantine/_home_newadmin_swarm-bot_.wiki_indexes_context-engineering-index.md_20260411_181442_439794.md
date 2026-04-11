---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/indexes/context-engineering-index.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-11T18:14:42.439828"
}
---

# Context Engineering Index
Source: ~/swarm-bot/.wiki/research/context-engineering

## Summary
Context Engineering is the systematic optimization of information payloads for LLMs. It encompasses context retrieval, processing, management, compression, and isolation. Key strategies include: Write Context (save outside window), Select Context (pull relevant info), Compress Context (retain only necessary tokens), and Isolate Context (split across spaces). Context failures occur via poisoning, distraction, confusion, and clash patterns. Solutions include RAG, tool loadout, context quarantine, pruning, summarization, and offloading.

## Top 10 Context Engineering Principles
- Context window optimization is non-trivial — too little/irrelevant hurts performance, too much increases cost
- Use KV-Cache for performance optimization (cache hit rates reduce latency/cost)
- Append-only context maintains cache validity — avoid modifying previous context
- Treat file systems as external context memory
- Mask, don't remove tools for better action selection in agents
- Context poisoning, distraction, confusion, and clash are primary failure modes
- RAG + tool loadout + context quarantine + pruning are core solutions
- Model Context Protocol (MCP) standardizes context sharing between tools
- LangGraph provides low-level orchestration for context management
- Error preservation (keeping failure traces) enables model learning

## Key Frameworks Mentioned
- LangGraph: orchestration framework
- LangSmith: agent tracing/evaluation
- LangMem: memory management
- Claude Code: auto-compact context management
- Reflexion: memory systems
- RAG: retrieval-augmented generation
