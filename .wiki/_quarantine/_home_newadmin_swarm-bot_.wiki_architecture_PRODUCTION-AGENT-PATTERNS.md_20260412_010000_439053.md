---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/PRODUCTION-AGENT-PATTERNS.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.439076"
}
---

# Production Agent Patterns for Legion

> Source: [EthicalML/awesome-production-agentic-systems](https://github.com/EthicalML/awesome-production-agentic-systems)  
> Categories: Agentic Frameworks, Observability, Protocols, Memory, Security  
> Last updated: 2026-04-11

---

## 1. Overview

This document covers production-grade patterns for deploying, monitoring, and scaling agentic systems. It bridges the gap between "working prototype" and "production-ready" by addressing memory at scale, context management, multi-agent orchestration, observability, and security.

---

## 2. Memory Management at Scale

### 2.1 Mem0 — Production Memory Layer

**What it is**: Universal memory layer purpose-built for AI agents with multi-level memory (User, Session, Agent).

**Key stats**: +26% accuracy over OpenAI Memory on LOCOMO benchmark, 91% faster, 90% fewer tokens.

**Architecture**:
```
User Memory → User preferences, long-term facts
Session Memory → Current conversation context
Agent Memory → Agent-specific state and capabilities
```

**How it works**:
1. Embed incoming facts/interactions into vectors
2. Store in vector DB (ChromaDB, Pinecone, Qdrant, etc.)
3. At retrieval: semantic search + importance scoring + recency weighting
4. Return top-k relevant memories as context

**For Legion**:
```python
from mem0 import Memory
memory = Memory()

# After each Telegram interaction
memory.add(messages, user_id="bashara")

# On new session start
memories = memory.search(query=user_query, user_id="bashara", limit=5)
```

### 2.2 Graphiti — Temporal Knowledge Graphs

**What it is**: Builds temporally-aware knowledge graphs from agent interactions.

**Key feature**: Tracks *when* facts were learned, enabling "what did the agent know at time T?" queries.

**For Legion**: Build a knowledge graph of Bashara's life events, project milestones, and appointments.

### 2.3 LangMem — Long-Term Memory for LangChain

**What it is**: Memory management primitives for LangChain agents.

**Key patterns**:
- **Mem0 memory store**: Plug-and-play Mem0 as LangChain memory
- **Summary memory**: Compress history into summaries
- **Buffer memory**: Sliding window of recent interactions

**For Legion**: Use LangMem with LangGraph for agent state management.

---

## 3. Context Management Protocols

### 3.1 The Problem
- Context windows are expensive at scale
- Append-only context preserves KV-cache validity (MCP best practice)
- Context poisoning/distraction/confusion/clash are primary failure modes

### 3.2 Solutions from Awesome-Context-Engineering

| Pattern | Mechanism | Legion Use |
|---------|-----------|------------|
| **Context pruning** | Remove low-relevance context before it enters the window | Prune old Telegram messages |
| **Context summarization** | LLM summarizer pass to compress | Summarize long sessions before storage |
| **Context quarantine** | Isolate context types to prevent cross-contamination | Keep Soul Engine state separate from code gen |
| **KV-Cache optimization** | Cache context embeddings; only compute deltas | Already in llm_client.py |
| **RAG + tool loadout** | Retrieve relevant docs + load available tools | `.wiki/` RAG + skills manifest |

### 3.3 Context Budget Enforcement
```python
CONTEXT_BUDGET = {
    "max_tokens": 128000,      # MiniMax context limit
    "memory allocation": 0.40,  # 40% for memories
    "task_allocation": 0.50,    # 50% for current task
    "buffer": 0.10              # 10% reserved
}
```

---

## 4. A2A (Agent-to-Agent) Protocol

### 4.1 What It Is
**A2A** (Agent-to-Agent) is Google's open protocol for enabling agents built on different frameworks by different companies to communicate and collaborate — as agents, not just as tools.

**Key principle**: Tools are stateless; agents are stateful. A2A enables stateful handoffs between agents.

### 4.2 A2A vs MCP
| Aspect | MCP | A2A |
|--------|-----|-----|
| **Model** | Client-server | Peer-to-peer |
| **State** | Stateless (tools) | Stateful (agents) |
| **Use case** | Tool access | Agent collaboration |
| **Scope** | Single tool calls | Multi-step, multi-agent workflows |
| **Anthropic/Google** | Anthropic pioneered | Google/agentcosystem |

### 4.3 For Legion
- `@planner` → `@worker` handoff: Could use A2A for richer state transfer
- Future: Legion ↔ specialized sub-agents (DatabaseAgent, WebSearchAgent)
- A2A enables "negotiation" patterns where agents share partial results

### 4.4 Related Protocols
| Protocol | Purpose | Status |
|----------|---------|--------|
| **A2A** | Agent-to-agent collaboration | Active (Google/agentcosystem) |
| **ACP** | Agent Client Protocol for code editors | Active |
| **ANP** | Agent Network Protocol | Active |
| **AG-UI** | Agent-Generated User Interface | Active |
| **MCP** | Tool/context sharing (see MCP-SERVERS-AVAILABLE.md) | Dominant standard |

---

## 5. Composio Integrations

### 5.1 What It Is
**Composio** equips AI agents with 100+ high-quality integrations via function calling. Think of it as "100+ MCP servers with enterprise SLAs."

### 5.2 Key Integration Categories
| Category | Tools |
|----------|-------|
| **Code** | GitHub, GitLab, Jira, Linear |
| **Communication** | Slack, Gmail, Notion, Calendar |
| **CRM** | Salesforce, HubSpot |
| **Commerce** | Stripe, Shopify |
| **Product** | Figma, Airtable |

### 5.3 For Legion
- Replace individual MCP server integrations with Composio for production-grade reliability
- Use Composio's auth management (OAuth flows handled)
- Batch tool updates — Composio maintains tool definitions as APIs evolve

---

## 6. Budget Enforcement & Cost Optimization

### 6.1 Token Budgeting
```python
class TokenBudget:
    def __init__(self, max_tokens: int = 128000):
        self.max_tokens = max_tokens
        self.used_tokens = 0
        
    def allocate(self, purpose: str, fraction: float) -> int:
        allocation = int(self.max_tokens * fraction)
        return allocation
    
    def check(self, required: int) -> bool:
        return (self.used_tokens + required) <= self.max_tokens
    
    def reserve(self, tokens: int) -> None:
        self.used_tokens += tokens
```

### 6.2 Cost Optimization Strategies
| Strategy | Mechanism | Savings |
|----------|-----------|---------|
| **KV-Cache reuse** | Append-only context; cache hits | 30-60% latency reduction |
| **Context compression** | Summarize before storing | 50-80% tokens saved |
| **Selective retrieval** | Only retrieve when needed | 20-40% fewer LLM calls |
| **Model routing** | Use cheaper model for simple tasks | 50-90% cost reduction |

### 6.3 Budget for Legion
- Current: ~$40/month total AI spend
- Target: Stay under $50/month with added capabilities
- Strategy: Use MiniMax M2.7 (primary) + Claude Sonnet 4.6 (fallback) + local models (future)

---

## 7. Observability & Tracing

### 7.1 Why Observability Matters
Agents fail in complex ways: tool call failures, context overflows, hallucinated facts, infinite loops. Without observability, you can't debug.

### 7.2 Key Tools

| Tool | What it does | For Legion |
|------|--------------|------------|
| **LangSmith** | End-to-end tracing, evaluation, prompt management | Already uses LangChain |
| **AgentOps** | Session recording, cost tracking, error analysis | Add for agent monitoring |
| **IntellAgent** | Multi-agent conversation benchmarking | Future multi-agent testing |
| **Manifest** | Open-source, local-first observability | Alternative to cloud tools |
| **OpenTelemetry** | Standard semantic conventions for GenAI | For custom tracing |

### 7.3 Core Observability Signals
```python
# What to trace per agent call
tracing_payload = {
    "session_id": "telegram-123",
    "agent": "planner",
    "input_tokens": len(encode(user_message)),
    "output_tokens": len(encode(response)),
    "tool_calls": [{"tool": "search", "args": {...}, "result": "..."}],
    "latency_ms": elapsed_time,
    "errors": [error_instances],
    "memory_retrieved": [{"fact": "...", "source": "mem0", "relevance": 0.87}]
}
```

### 7.4 For Legion
- Add structured logging to `@planner`, `@worker`, `@reviewer`
- Use LangSmith for tracing (already uses LangChain)
- Consider AgentOps for session recording and cost tracking
- Log to `.wiki/logs/` as secondary persistence

---

## 8. Error Handling & Recovery

### 8.1 Error Categories
| Category | Example | Recovery Strategy |
|----------|---------|-------------------|
| **Tool failure** | API timeout, auth expired | Retry with backoff; fall back to alternative tool |
| **Context overflow** | Context window exceeded | Summarize + prune; defer sub-task |
| **LLM hallucination** | Confident but wrong | Add verification step; check against known facts |
| **Infinite loop** | Agent loops without progress | Max iterations guard; intervention prompt |
| **State corruption** | Memory store inconsistent | Rebuild from session logs; checkpoint restore |

### 8.2 Error Preservation Pattern
> From Awesome-Context-Engineering: "Error preservation (keeping failure traces) enables model learning."

```python
# Preserve error context for learning
error_log = {
    "task": "search_recent_commits",
    "error": "RateLimitError: GitHub API rate limit exceeded",
    "context": {"repo": "bashara/swarm-bot", "since": "2026-04-01"},
    "recovery_attempted": "Switched to GitHub MCP search",
    "recovery_succeeded": True,
    "timestamp": "2026-04-11T03:14:00+09:00"
}
# Store in .wiki/logs/errors/ for future reference
```

### 8.3 For Legion
- `@planner` maintains a `failed_task_log` in session state
- `@worker` catches and preserves tool errors with full context
- `@reviewer` checks for hallucination patterns against wiki facts

---

## 9. Multi-Agent Orchestration Patterns

### 9.1 Framework Comparison

| Framework | Strength | For Legion |
|-----------|----------|-----------|
| **LangGraph** | Graph-based state machines, deeply production-grade | Already used; scale to sub-agents |
| **CrewAI** | Role-based agents, Fortune 500 adoption | Define 9 department agents as CrewAI crew |
| **AutoGen** | Flexible conversation patterns | Complex multi-agent conversations |
| **OpenAI Agents SDK** | Official OpenAI, handoffs as first-class | Future consideration |
| **smolagents** | Lightweight, HuggingFace-native | Lightweight tasks |
| **Swarms** | Enterprise multi-agent at scale | If Legion grows to team orchestration |

### 9.2 Orchestration Patterns

**Pattern 1: Planner-Executor Chain**
```
@planner (decomposes) → @worker (executes) → @reviewer (validates)
```

**Pattern 2: Specialized Sub-Agents**
```
@planner → DatabaseAgent
        → WebSearchAgent  
        → EmailAgent
        → FileAgent
```

**Pattern 3: CrewAI-Style Department Crews**
```
Department Head Agent (orchestrator)
  → Researcher Agent
  → Analyst Agent
  → Communicator Agent
```

### 9.3 For Legion
- **Immediate**: Enhance 3-agent pipeline with error recovery and state persistence
- **Short-term**: Add specialized sub-agents (DatabaseAgent already exists)
- **Long-term**: Use A2A protocol for peer-to-peer agent communication

---

## 10. Security & Data Privacy

### 10.1 Critical Rules
1. **Never expose API keys in logs or error messages**
2. **Mask .env files from context** — use `os.getenv()` references only
3. **PII masking**: Filter personal data (phone numbers, addresses) before memory storage
4. **Session isolation**: Each user's memory should be isolated by `user_id`

### 10.2 Privacy by Memory Tier
| Tier | Data Type | Privacy Concern | Mitigation |
|------|-----------|-----------------|------------|
| Working | Telegram messages | May contain PII | Auto-filter before storage |
| Episodic | Session summaries | User context | Encrypted at rest |
| Semantic | Wiki entries | Project/business | Access-controlled |
| Procedural | Skill definitions | System prompts | No PII; safe |

### 10.3 Security Tools
| Tool | Purpose |
|------|---------|
| **LangSmith** | Audit logs, PII detection |
| **opencode-envsitter-guard** | Prevent .env leaks (from OpenCode Elite) |
| **AgentOps** | Session recording with privacy controls |
| **Composio** | Enterprise auth (OAuth, API keys managed) |

### 10.4 For Legion
- **Current**: No PII in wiki (except BASHARA-MASTER-PROFILE.md — which is intentional)
- **Action**: Add PII filter before adding Telegram messages to Mem0
- **Action**: Add `.env` check in `@reviewer` before any commit

---

## 11. Production Readiness Checklist

| Category | Requirement | Legion Status |
|----------|-------------|---------------|
| **Memory** | Cross-session memory with user isolation | 🟡 Mem0 integration needed |
| **Observability** | Structured tracing of all agent calls | 🟡 Basic logging; needs LangSmith |
| **Error handling** | Error preservation + recovery | 🟡 Basic retry; needs structured error log |
| **Cost control** | Token budget enforcement | 🔴 Not implemented |
| **Security** | PII filtering, .env protection | 🟡 Reviewer checks .env; needs PII filter |
| **Scalability** | Multi-agent orchestration | 🟡 3-agent pipeline; sub-agents needed |
| **Protocols** | MCP + A2A adoption | 🟡 MCP skills; A2A not implemented |
| **Reliability** | SLOs, health checks, graceful degradation | 🔴 Not implemented |

---

## 12. Further Reading

- [LangGraph Documentation](https://langchain-langgraph.readthedocs.io/)
- [Mem0 Research Paper](https://arxiv.org/abs/2504.19413)
- [A2A Protocol Specification](https://a2a-protocol.org/latest/)
- [LangSmith Observability](https://docs.langchain.com/langsmith/observability-quickstart)
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Composio Documentation](https://docs.composio.io/)
