---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/agent-intelligence/CONTEXT-ENGINEERING-GUIDE.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.465999"
}
---

# Context Engineering Guide for Legion

> Source: [Meirtz/Awesome-Context-Engineering](https://github.com/Meirtz/Awesome-Context-Engineering)  
> Paper: ["A Survey of Context Engineering for Large Language Models"](https://arxiv.org/abs/2507.13334) (arXiv:2507.13334)  
> Last updated: 2026-04-11

---

## 1. Overview

**Context Engineering** is the discipline of constructing, managing, and optimizing the information payload delivered to an LLM at inference time. Unlike static prompting, it encompasses dynamic context assembly, memory systems, retrieval pipelines, and runtime state management.

As of 2026, context engineering sits inside a broader **agent engineering** stack that includes agent harnesses, interoperability protocols (MCP, A2A), project memory, and observability.

---

## 2. RAG Patterns

### 2.1 Dense Retrieval
- Uses embedding models (e.g., sentence-transformers, OpenAI embeddings) to encode documents into vectors
- Stores vectors in a vector database (ChromaDB, Qdrant, Weaviate, Pinecone)
- At query time: embed the query, perform approximate nearest-neighbor (ANN) search
- **Legion use case**: Retrieve relevant wiki entries, past session summaries, project documentation

### 2.2 Sparse Retrieval (BM25 / TF-IDF)
- Traditional keyword-based retrieval
- Works well when exact technical terms matter (function names, API endpoints)
- No embedding model needed; fast and interpretable
- **Legion use case**: Find exact code patterns, file paths, command names

### 2.3 Hybrid Retrieval
- Combines dense (semantic) + sparse (keyword) retrieval
- Typically uses Reciprocal Rank Fusion (RRF) to merge result sets
- Preferred for production systems — captures both meaning AND specificity
- **Legion use case**: Technical queries where semantic similarity + exact terminology both matter

### 2.4 GraphRAG
- Builds a knowledge graph from documents; nodes = entities, edges = relationships
- Query-time: traverse graph to get connected context before generating
- Excels at multi-hop reasoning ("Who worked on X with Y in project Z?")
- **Legion use case**: Research tasks, understanding relationships between code modules

### 2.5 Agentic RAG
- LLM decides when to retrieve, what to retrieve, and how many retrieval steps
- Typically involves a re-ranking step (e.g., Cohere Rerank) after initial retrieval
- **Legion use case**: Complex queries that require planning before answering

---

## 3. Memory Tiers

Based on the taxonomy from [Zhang et al. "A Survey on Memory Mechanism of LLM Agents"](https://arxiv.org/abs/2404.13501):

### 3.1 Working Memory
- **What**: Current conversation context — the active context window
- **Scope**: Within a single session turn or few-shot examples
- **For Legion**: Telegram message history, current planning state, active tool results
- **Key constraint**: Limited by context window size; must be pruned/summarized

### 3.2 Episodic Memory
- **What**: Past interactions, sessions, events — "what happened"
- **Scope**: Across sessions, time-ordered
- **For Legion**: Session logs in `.wiki/logs/`, past task outcomes, failure histories
- **Key mechanism**: Mem0, MemGPT, MemoryBank — stores and retrieves conversation episodes

### 3.3 Semantic Memory
- **What**: Structured knowledge — facts, concepts, world knowledge
- **Scope**: Long-term, general-purpose
- **For Legion**: `.wiki/` contents, AGENTS.md system prompts, project documentation
- **Key mechanism**: RAG over structured docs; knowledge graphs (Graphiti, Zep)

### 3.4 Procedural Memory
- **What**: How to do things — skills, workflows, agent capabilities
- **Scope**: Persistent capability definitions
- **For Legion**: `skills/manifest.json`, skill definitions, agent role definitions
- **Key mechanism**: Skill registry, tool manifests, MCP server definitions

---

## 4. Dynamic Context Assembly

### 4.1 What to Inject When

| Trigger | Context to Inject |
|---------|------------------|
| New session | User profile, recent session summary, active projects |
| Task type detected | Relevant skill instructions, similar past task |
| Error/failure | Error history, troubleshooting patterns |
| Long conversation | Summarized history, key facts retained |
| Cross-agent handoff | Task state, reasoning so far, next steps |

### 4.2 How Much to Inject

- **Budget-aware injection**: Track token budget; allocate ~30-50% of context to relevant memories, remainder to current task
- **Relevance scoring**: Score retrieved context by cosine similarity + recency + importance
- **Progressive injection**: Start with high-confidence top-k; expand if task requires it

### 4.3 Context Quarantine
- Isolate different types of context in separate "zones" to prevent context poisoning
- Example: Keep user emotional state separate from code generation context
- Use structured metadata headers so the LLM can distinguish context types

---

## 5. Context Compression & Summarization

### 5.1 Summarization Strategies

- **Fixed-length summarization**: Compress to N tokens using an LLM summarization pass
- **Importance-weighted summarization**: Keep facts marked as high-importance; discard low-importance
- **Hierarchical summarization**: Create session summary → daily summary → weekly summary
- **Semantic compression**: Group related facts; keep one representative fact per group

### 5.2 Key Papers
- **MemFree** (open-source): Open-source full-context RAG; performs selective reference to avoid hallucination
- **SELF-RAG** ( ank et al.): Asynchronously train a RAG-augmented model that critiques its own retrievals

### 5.3 Implementation for Legion
```
Session log → LLM summarizer → Summary + importance score → Vector DB
On retrieval: top-k summaries + current context → injected
```

---

## 6. Knowledge Graph Injection

### 6.1 Pattern: GraphReader
- Builds a graph from documents; LLM agent "walks" the graph to gather context
- Uses step-by-step planning: identify relevant nodes → retrieve → reason → expand
- Better than flat RAG for multi-hop reasoning

### 6.2 Pattern: GraphRAG (Microsoft)
- Global: Leiden community detection on entity graph → generate community reports
- Local: Vector search over entity descriptions → expand neighborhood
- Handles both global ("what are the themes?") and local ("who does X?") queries

### 6.3 For Legion
- Build a knowledge graph from: `.wiki/` content, code module relationships, agent capability map
- Use Graphiti (Zep) or langchain's graph store for persistent KG

---

## 7. Citation-Backed Claims

| Claim | Source |
|-------|--------|
| RAG + tool loadout + context quarantine + pruning are core solutions | [Awesome-Context-Engineering README](https://github.com/Meirtz/Awesome-Context-Engineering) |
| Context poisoning, distraction, confusion, clash are primary failure modes |同上 |
| Model Context Protocol (MCP) standardizes context sharing between tools | 同上 |
| LangGraph provides low-level orchestration for context management | 同上 |
| Error preservation (keeping failure traces) enables model learning | 同上 |
| KV-Cache optimization reduces latency/cost via cache hit rates | 同上 |
| Append-only context maintains cache validity | 同上 |
| Hybrid RAG (dense + sparse) is preferred for production | 同上 |

---

## 8. Applying Each Pattern to Legion

| Pattern | Legion Application |
|---------|-------------------|
| **Hybrid RAG** | `.wiki/` retrieval: vector search (ChromaDB) + BM25 keyword search |
| **Agentic RAG** | @planner decides when to retrieve from wiki vs. proceed directly |
| **Memory tiers** | Working: Telegram history; Episodic: session logs; Semantic: wiki; Procedural: skills |
| **Context compression** | Long Telegram threads → LLM summarizer → compact summary stored |
| **Knowledge graphs** | Graphiti for code relationships, agent capability mapping |
| **MCP integration** | Legion self-installs MCP servers for GitHub, email, database access |
| **A2A protocol** | Future: Legion ↔ specialized sub-agents communicate via A2A |

---

## 9. Key Tools & Libraries

| Tool | Purpose |
|------|---------|
| **LangGraph** | Orchestration + context management graphs |
| **LangChain** | RAG pipelines, document loaders, vector stores |
| **LlamaIndex** | Data-focused RAG, knowledge agents |
| **ChromaDB** | Local vector store for embeddings |
| **Graphiti** (Zep) | Temporal knowledge graph for agents |
| **Mem0** | Production memory layer (User + Session + Agent memory) |
| **MCP** | Model Context Protocol — tool/context sharing standard |

---

## 10. Further Reading

- [arXiv:2507.13334](https://arxiv.org/abs/2507.13334) — A Survey of Context Engineering for LLMs
- [arXiv:2404.13501](https://arxiv.org/abs/2404.13501) — Survey on Memory Mechanism of LLM Agents
- [arXiv:2410.12837](https://arxiv.org/abs/2410.12837) — Comprehensive Survey of RAG
- [LangGraph Documentation](https://langchain-langgraph.readthedocs.io/)
- [Mem0 Documentation](https://docs.mem0.ai)
- [Graphiti/Gep](https://github.com/getzep/graphiti)
