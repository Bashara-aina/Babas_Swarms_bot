---
title: Memory Injection Strategy
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- memory-injection-strategy.md
created: '2026-04-14'
updated: '2026-05-23'
summary: Which memories to inject per task type, in what order, with token budget — now driven by intent classification and temporal decay across 10 memory layers.
wikilinks: []
confidence: high
source: implementation
---

# MEMORY INJECTION STRATEGY

## ONE-LINE SUMMARY
Which memories to inject per task type, in what order, with token budget — powered by intent-driven 10-layer recall with exponential temporal decay.

## INJECTION BY TASK TYPE

### Code Tasks
1. Project context (which project: rumahlabuh? cekwajar? thesis?)
2. Recent code decisions from episodic (last 7 days)
3. Core facts about Bashara's preferences (verbose? concise?)
Token budget: ~800 chars

### Research Tasks
1. Thesis context (what's the current focus)
2. Mem0 semantic search for related topics
3. Graph relationships (who knows what)
Token budget: ~1200 chars

### Emotional Tasks
1. Recent emotional events from Letta
2. Current mood state
3. Relevant SOUL.md opinions
Token budget: ~600 chars

### System/Admin Tasks
1. Bot status and health
2. Recent errors or issues
3. Project blockers from core profile
Token budget: ~500 chars

## MEMORY FORMATTING FOR LLM
```
[Legion Memory — relevant context:]
- (0.95) [memory content] — [when stored]
- (0.87) [memory content] — [when stored]
[End memory context]
```

## LEGION BEHAVIOR RULES
1. Max 3000 chars of memory context per request
2. Sort by relevance score descending
3. Include "when stored" for temporal context
4. Filter out memories with score < 0.5

## ANTI-PATTERNS
- Injecting ALL memory tiers for every request
- Including low-relevance memories (>0.5 threshold)
- Forgetting to sort by recency for emotional tasks
- Not formatting for LLM scannability

---

## 10-LAYER INTENT-DRIVEN RECALL (2026-05-23)

`build_memory_context()` in `core/memory/memory_injector.py` fires all 10 layers concurrently:

| Layer | Source | Half-life | Decay rate |
|-------|--------|-----------|------------|
| L1 Checkpoints | `.session_state/checkpoints/` | 4h | very fast |
| L2 mem0 | ChromaDB vector | 12h | fast |
| L3 langmem | InMemoryStore | 24h | medium |
| L4 observation | SQLite+FTS5 | 48h | medium |
| L5 graphrag | wiki text_units | 336h (2 weeks) | very slow |
| L6 obsidian_mcp | Obsidian vault (121 tools) | 168h (1 week) | slow |
| L7 gitnexus_mcp | 68k+ symbol code graph | 1440h (60 days) | near-static |
| L8 ruflo_mcp | HNSW semantic | 72h | medium |
| L9 symphony_tasks | Active task state | 24h | fast |
| L10 mem0_cloud | litellm proxy | 24h | fast |

### Intent Classification (8 types)

Before searching, `_classify_intent(query)` identifies the query type:

| Intent | Trigger keywords | Primary layers | Decision boost |
|--------|-----------------|----------------|----------------|
| `session_summary` | "what did we", "session", "history" | checkpoints, mem0, observation | +2.0 |
| `task_list` | "todo", "task", "next", "pending" | symphony_tasks, checkpoints | — |
| `decision_recovery` | "decided", "why did we", "went with" | observation, checkpoints, graphrag | +2.0 |
| `code_implementation` | "code", "function", "where is" | gitnexus_mcp, checkpoints | — |
| `entity_facts` | "what is", "who is", "define" | graphrag, obsidian_mcp, mem0 | — |
| `bug_investigation` | "bug", "error", "not working" | observation, checkpoints | — |
| `architecture_design` | "architecture", "design", "tradeoff" | graphrag, gitnexus_mcp | +2.0 |
| `wiki_docs` | "wiki", "documentation", "docs" | graphrag, obsidian_mcp | — |

### Scoring Pipeline

```
boosted_confidence = base_conf
                   + intent_boost (per-layer relevance to intent type)
                   + recency_boost (timestamp-parsing small boost)
                   + decision_boost (2.0 if intent=decision_recovery AND content has decision keywords)
                   ↓ temporal_decay (exponential, layer-specific half-life)
                   ↓ cross_layer_boost (triangulation: 3+ layers → 1.5x, 2 layers → 1.3x)
                   ↓ final_score (sorted descending, top N)
```

### 3-Tier Progressive Output

```
━━━ MEMORY CONTEXT ━━━  intent: ⚖️  Decision Recovery  query: «why did we choose X»
   layers: 4/10  results: 12  time: 8.64s ━━━

━━ INDEX ━━       ← compact single lines: emoji + score + 1-line snippet
━━ CONTEXT ━━      ← medium detail grouped by layer: first 200 chars
━━ DECISIONS ━━   ← full content (up to 500 chars) for decision-tagged results
━━ DETAIL ━━      ← top-2 results with full content (up to 500 chars)
```

### Temporal Decay Formula

```python
decay_factor = _DECAY_BASE_RATE ** (hours_since / half_life_hours)
# base_rate = 0.85 (lower = faster decay)
# half_life = hours until decay_factor reaches 0.5
```

Example: checkpoint 54h old → 0.059 decay (very stale). graphrag 54h old → 0.967 (near-fresh).
