# Ruflo Autonomy Layer — Reference Manual v1

> **Status:** Reference Manual (v1)
> **Load Order:** This document loads BEFORE `ruflo_minimax_master_prompt.md` (v2 behavioral wiring). Both must be present for full operation.
> **Version:** 1.0 | 2026-04-24

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Memory Architecture](#2-memory-architecture)
3. [Swarm Orchestration](#3-swarm-orchestration)
4. [Neural Learning](#4-neural-learning)
5. [Hooks System](#5-hooks-system)
6. [MCP Tools Reference](#6-mcp-tools-reference)
7. [AgentDB v3](#7-agentdb-v3)
8. [Configuration](#8-configuration)
9. [WASM Agents](#9-wasm-agents)
10. [Observability](#10-observability)

---

## 1. System Overview

### 1.1 What is Ruflo?

Ruflo is the **nervous system** of the autonomous coding stack — invisible infrastructure that runs before, during, and after every task. It is not a tool you call; it is always already running.

Ruflo provides:
- **Memory** — Hierarchical persistent context across sessions
- **Orchestration** — Multi-agent spawning and coordination
- **Learning** — Neural pattern accumulation from experience
- **Hooks** — Event-driven automation at key lifecycle points
- **Observability** — Performance metrics and health monitoring

### 1.2 Nervous System Metaphor

| Biological | Ruflo | Purpose |
|------------|-------|---------|
| CNS | OpenCode/Legion | Primary inference engine |
| Spinal cord | MCP tools | Tool execution pathway |
| Autonomic NS | Hooks system | Background automation |
| Memory | AgentDB/Hierarchical memory | Persistent context |
| Reflexes | Pre-built workflows | Instant responses |
| Learning | SONA/EWC++ | Long-term pattern growth |

### 1.3 Integration with OpenCode/Legion

Ruflo runs as an MCP server (`ruflo_mcp_server`) that OpenCode connects to via stdio. The integration layer allows:

- **Tool calls** — All `ruflo_*` tools exposed via MCP protocol
- **Agent spawning** — Legion agents coordinated through Ruflo
- **Memory access** — Semantic search across all sessions
- **Event hooks** — Triggers fire at appropriate lifecycle points

```
┌─────────────────────────────────────────────────────────┐
│                    OpenCode / Legion                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Ruflo MCP Client                     │   │
│  │  (ruflo_* tools via stdio)                      │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ stdio
┌──────────────────────▼──────────────────────────────────┐
│                  Ruflo MCP Server                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│  │ Memory   │ │ Swarm    │ │ Neural   │ │ Hooks   │  │
│  │ Engine   │ │ Engine   │ │ Engine   │ │ Engine  │  │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘  │
│  ┌─────────────────────────────────────────────────┐   │
│  │              AgentDB v3 (sql.js + HNSW)          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.4 Boot Sequence

When OpenCode starts, Ruflo executes a silent boot sequence:

```
BOOT STEP 1: Health check (ruflo: system_status + ruflo: doctor)
BOOT STEP 2: Session restore (ruflo: session_restore { "name": "latest" })
BOOT STEP 3: Memory load (ruflo: neural_patterns_list)
BOOT STEP 4: Worker activation (4 background workers dispatched)
BOOT STEP 5: Hook registration (5 hooks registered)
```

Total target: < 7 seconds, fully silent.

---

## 2. Memory Architecture

### 2.1 Hierarchical Memory Tiers

Ruflo implements a three-tier memory hierarchy:

```
┌─────────────────────────────────────────────────────────┐
│  SEMANTIC (Long-term)                                   │
│  - Persisted to disk (sql.js)                          │
│  - HNSW vector index for semantic search                │
│  - Pattern library, learned behaviors                  │
│  - Decays: never (permanent)                           │
├─────────────────────────────────────────────────────────┤
│  EPISODIC (Session)                                     │
│  - In-memory during session                            │
│  - Auto-saved to AgentDB on session end                │
│  - Complete task memories, decisions, outcomes         │
│  - Decays: after 30 days of inactivity                │
├─────────────────────────────────────────────────────────┤
│  WORKING (Immediate)                                    │
│  - LRU cache, sub-second access                        │
│  - Current task context, recent retrievals             │
│  - Decays: after 1 hour of inactivity                 │
└─────────────────────────────────────────────────────────┘
```

### 2.2 AgentDB v3 Architecture

AgentDB is the persistence layer for all Ruflo memory:

```python
# AgentDB Schema (simplified)
class Episode:
    id: str              # UUID
    tier: str             # "working" | "episodic" | "semantic"
    namespace: str        # Project/organization scope
    key: str              # Unique within namespace
    value: str            # JSON-encoded content
    embedding: bytes      # 384-dim float32 vector (HNSW)
    created_at: float     # Unix timestamp
    accessed_at: float    # Last access time
    access_count: int    # LRU tracking
    metadata: dict        # Tags, TTL, source info
```

**Storage backends:**
- **Default:** sql.js (SQLite compiled to WebAssembly)
- **Optional:** PostgreSQL for production scale
- **Index:** HNSWlib for vector similarity search

### 2.3 Semantic Search

Ruflo uses **HNSW (Hierarchical Navigable Small World)** for semantic search:

```python
# Search example (via ruflo_memory_search)
{
    "query": "authentication implementation patterns",
    "namespace": "project/swarm-bot",
    "limit": 5,
    "threshold": 0.3,
    "smart": true  # Enables: query expansion, RRF fusion, recency boost, MMR
}
```

**How it works:**
1. Query text → embedded via ONNX model (`Xenova/all-MiniLM-L6-v2`)
2. HNSW traversal finds k-nearest neighbors by cosine similarity
3. Results filtered by threshold (default 0.3)
4. Smart mode applies: query expansion, Reciprocal Rank Fusion, recency boost

### 2.4 Memory Operations

| Operation | Tool | Description |
|-----------|------|-------------|
| Store | `ruflo_memory_store` | Write with auto-embedding |
| Retrieve | `ruflo_memory_retrieve` | Direct key lookup |
| Search | `ruflo_memory_search` | Semantic vector search |
| List | `ruflo_memory_list` | Namespace listing |
| Delete | `ruflo_memory_delete` | Key deletion |

### 2.5 Namespaces

Memory is partitioned by namespace:

| Namespace | Purpose | Example keys |
|-----------|---------|--------------|
| `default` | General purpose | — |
| `project/<name>` | Per-project memory | `project/swarm-bot:auth-implementation-v1` |
| `pattern` | Learned patterns | `sona:auth-validation-success` |
| `session/<id>` | Session-scoped | `session/abc123:task-001` |
| `claude-memories` | Imported Claude Code memories | — |

---

## 3. Swarm Orchestration

### 3.1 Agent Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ SPAWNED  │ ──▶ │ RUNNING  │ ──▶ │ COMPLETE │ ──▶ │TERMINATED│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │
                      ▼
                 ┌──────────┐
                 │  ERROR   │ ──▶ Re-spawn (max 2 retries)
                 └──────────┘
```

### 3.2 Topology Types

Ruflo supports six swarm topologies:

| Topology | Best For | Agent Count | Consensus |
|----------|----------|-------------|-----------|
| `hierarchical` | Feature development, pipelines | 4-5 | Raft leader |
| `mesh` | Equal peers, complex coordination | 3-5 | Gossip |
| `ring` | Sequential processing, pipelines | 3-4 | Raft token |
| `star` | Central coordinator + workers | 4+1 | Central |
| `hybrid` | Mixed workloads | Variable | Multi |
| `hierarchical-mesh` | Large-scale, complex | 10+ | Nested raft |

### 3.3 Consensus Strategies

**Raft (Default)**
- Leader election with term numbers
- Log replication across agents
- Anti-drift protection
- Use for: structured tasks, clear ownership

```json
{
    "strategy": "raft",
    "term": 1,
    "quorumPreset": "majority"
}
```

**Byzantine (BFT)**
- Tolerates f < n/3 faulty agents
- More expensive, slower
- Use for: untrusted environments, critical consensus

```json
{
    "strategy": "byzantine",
    "faultTolerance": 1
}
```

**Quorum**
- Configurable threshold voting
- Flexible consistency
- Use for: approximate consensus, voting scenarios

```json
{
    "strategy": "quorum",
    "quorumPreset": "supermajority"
}
```

**Gossip**
- eventual consistency
- No leader, all agents equal
- Use for: mesh topologies, decentralized coordination

### 3.4 Swarm Initialization

```python
ruflo_swarm_init({
    "topology": "hierarchical",
    "maxAgents": 5,
    "strategy": "specialized",  # specialized | balanced | adaptive
    "config": {
        "leader": "planner",
        "consensus": "raft"
    }
})
```

### 3.5 Agent Spawning

```python
ruflo_agent_spawn({
    "agentType": "worker",
    "agentId": "backend-developer-1",
    "domain": "backend",
    "model": "haiku",  # haiku | sonnet | opus | inherit
    "task": "Implement the /api/auth/login endpoint with JWT"
})
```

**Agent Types:**
| Type | Role | Default Model |
|------|------|---------------|
| `worker` | Task execution | sonnet |
| `planner` | Task decomposition | opus |
| `reviewer` | Code review | sonnet |
| `researcher` | Information gathering | haiku |
| `specialist` | Domain expertise | configurable |

### 3.6 Hive Mind

Hive Mind is Ruflo's multi-agent coordination layer:

```python
# Initialize hive
ruflo_hive_mind_init({
    "topology": "mesh",           # mesh | hierarchical | ring | star
    "consensus": "raft",          # raft | byzantine | gossip | crdt | quorum
    "queenId": "orchestrator-1"
})

# Spawn workers that auto-join hive
ruflo_hive_mind_spawn({
    "count": 3,
    "role": "worker",             # worker | specialist | scout
    "agentType": "worker",
    "prefix": "hive-worker"
})

# Broadcast to all workers
ruflo_hive_mind_broadcast({
    "message": "New task: refactor auth module",
    "priority": "high",
    "fromId": "orchestrator-1"
})

# Shared memory across agents
ruflo_hive_mind_memory({
    "action": "set",
    "key": "current-task",
    "value": "auth-refactor"
})
```

---

## 4. Neural Learning

### 4.1 SONA (Instant Adaptation)

SONA (Self-Optimizing Neural Adaptor) provides <1ms adaptation cycles:

```python
# Create SONA instance
ruflo_ruvllm_sona_create({
    "hiddenDim": 64,
    "learningRate": 0.01,
    "patternCapacity": 100
})

# Adapt with quality signal
ruflo_ruvllm_sona_adapt({
    "sonaId": "sona-abc123",
    "quality": 0.85  # 0.0 - 1.0 quality signal
})
```

**Use cases:**
- Immediate feedback to agent actions
- Quality-weighted memory consolidation
- Adaptive routing decisions

### 4.2 EWC++ (Consolidation)

Elastic Weight Consolidation++ prevents catastrophic forgetting:

```python
# Run consolidation after significant learning
ruflo_hooks_intelligence_learn({
    "trajectoryIds": ["traj-001", "traj-002"],
    "consolidate": true  # Triggers EWC++
})
```

**How EWC++ works:**
1. Identify important parameters (Fisher information)
2. Compute penalty for deviating from learned weights
3. Apply consolidated updates to pattern store
4. Tag patterns with confidence scores

### 4.3 Pattern Training

Patterns are trained via `ruflo_neural_train`:

```python
ruflo_neural_train({
    "modelType": "moe",  # moe | transformer | classifier | embedding
    "epochs": 10,
    "learningRate": 0.001,
    "data": {
        "patterns": [
            {"input": "auth validation", "output": "use_jwt_verify"},
            {"input": "db query", "output": "use_connection_pool"}
        ],
        "context": {
            "stack": "python/fastapi",
            "project": "swarm-bot"
        }
    }
})
```

### 4.4 Trajectory System

Trajectories track multi-step learning episodes:

```python
# Start trajectory
ruflo_hooks_intelligence_trajectory_start({
    "task": "Learn to route auth tasks optimally",
    "agent": "router-agent"
})

# Record steps
ruflo_hooks_intelligence_trajectory_step({
    "trajectoryId": "traj-abc123",
    "action": "route_auth_to_specialist",
    "result": "success",
    "quality": 0.9
})

# End and trigger learning
ruflo_hooks_intelligence_trajectory_end({
    "trajectoryId": "traj-abc123",
    "success": true,
    "feedback": "High quality routing observed"
})
```

### 4.5 RuVector Intelligence

RuVector provides attention-weighted semantic routing:

```python
# Initialize with hyperbolic embeddings
ruflo_embeddings_init({
    "model": "Xenova/all-MiniLM-L6-v2",
    "hyperbolic": true,      # Poincaré ball embeddings
    "curvature": -1,
    "cacheSize": 256
})

# Attention-weighted search
ruflo_hooks_intelligence_attention({
    "query": "authentication patterns",
    "mode": "hyperbolic",    # flash | moe | hyperbolic
    "topK": 5
})
```

---

## 5. Hooks System

### 5.1 Hook Architecture

Hooks are event-driven triggers that fire at key lifecycle points:

```
┌─────────────────────────────────────────────────────────┐
│                    OpenCode Event                       │
│  (command, edit, task, session lifecycle)              │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   Hooks Engine                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 17 Hook Events × Configurable Actions           │    │
│  │  • pre_*  — Block/modify before action          │    │
│  │  • post_* — React after action                  │    │
│  │  • on_*   — Autonomous triggers                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 Action Execution                         │
│  security_scan, memory_store, neural_train, etc.        │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Complete Hook Events

| Hook Event | Trigger | Action Types | Blockable |
|------------|----------|--------------|-----------|
| `pre_command` | Before command execution | `security_scan`, `pii_detect` | Yes |
| `post_command` | After command completes | `memory_store`, `neural_train` | No |
| `pre_edit` | Before file edit | `context_retrieve`, `pre_task` | Yes |
| `post_edit` | After file edit | `memory_store`, `neural_train` | No |
| `pre_task` | Before task start | `agent_suggest`, `context_retrieve` | Yes |
| `post_task` | After task completes | `memory_store`, `neural_train` | No |
| `on_commit` | Git commit triggered | `security_scan`, `pii_detect` | Yes |
| `pre_git_commit` | Before git commit | `pii_detect`, `security_scan` | Yes |
| `on_pr_create` | PR opened | `review_trigger`, `test_trigger` | No |
| `on_merge` | PR merged | `deploy_trigger`, `notify` | No |
| `on_session_start` | New session begins | `memory_restore`, `context_load` | No |
| `on_session_end` | Session ends | `memory_store`, `session_save` | No |
| `on_conversation_turn` | Each user message | `context_enrich`, `intent_classify` | No |
| `task_success` | Task completed successfully | `neural_train`, `memory_store` | No |
| `task_failure` | Task failed | `neural_train`, `error_log` | No |
| `agent_error` | Agent threw error | `agent_restart`, `escalate` | No |
| `pre_agent_spawn` | Before agent spawn | `context_load`, `model_select` | Yes |

### 5.3 Hook Configuration

```python
# Register a hook
ruflo_hooks_trigger({
    "event": "pre_git_commit",
    "action": "security_scan",
    "config": {
        "checks": ["pii_detect", "api_key_exposure"],
        "block_on_fail": true
    }
})

# Register memory store on task success
ruflo_hooks_trigger({
    "event": "task_success",
    "action": "memory_store",
    "config": {
        "auto_tag": true,
        "also_store_to": ["mem0", "obsidian"]
    }
})

# Register neural training on task success
ruflo_hooks_trigger({
    "event": "task_success",
    "action": "neural_train",
    "config": {
        "min_confidence_threshold": 0.7,
        "pattern_namespace": "elite-stack"
    }
})
```

### 5.4 Hook Action Reference

| Action | Inputs | Outputs | Blockable |
|--------|--------|---------|-----------|
| `security_scan` | paths, checks | {issues[], blocked: bool} | Yes |
| `pii_detect` | paths, patterns | {pii_found[], blocked: bool} | Yes |
| `memory_store` | namespace, key, value | {stored: bool} | No |
| `memory_search` | query, namespace | {results[]} | No |
| `neural_train` | pattern, outcome, context | {trained: bool} | No |
| `agent_suggest` | task, context | {agents[], confidence[]} | Yes |
| `model_select` | task, context | {model: str, confidence: float} | Yes |
| `context_retrieve` | query, types | {context: obj} | No |
| `session_save` | name, include_memory | {saved: bool} | No |
| `session_restore` | name | {restored: bool, context: obj} | No |
| `notify` | target, message, priority | {sent: bool} | No |
| `agent_restart` | agent_id, reason | {restarted: bool} | No |
| `escalate` | agent_id, reason, context | {escalated: bool} | No |

---

## 6. MCP Tools Reference

### 6.1 Tool Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Memory | 8 | Hierarchical storage and search |
| Swarm | 7 | Agent orchestration |
| Neural | 6 | Learning and adaptation |
| Hooks | 20+ | Event-driven automation |
| Config | 6 | Configuration management |
| System | 5 | Health and observability |
| WASM | 8 | Sandboxed agent execution |
| Coordination | 8 | Multi-agent coordination |
| GitHub | 3 | Repository integration |
| Transfer | 5 | IPFS and plugin store |
| Embeddings | 8 | Vector operations |
| ruvLLM | 7 | LLM-specific operations |
| Claims | 10 | Task ownership tracking |
| Workflow | 7 | Workflow execution |

### 6.2 Memory Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_memory_store` | `{key, value, namespace?, tags?, ttl?, upsert?}` | Store with auto-embedding |
| `ruflo_memory_retrieve` | `{key, namespace?}` | Direct key lookup |
| `ruflo_memory_search` | `{query, namespace?, limit?, threshold?, smart?}` | Semantic vector search |
| `ruflo_memory_list` | `{namespace?, limit?, offset?}` | List namespace entries |
| `ruflo_memory_delete` | `{key, namespace?}` | Delete entry |
| `ruflo_memory_stats` | `{}` | Get storage statistics |
| `ruflo_memory_migrate` | `{force?}` | Migrate legacy JSON to sql.js |

### 6.3 Swarm Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_swarm_init` | `{topology, maxAgents, strategy, config?}` | Initialize swarm |
| `ruflo_swarm_status` | `{swarmId?}` | Get swarm status |
| `ruflo_swarm_shutdown` | `{swarmId, graceful?}` | Shutdown swarm |
| `ruflo_swarm_health` | `{swarmId?}` | Check swarm health |
| `ruflo_agent_spawn` | `{agentType, agentId?, domain?, model?, task}` | Spawn agent |
| `ruflo_agent_list` | `{status?, domain?, includeTerminated?}` | List agents |
| `ruflo_agent_terminate` | `{agentId, force?}` | Terminate agent |

### 6.4 Neural Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_neural_train` | `{modelType, modelId?, epochs?, learningRate?, data}` | Train model |
| `ruflo_neural_predict` | `{modelId?, input, topK?}` | Make predictions |
| `ruflo_neural_status` | `{modelId?, detailed?}` | Get model status |
| `ruflo_neural_optimize` | `{modelId, target}` | Optimize performance |
| `ruflo_neural_compress` | `{modelId, method, targetSize?}` | Compress model |
| `ruflo_neural_patterns` | `{action, patternId?, name?, type?, query?, data?}` | Manage patterns |

### 6.5 Embeddings Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_embeddings_generate` | `{text, hyperbolic?, normalize?}` | Generate embedding |
| `ruflo_embeddings_search` | `{query, topK?, threshold?, namespace?}` | Semantic search |
| `ruflo_embeddings_compare` | `{text1, text2, metric?}` | Compare similarity |
| `ruflo_embeddings_hyperbolic` | `{action, embedding?, embedding1?, embedding2?}` | Hyperbolic ops |
| `ruflo_embeddings_rabitq_build` | `{force?}` | Build RaBitQ index |
| `ruflo_embeddings_rabitq_search` | `{query, k?, namespace?}` | Fast Hamming search |
| `ruflo_embeddings_rabitq_status` | `{}` | Get RaBitQ status |
| `ruflo_embeddings_status` | `{}` | Get embeddings status |

### 6.6 System Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_system_status` | `{verbose?, components?}` | Overall health |
| `ruflo_system_info` | `{include?}` | System information |
| `ruflo_system_health` | `{deep?, components?, fix?}` | Deep health check |
| `ruflo_system_metrics` | `{category?, timeRange?, format?}` | Performance metrics |
| `ruflo_system_reset` | `{component, confirm}` | Reset component |

### 6.7 Configuration Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_config_get` | `{key, scope?}` | Get config value |
| `ruflo_config_set` | `{key, value, scope?}` | Set config value |
| `ruflo_config_list` | `{scope?, prefix?, includeDefaults?}` | List config |
| `ruflo_config_reset` | `{scope?, key?}` | Reset to defaults |
| `ruflo_config_export` | `{scope?, includeDefaults?}` | Export as JSON |
| `ruflo_config_import` | `{config, scope?, merge?}` | Import from JSON |

### 6.8 WASM Agent Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `ruflo_wasm_agent_create` | `{template?, model?, instructions?, maxTurns?}` | Create agent |
| `ruflo_wasm_agent_prompt` | `{agentId, input}` | Send prompt |
| `ruflo_wasm_agent_tool` | `{agentId, toolName, toolInput}` | Execute tool |
| `ruflo_wasm_agent_terminate` | `{agentId}` | Terminate agent |
| `ruflo_wasm_agent_list` | `{}` | List agents |
| `ruflo_wasm_agent_files` | `{agentId}` | Get agent tools |
| `ruflo_wasm_agent_export` | `{agentId}` | Export state |
| `ruflo_wasm_gallery_list` | `{}` | List gallery templates |
| `ruflo_wasm_gallery_create` | `{template}` | Create from template |

---

## 7. AgentDB v3

### 7.1 Architecture

AgentDB v3 is the memory and learning substrate:

```
┌─────────────────────────────────────────────────────────┐
│                     AgentDB v3                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Controller Layer                     │    │
│  │  • MemoryController  • LearningController       │    │
│  │  • ReasoningController  • SemanticRouter        │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Storage Layer (sql.js)              │    │
│  │  Episodes | Patterns | Trajectories | Config     │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Index Layer (HNSW)                   │    │
│  │  Vector similarity | BM25 keyword | Hybrid       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Controllers

| Controller | Purpose | Key Operations |
|------------|---------|-----------------|
| `MemoryController` | Hierarchical storage | store, retrieve, consolidate |
| `LearningController` | Pattern training | train, adapt, consolidate |
| `ReasoningController` | Trajectory tracking | start, step, end, analyze |
| `SemanticRouter` | Intent classification | route, score, explain |
| `NightlyLearner` | Background consolidation | run, schedule, cancel |

### 7.3 Session Management

```python
# Start session with episodic replay
ruflo_agentdb_session_start({
    "sessionId": "session-abc123",
    "context": "Refactoring authentication module"
})

# Store episodic memory
ruflo_agentdb_hierarchical_store({
    "key": "auth-refactor-approach",
    "value": "Split JWT validation into separate validator",
    "tier": "episodic"
})

# Recall from episodic memory
ruflo_agentdb_hierarchical_recall({
    "query": "previous auth refactoring decisions",
    "tier": "episodic",
    "topK": 5
})

# End session, trigger consolidation
ruflo_agentdb_session_end({
    "sessionId": "session-abc123",
    "summary": "Completed auth module refactor",
    "tasksCompleted": 7
})
```

### 7.4 Hierarchical Recall

```python
ruflo_agentdb_hierarchical_recall({
    "query": "authentication error handling patterns",
    "tier": "semantic",          # working | episodic | semantic
    "topK": 10,
    "filter": {
        "namespace": "project/swarm-bot",
        "tags": ["auth", "security"]
    }
})
```

**Recall algorithm:**
1. Query working cache (sub-ms)
2. If miss, query episodic table
3. If miss, query semantic with HNSW
4. Apply recency boost and MMR diversity
5. Return merged, deduplicated results

### 7.5 Pattern Store and Search

```python
# Store pattern
ruflo_agentdb_pattern_store({
    "pattern": "auth validation always use JWT library, never roll own crypto",
    "type": "security-best-practice",
    "confidence": 0.95,
    "metadata": {
        "source": "security-audit",
        "project": "swarm-bot"
    }
})

# Search patterns
ruflo_agentdb_pattern_search({
    "query": "password hashing recommendations",
    "topK": 5,
    "minConfidence": 0.7
})
```

### 7.6 Causal Memory Graph

```python
# Record causal relationship
ruflo_agentdb_causal_edge({
    "sourceId": "memory-abc",
    "targetId": "memory-xyz",
    "relation": "caused",        # caused | preceded | succeeded | related
    "weight": 0.85
})

# Context synthesis
ruflo_agentdb_context_synthesize({
    "query": "why did we choose RS256 over HS256?",
    "maxEntries": 10
})
```

---

## 8. Configuration

### 8.1 Configuration Scopes

| Scope | Persistence | Override Priority |
|-------|-------------|-------------------|
| `system` | Global default | Lowest |
| `user` | User-level preferences | Middle |
| `project` | Per-repo settings | Highest |

### 8.2 Configuration Keys

**Memory Configuration:**
```json
{
    "memory.default_namespace": "default",
    "memory.hnsw.ef_search": 128,
    "memory.hnsw.ef_construction": 200,
    "memory.hnsw.m": 16,
    "memory.cache.size": 1024,
    "memory.cache.ttl.working": 3600,
    "memory.cache.ttl.episodic": 2592000
}
```

**Swarm Configuration:**
```json
{
    "swarm.max_agents": 50,
    "swarm.default_topology": "hierarchical",
    "swarm.default_consensus": "raft",
    "swarm.agent_timeout": 300,
    "swarm.spawn_retry_limit": 2
}
```

**Neural Configuration:**
```json
{
    "neural.embedding.model": "Xenova/all-MiniLM-L6-v2",
    "neural.embedding.dimensions": 384,
    "neural.sona.learning_rate": 0.01,
    "neural.ewc.fisher_multiplier": 3000,
    "neural.training.default_epochs": 10
}
```

**Hooks Configuration:**
```json
{
    "hooks.auto_enable": true,
    "hooks.pre_commit.checks": ["pii_detect", "security_scan"],
    "hooks.post_task.store_memory": true,
    "hooks.session.auto_save": true
}
```

### 8.3 Configuration Operations

```python
# Get value
ruflo_config_get({
    "key": "memory.default_namespace",
    "scope": "project"
})

# Set value
ruflo_config_set({
    "key": "swarm.max_agents",
    "value": 25,
    "scope": "project"
})

# List all project config
ruflo_config_list({
    "scope": "project",
    "includeDefaults": false
})

# Export configuration
ruflo_config_export({
    "scope": "project",
    "includeDefaults": true
})

# Import configuration
ruflo_config_import({
    "config": {"memory.default_namespace": "my-project"},
    "scope": "project",
    "merge": true
})

# Reset to defaults
ruflo_config_reset({
    "scope": "project",
    "key": "memory.default_namespace"
})
```

---

## 9. WASM Agents

### 9.1 Gallery Templates

Pre-built agent templates:

| Template | Purpose | Default Tools |
|---------|---------|---------------|
| `coder` | General code writing | read_file, write_file, edit_file, list_files |
| `researcher` | Information gathering | search, read_file, analyze |
| `tester` | Test generation | read_file, write_file, run_tests |
| `reviewer` | Code review | read_file, analyze, comment |
| `security` | Security audit | read_file, analyze, scan |
| `swarm` | Multi-agent coordination | spawn, coordinate, merge |

### 9.2 Creating WASM Agents

```python
# Create from gallery template
ruflo_wasm_gallery_create({
    "template": "coder"
})

# Create with custom instructions
ruflo_wasm_agent_create({
    "model": "anthropic:claude-sonnet-4-20250514",
    "instructions": "You are a Python security expert. Always check for SQL injection, XSS, and hardcoded secrets.",
    "maxTurns": 50
})

# List available templates
ruflo_wasm_gallery_list()
```

### 9.3 Interacting with WASM Agents

```python
# Send prompt
ruflo_wasm_agent_prompt({
    "agentId": "wasm-agent-abc123",
    "input": "Review the auth.py file for security vulnerabilities"
})

# Execute specific tool
ruflo_wasm_agent_tool({
    "agentId": "wasm-agent-abc123",
    "toolName": "read_file",
    "toolInput": {
        "path": "/code/auth.py"
    }
})

# List agent capabilities
ruflo_wasm_agent_files({
    "agentId": "wasm-agent-abc123"
})
```

### 9.4 WASM Agent Characteristics

**Advantages:**
- Fully sandboxed (no OS access)
- Reproducible execution
- Parallel execution support
- Resource isolation

**Limitations:**
- No filesystem access outside sandbox
- No network access
- Limited to bundled tools
- Max 50 conversation turns default

---

## 10. Observability

### 10.1 Metrics Categories

| Category | Metrics | Use Case |
|----------|---------|----------|
| `cpu` | utilization, temperature, per-core | Performance tuning |
| `memory` | used, available, swap, heap | Memory pressure |
| `latency` | p50, p95, p99, tail | SLA monitoring |
| `throughput` | requests/sec, tokens/sec | Capacity planning |
| `agents` | active, queued, errors | Swarm health |
| `tasks` | completed, failed, pending | Task tracking |

### 10.2 Performance Metrics

```python
# Get metrics
ruflo_performance_metrics({
    "metric": "latency",
    "aggregation": "p95",
    "timeRange": "1h"
})

# Get all metrics
ruflo_performance_metrics({
    "metric": "all",
    "timeRange": "24h",
    "format": "json"
})

# Performance report
ruflo_performance_report({
    "timeRange": "7d",
    "format": "detailed",
    "components": ["memory", "neural", "swarm"]
})
```

### 10.3 Bottleneck Detection

```python
# Detect bottlenecks
ruflo_performance_bottleneck({
    "component": "all",
    "threshold": 0.8,    # Alert at 80% utilization
    "deep": true          # Include root cause analysis
})
```

**Automatic thresholds:**
| Component | Warning | Critical |
|-----------|---------|----------|
| CPU | >70% | >90% |
| Memory | >75% | >90% |
| Latency p95 | >500ms | >1000ms |
| Error rate | >1% | >5% |

### 10.4 Benchmarks

```python
# Run benchmark suite
ruflo_performance_benchmark({
    "suite": "all",      # all | memory | neural | swarm | io
    "iterations": 100,
    "warmup": true
})

# Profile specific component
ruflo_performance_profile({
    "target": "neural.embeddings",
    "duration": 30,
    "sampleRate": 100
})
```

### 10.5 Optimization

```python
# Apply optimizations
ruflo_performance_optimize({
    "target": "memory",      # memory | latency | throughput | all
    "aggressive": false
})
```

**Available optimizations:**
| Target | Optimizations |
|--------|---------------|
| `memory` | LRU tuning, cache warming, HNSW optimization |
| `latency` | Connection pooling, batch processing, prefetch |
| `throughput` | Parallel agents, async I/O, batch inference |

### 10.6 System Health

```python
# Quick health check
ruflo_system_status()

# Detailed health with component status
ruflo_system_health({
    "deep": true,
    "components": ["memory", "neural", "swarm"],
    "fix": true           # Attempt automatic fixes
})
```

---

## Appendix A: Quick Reference

### Boot Sequence
```python
ruflo_system_status()
ruflo_session_restore({ "name": "latest" })
ruflo_neural_patterns_list()
ruflo_worker_dispatch({ "worker": "audit", "trigger": "session_start" })
ruflo_worker_dispatch({ "worker": "memory_consolidate", "trigger": "session_end" })
```

### Task Execution
```python
ruflo_task_create({ "type": "feature", "description": "..." })
ruflo_agent_spawn({ "agentType": "worker", "task": "..." })
ruflo_task_complete({ "taskId": "...", "result": "success" })
ruflo_neural_train({ "pattern": "...", "outcome": "success" })
```

### Session Save
```python
ruflo_session_save({
    "name": "auto-$(date +%Y%m%d-%H%M)",
    "includeMemory": true
})
```

---

## Appendix B: Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `E001` | MCP server not running | Start with `python3 -m mcp_servers.ruflo_mcp_server` |
| `E002` | Agent spawn failed | Check model availability, reduce agent count |
| `E003` | Memory store failed | Check disk space, run migration |
| `E004` | Swarm consensus timeout | Increase timeout, check network |
| `E005` | Neural training failed | Check data format, reduce batch size |
| `E006` | Hook blocked action | Review and approve or adjust hook config |
| `E007` | WASM agent timeout | Increase maxTurns or simplify task |
| `E008` | Config scope conflict | Use correct scope priority |

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **AgentDB** | Ruflo's memory and learning substrate (v3) |
| **EWC++** | Elastic Weight Consolidation++ — prevents catastrophic forgetting |
| **HNSW** | Hierarchical Navigable Small World — vector index algorithm |
| **Hive Mind** | Ruflo's multi-agent coordination layer |
| **MCP** | Model Context Protocol — tool/exposure standard |
| **MMR** | Maximal Marginal Relevance — diversity in search results |
| **RaBitQ** | 1-bit quantized vector index (32x compression) |
| **RRF** | Reciprocal Rank Fusion — combining multiple result sets |
| **SONA** | Self-Optimizing Neural Adaptor — instant adaptation |
| **Trajectory** | Multi-step learning episode tracking |

---

> **Document Version:** 1.0 | **Last Updated:** 2026-04-24
> **See Also:** `ruflo_minimax_master_prompt.md` (v2 behavioral wiring)
