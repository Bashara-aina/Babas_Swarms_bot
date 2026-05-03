# Elite Stack Session Lifecycle

## SESSION START (Every Session)

```python
# 1. Verify ruflo is healthy
ruflo system_status

# 2. Restore last session (continue where left off)
ruflo session_restore { "name": "latest" }

# 3. Search relevant memory for current task
ruflo memory_search { "query": "<task>", "namespace": "all", "limit": 5 }

# 4. Check neural patterns for similar past tasks
ruflo neural_predict { "task": "<task>" }
# → Use predicted approach if confidence > 0.7

# 5. Verify MiniMax M2.7 is default provider
ruflo provider_list
```

## SESSION WORK (Per Task)

### Decision Tree
1. **3+ independent subtasks** → `swarm_init` (mesh) + `agent_spawn` each
2. **Sequential phases** → `swarm_init` (hierarchical) + `task_create` per phase
3. **Need persist knowledge** → `memory_store` after task complete
4. **Code will be reused** → `session_save` + `neural_train` at end
5. **PII/APIs involved** → `security_scan` + `pii_detect` BEFORE processing
6. **Single one-step task** → Direct MCP tools (skip ruflo)

### Swarm Execution
```python
# Init swarm with correct topology
ruflo swarm_init { "topology": "<mesh|hierarchical|ring|star>", "max_agents": 6 }

# Spawn agents — ALWAYS specify model
ruflo agent_spawn {
  "role": "<backend-developer|research-analyst|test-generator|...>",
  "objective": "<specific task>",
  "model": "minimax/MiniMax-M2.7",
  "api_base": "https://api.minimax.io/v1",
  "max_tokens": 32768,
  "temperature": 0.2,  # coding
  # temperature: 0.7,  # research
  "tools": ["filesystem", "git", ...],
  "memory_namespace": "<project/context>"
}

# Track with tasks
ruflo task_create { "title": "...", "priority": "high" }
ruflo task_status { "task_id": "..." }
ruflo task_complete { "task_id": "...", "result": "success" }
```

## SESSION END (Every Session)

```python
# 1. Save full session snapshot
ruflo session_save { "name": "session-$(date +%Y%m%d-%H%M)", "include_memory": true }

# 2. Export for backup
ruflo session_export { "format": "json", "destination": "~/.legion/sessions/" }

# 3. Write decisions to obsidian wiki
# obsidian create_note or write directly to .wiki/

# 4. Store learnings to mem0
python3 -c "from tools.mem0_client import get_mem0; ..."

# 5. Neural training on success (only if outcome=success)
ruflo neural_train { "pattern": "...", "outcome": "success", "context": "..." }
```

## Temperature Guidelines

| Task Type | Temperature | Example |
|-----------|-------------|---------|
| Coding (precise) | 0.2 | Refactor, implement, debug |
| Research (exploratory) | 0.7 | Research, analysis, brainstorming |
| Creative (diverse) | 0.8-1.0 | Writing, design, ideation |

## Model Requirement

**CRITICAL**: Every `agent_spawn` MUST include `"model": "minimax/MiniMax-M2.7"`
- Never let ruflo default to Claude/GPT/Gemini
- Always pass `api_base: "https://api.minimax.io/v1"`
- MiniMax M2.7 has 1M token context — use it