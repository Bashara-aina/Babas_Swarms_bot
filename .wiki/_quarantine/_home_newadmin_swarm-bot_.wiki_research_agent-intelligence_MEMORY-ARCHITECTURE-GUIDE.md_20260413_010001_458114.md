---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/agent-intelligence/MEMORY-ARCHITECTURE-GUIDE.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.458135"
}
---

# Memory Architecture Guide for Legion

> Sources: [mem0ai/mem0](https://github.com/mem0ai/mem0) (52.6k stars) + [letta-ai/letta-obsidian](https://github.com/letta-ai/letta-obsidian)  
> Paper: [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413)  
> Last updated: 2026-04-11

---

## 1. Overview

This guide covers how to wire production-grade memory concepts into Legion's existing 3-tier memory system. It draws from Mem0's universal memory architecture and Letta's stateful agent memory approach.

**Key insight from Mem0 paper**: Memory is not one-size-fits-all. Effective agent memory requires distinct tiers with different retention policies, retrieval strategies, and update mechanisms.

---

## 2. Memory Tiers — What to Store Where

### 2.1 The 4-Tier Model

| Tier | Purpose | Retention | Update Frequency | For Legion |
|------|---------|-----------|------------------|------------|
| **Working** | Current task context | Per-message | Every turn | Telegram history, active tool results |
| **Episodic** | Past sessions and events | Days-weeks | After each session | Session logs in `.wiki/logs/` |
| **Semantic** | Structured knowledge and facts | Months+ | On new information | `.wiki/` contents, project docs |
| **Procedural** | Skills and how-to knowledge | Permanent | On skill change | `skills/manifest.json`, AGENTS.md |

### 2.2 What Each Tier Stores

**Working Memory (Context Window)**
```
- Current Telegram message
- Conversation history (last N messages)
- Active tool call stack
- Current task description
- Soul Engine emotional state
```
**Storage**: In-memory Python structures (list of message dicts)
**Max size**: Limited by context window (~128k tokens for MiniMax M2.7)

**Episodic Memory (Session Logs)**
```
- Completed task summaries
- Task outcomes (success/failure)
- Key decisions made during session
- User feedback received
- Error instances encountered
```
**Storage**: `.wiki/logs/` as Markdown files
**Retrieval**: RAG over log filenames + content

**Semantic Memory (Knowledge Base)**
```
- Project architecture and code structure
- User (Bashara) profile and preferences
- Business context (rumahlabuh, cekwajar)
- Academic context (thesis, research)
- Agent capability definitions
```
**Storage**: `.wiki/` as Markdown; vectorized in ChromaDB
**Retrieval**: Hybrid search (dense + sparse)

**Procedural Memory (Skill Definitions)**
```
- Available skills and their triggers
- Tool definitions (MCP servers)
- Agent roles and responsibilities
- Workflow definitions (n8n integrations)
```
**Storage**: `skills/manifest.json`, YAML configs
**Retrieval**: Direct lookup by skill name

---

## 3. Retrieval Strategies

### 3.1 Semantic Search (Dense Retrieval)
- **How**: Embed query with an embedding model → ANN search over vectors
- **Best for**: Conceptual queries, natural language questions
- **For Legion**: "What does Bashara want to do with his thesis?"
- **Implementation**: ChromaDB + sentence-transformers

### 3.2 Keyword Search (Sparse Retrieval / BM25)
- **How**: TF-IDF or BM25 scoring; match exact terms
- **Best for**: Technical queries with specific terms (file paths, function names, IDs)
- **For Legion**: "Find the Supabase schema for rumahlabuh bookings"
- **Implementation**: rank_bm25 from `rank_bm25` library

### 3.3 Hybrid Retrieval
- **How**: Combine semantic + keyword; merge with Reciprocal Rank Fusion (RRF)
- **Best for**: Queries that need both meaning AND specificity
- **For Legion**: Default mode for all wiki searches
- **Implementation**:
```python
def hybrid_search(query: str, k: int = 10):
    # Dense: semantic similarity
    dense_results = vector_db.similarity_search(query, k=k)
    
    # Sparse: keyword match
    sparse_results = bm25_index.search(query, k=k)
    
    # RRF fusion
    fused = reciprocal_rank_fusion([dense_results, sparse_results], k=60)
    return fused[:k]
```

### 3.4 Temporal Retrieval (Graphiti/Zep)
- **How**: Query knowledge graph with time constraints
- **Best for**: "What was decided in sessions from the past week?"
- **For Legion**: Session回顾, tracking progress over time

---

## 4. Importance Scoring & Forgetting

### 4.1 Mem0's Approach

Mem0 assigns **importance scores** (0-1) to each memory based on:
- **Recency**: Fresh information is more important
- **Frequency**: Repeated facts are reinforced
- **Relevance**: How often the fact is retrieved
- **User feedback**: Explicit correction/upvote/downvote signals

### 4.2 Forgetting Strategies

| Strategy | Mechanism | When to Use |
|----------|-----------|-------------|
| **Least Recently Used (LRU)** | Drop oldest when memory full | Working memory overflow |
| **Low Importance First** | Drop lowest-importance facts | Memory budget exceeded |
| **Time-based Decay** | Exponential decay: `importance *= decay^(hours)` | Episodic memory cleanup |
| **Access-based Decay** | Reduce importance if not accessed for N days | Semantic memory cleanup |

### 4.3 Importance Signals for Legion

| Signal | Weight | Source |
|--------|--------|--------|
| User explicitly stated it | +0.5 | Telegram message marked important |
| Fact affects task outcome | +0.3 | Task succeeded/failed after using it |
| Repeated in conversation | +0.2 | Same fact appears N times |
| Time-sensitive | -0.3 if expired | Appointment date passed |
| Contradicted | -0.5 | User corrected the fact |

### 4.4 Implementation
```python
class MemoryEntry:
    content: str
    importance: float = 0.5
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    
    def update_importance(self, signal: str):
        if signal == "user_affirmed":
            self.importance = min(1.0, self.importance + 0.2)
        elif signal == "contradicted":
            self.importance = max(0.0, self.importance - 0.3)
        elif signal == "accessed":
            self.access_count += 1
            self.importance = min(1.0, self.importance + 0.01 * self.access_count)
        self.last_accessed = datetime.now()
```

---

## 5. Wiring Mem0 into Legion's Existing 3-Tier Memory

### 5.1 Legion's Current Memory (from AGENTS.md)
```
core/ — Agent orchestration, intent routing, MEMORY, soul engine
swarms_bot/ — Enterprise orchestration layer (routing, sessions, security)
```

### 5.2 Gap Analysis

| Tier | Current State | Gap |
|------|---------------|-----|
| **Working** | Telegram history in memory | No automatic summarization |
| **Episodic** | Session logs written to `.wiki/logs/` | No semantic retrieval from logs |
| **Semantic** | `.wiki/` files + project docs | No vector DB; manual grep only |
| **Procedural** | `skills/manifest.json` | Skills not connected to memory |

### 5.3 Mem0 Integration Plan

**Step 1: Working Memory → Mem0 Session Memory**
```python
# core/memory/mem0_integration.py
from mem0 import Memory
from datetime import datetime

memory = Memory()  # Uses gpt-4.1-nano by default; configure for MiniMax

async def on_telegram_message(user_id: str, message: str, response: str):
    """Called after each Telegram exchange"""
    messages = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response}
    ]
    memory.add(messages, user_id=user_id)
    
async def retrieve_for_new_message(user_id: str, query: str, limit: int = 5):
    """Called at start of new session to load relevant memories"""
    results = memory.search(query=query, user_id=user_id, limit=limit)
    return [r["memory"] for r in results["results"]]
```

**Step 2: Episodic Memory → Mem0 + ChromaDB**
```python
# After each session, summarize and store
async def on_session_end(session_summary: str, user_id: str):
    """Called when Telegram conversation ends"""
    memory.add(
        f"Session summary: {session_summary}",
        user_id=user_id,
        metadata={"type": "session_summary", "timestamp": datetime.now().isoformat()}
    )
    # Also save raw log to .wiki/logs/
    save_session_log(session_summary)
```

**Step 3: Semantic Memory → ChromaDB over .wiki/**
```python
# core/memory/wiki_vector_store.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
import chromadb

chroma_client = chromadb.PersistentClient(path=".wiki/chroma_db")
wiki_collection = chroma_client.get_or_create_collection("wiki")

def index_wiki():
    """Index all .wiki/*.md files into ChromaDB"""
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    for md_file in Path(".wiki").rglob("*.md"):
        chunks = recursive_text_split(md_file.read_text())
        for i, chunk in enumerate(chunks):
            wiki_collection.add(
                documents=[chunk],
                ids=[f"{md_file.name}_{i}"],
                embeddings=[embeddings.embed_query(chunk)]
            )

def retrieve_wiki_context(query: str, k: int = 5) -> list[str]:
    results = wiki_collection.similarity_search(query, k=k)
    return [r["document"] for r in results]
```

### 5.4 Memory Wiring Diagram
```
Telegram Message
      ↓
[Working Memory] ← Mem0 Session Memory
      ↓
[Episodic Memory] ← .wiki/logs/ + Mem0 summaries
      ↓
[Semantic Memory] ← .wiki/ (vectorized) + Mem0 facts
      ↓
[Procedural Memory] ← skills/manifest.json + Mem0 agent memory
```

---

## 6. Letta's Approach to Stateful Agent Memory

### 6.1 Letta's Memory Blocks

Letta organizes agent memory into **blocks** — structured, labeled pieces of memory that can be attached/detached from agents at runtime.

**Block types**:
- **human**: Description of the user
- **persona**: Description of the agent
- **core_memory**: Essential facts the agent should always know
- **remove_memory**: Facts to forget (privacy, irrelevance)

### 6.2 Letta's Obsidian Plugin Pattern

The [letta-obsidian](https://github.com/letta-ai/letta-obsidian) plugin demonstrates:
- **Automatic vault sync**: Markdown files → Letta memory blocks
- **Real-time updates**: File changes trigger memory updates
- **Directory structure preserved**: `folder__subfolder__file.md` encoding
- **Memory block management**: Create, edit, delete blocks via chat interface

### 6.3 For Legion

Legion's `.wiki/` is already an Obsidian vault. Key insight from Letta:

> **Automatic sync means the wiki IS the agent's memory.** Every Markdown note is automatically available to the agent.

**Adoption path**:
1. Install Letta Obsidian plugin on Bashara's Obsidian vault
2. Connect to Letta cloud or self-hosted instance
3. Legion's `.wiki/` contents become persistent agent memory
4. Session summaries auto-sync to Letta memory blocks

---

## 7. Cross-Session Memory Consolidation

### 7.1 The Problem
Over time, memory becomes:
- **Fragmented**: Same fact stored in multiple places with slight variations
- **Outdated**: Old preferences that no longer apply
- **Conflicting**: Contradictory facts from different sessions

### 7.2 Consolidation Strategies

**Strategy 1: Periodic Review (Mem0's approach)**
```python
async def consolidate_memories(user_id: str, days_back: int = 7):
    """Review memories from the past N days; merge duplicates"""
    recent = memory.search(
        query="",
        user_id=user_id,
        filter={"created_at": {"$gte": days_back(days_back)}}
    )
    # LLM: "These memories may be duplicates. Merge them and keep the most accurate version."
    consolidated = llm_merge_and_deduplicate(recent)
    for mem in consolidated:
        memory.update(mem["id"], mem["content"])
```

**Strategy 2: Importance-Based Cleanup**
```python
def cleanup_memories(user_id: str, max_entries: int = 1000):
    """Keep only top-N most important memories"""
    all_memories = memory.get_all(user_id=user_id)
    sorted_by_importance = sorted(all_memories, key=lambda m: m.importance, reverse=True)
    to_delete = sorted_by_importance[max_entries:]
    for mem in to_delete:
        memory.delete(mem["id"])
```

**Strategy 3: Time-Based Forgetting**
```python
DECAY_RATE = 0.95  # 5% decay per day

def apply_decay(memory_entries: list[MemoryEntry]) -> list[MemoryEntry]:
    """Apply exponential decay to importance scores"""
    now = datetime.now()
    for entry in memory_entries:
        days_elapsed = (now - entry.last_accessed).days
        entry.importance *= (DECAY_RATE ** days_elapsed)
    return [e for e in memory_entries if e.importance > 0.1]  # Drop if decayed below threshold
```

### 7.3 For Legion
- Run consolidation weekly (via scheduler)
- After each session, run importance update on new memories
- Apply decay to memories not accessed in 7+ days
- Keep top 500 most important memories per user

---

## 8. Importance Weighting — What Makes a Fact Worth Remembering

### 8.1 Mem0's Scoring Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| **User assertion** | +0.4 | User explicitly stated this fact |
| **Task relevance** | +0.3 | Fact was used in successful task completion |
| **Recency** | +0.2 | Fact learned recently |
| **Frequency** | +0.2 | Fact mentioned multiple times |
| **Emotional salience** | +0.1 | Fact has emotional weight (praise, frustration) |

### 8.2 Priority Facts for Legion/Bashara

| Fact Category | Examples | Priority |
|---------------|----------|----------|
| **Identity** | Name, location, nationality | Critical |
| **Relationships** | Hanifah, thesis advisor, family | Critical |
| **Projects** | rumahlabuh.com, cekwajar.id, thesis | Critical |
| **Goals** | Graduate July 2026, MEXT renewal | High |
| **Preferences** | Response language, work hours | Medium |
| **Context** | Current task, active blockers | High |
| **History** | Past projects, completed tasks | Medium |

### 8.3 Anti-Patterns — Facts NOT Worth Storing

| Pattern | Reason to Discard |
|---------|------------------|
| Exact API keys / tokens | Security risk; use env vars |
| Temporary state | Will be outdated immediately |
| Emotional spikes without substance | Noise |
| Contradicted facts | Create confusion |
| Generic world knowledge | LLM already knows this |

---

## 9. Privacy Considerations for Personal Data

### 9.1 PII Categories

| Category | Examples | Handling |
|----------|----------|----------|
| **Direct identifiers** | Phone, email, address, passport | Never store in memory |
| **Financial** | Bank accounts, credit cards | Never store; use payment processors |
| **Health** | Medical conditions, medications | Never store |
| **Relationships** | Names of friends/family | Store relationships but not details |
| **Location** | Current GPS, home address | Approximate only |

### 9.2 Privacy-by-Design for Legion

**Step 1: PII Filter Before Memory Storage**
```python
import re

PII_PATTERNS = [
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD"),  # Credit card
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL"),  # Email
    (r"\b\d{10,15}\b", "PHONE"),  # Phone number
    (r"\b\d{2}/\d{2}/\d{4}\b", "DATE_OF_BIRTH"),  # DOB
]

def filter_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, f"[{replacement}]", text)
    return text

# Before storing in Mem0:
filtered_message = filter_pii(original_message)
memory.add(filtered_message, user_id=user_id)
```

**Step 2: Consent Layer**
- Bashara explicitly opts in to memory features
- Memory can be cleared on demand (`/clear_memory` command)
- Session logs can be exported or deleted

**Step 3: Data Isolation**
- Each `user_id` is isolated in Mem0
- No cross-user memory leakage
- Wiki access is user-specific

---

## 10. Implementation Roadmap for Legion

### Phase 1: Foundation (1-2 weeks)
- [ ] Install Mem0 (`pip install mem0ai`)
- [ ] Add `on_telegram_message()` hook to core bot
- [ ] Basic memory retrieval on session start
- [ ] PII filter before memory storage

### Phase 2: Semantic Memory (2-3 weeks)
- [ ] Vectorize `.wiki/` into ChromaDB
- [ ] Hybrid search for wiki retrieval
- [ ] Connect Mem0 to wiki retrieval pipeline
- [ ] Session summarizer → Mem0 after each session

### Phase 3: Consolidation & Optimization (2-4 weeks)
- [ ] Weekly consolidation job
- [ ] Importance decay applied to old memories
- [ ] Budget enforcement (max 1000 memories per user)
- [ ] Observability: log memory hit/miss rates

### Phase 4: Advanced (Future)
- [ ] Letta Obsidian plugin integration
- [ ] Temporal knowledge graph (Graphiti)
- [ ] A2A protocol for sub-agent memory sharing
- [ ] Cross-modal memory (images, voice memos)

---

## 11. Key Resources

| Resource | Link |
|----------|------|
| Mem0 Paper | [arXiv:2504.19413](https://arxiv.org/abs/2504.19413) |
| Mem0 Docs | [docs.mem0.ai](https://docs.mem0.ai) |
| Mem0 GitHub | [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0) |
| Letta Docs | [docs.letta.com](https://docs.letta.com) |
| Letta Obsidian Plugin | [github.com/letta-ai/letta-obsidian](https://github.com/letta-ai/letta-obsidian) |
| ChromaDB | [github.com/chroma-core/chroma](https://github.com/chroma-core/chroma) |
| LangChain Memory | [python.langchain.com/docs/concepts/memory](https://python.langchain.com/docs/concepts/memory) |
