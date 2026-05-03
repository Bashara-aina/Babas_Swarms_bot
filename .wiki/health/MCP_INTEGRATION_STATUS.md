---
title: Mcp Integration Status
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# MCP INTEGRATION STATUS
Generated: 2026-05-03

## Servers (12/12)

| Server | Tools | Transport | Native Usage |
|--------|-------|-----------|--------------|
| gitnexus | 7 | stdio | Auto-called before any edit |
| obsidian | 80+ | stdio | Wiki read/write for all knowledge |
| git | 19 | stdio | All git operations |
| filesystem | 14 | stdio | All file I/O |
| exa | 2 | remote | Fast web search |
| crawl4ai | 4 | stdio | URL scraping & extraction |
| symphony | 9 | stdio | Workflow orchestration |
| latex | 9 | stdio | LaTeX file intelligence |
| ruflo | 39 | stdio | Swarm agents + memory |
| sequential-thinking | 1 | stdio | Multi-step reasoning |
| hermes | 6 | stdio | Agentic loops + skill memory |
| browser-use | 8 | stdio | Interactive browser (MiniMax only) |

## Memory Layers
- mem0ai 1.0.11 + ChromaDB + Ollama nomic-embed-text ✅
- langmem 0.0.30 ✅
- graphrag 3.0.9 ✅
- Redis 6.0.16 ✅

## Model Policy
- PRIMARY: minimax/MiniMax-M2.7 via LiteLLM :4000
- browser-use: MiniMax-M2.7 ONLY (no fallback)
- hermes: MiniMax-M2.7 via cli-config.yaml

## Agents: 297 across 24 departments
## Slash Commands: 33 + skill-based extensions
## Wiki: 129 notes, 95MB