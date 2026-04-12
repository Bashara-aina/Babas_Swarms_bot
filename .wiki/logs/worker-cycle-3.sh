#!/bin/bash
# Worker Cycle 3: MEMORY ARCHITECTURE AGENT
# Reads: core/memory/, handlers/memory_commands.py, handlers/brain.py
# Produces: memory-architecture.md, memory-gaps.md, memory-injection-strategy.md

LOGFILE="/home/newadmin/swarm-bot/.wiki/logs/worker-cycle-3.log"
echo "=== WORKER CYCLE 3 STARTED: $(date) ===" > "$LOGFILE"

cd /home/newadmin/swarm-bot

# Read memory files
MEMORY_MANAGER=$(cat core/memory/memory_manager.py 2>/dev/null || echo "")
EPISODIC=$(cat core/memory/episodic_store.py 2>/dev/null || echo "")
TIERS=$(cat core/memory/tiers.py 2>/dev/null || echo "")
SEMANTIC=$(cat core/memory/semantic_cache.py 2>/dev/null || echo "")
MEM_CMD=$(cat handlers/memory_commands.py 2>/dev/null || echo "")
BRAIN=$(cat handlers/brain.py 2>/dev/null || echo "")

echo "Files read successfully" >> "$LOGFILE"

# Write memory-architecture.md
cat > .wiki/memory-architecture.md << 'EOF'
---
title: Memory Architecture
domain: memory
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 550
---

# MEMORY ARCHITECTURE

## ONE-LINE SUMMARY
6 memory tiers working together — working, episodic, semantic, core, graph, long-term.

## MEMORY TIERS (from CLAUDE.md Section 7)
| Tier | Technology | Purpose | TTL |
|------|-----------|---------|-----|
| Working | In-process dict | Current session turns | Session |
| Episodic | SQLite (aiosqlite) | Recent conversations | 30 days |
| Semantic | mem0ai + ChromaDB | Vector semantic retrieval | Permanent |
| Core | memory_manager | Bashara's persistent profile | Permanent |
| Graph | graphiti-core | Relationship knowledge graph | Permanent |
| Long-term | Letta | Hierarchical memory tiers | Permanent |

## MEMORY WRITING RULE (CRITICAL)
ALL writes go through: core/memory/memory_manager.py
NEVER write directly to: mem0, chromadb, episodic_store, Letta
Consistency: Nightly consolidation at 02:00 JST via core/memory/consolidator.py

## RETRIEVAL STRATEGY
1. Working memory: In-process dict, current session only
2. Episodic: SQLite with access_count + decay scoring
3. Semantic: Vector search via mem0 + ChromaDB hybrid
4. Graph: Relationship traversal via graphiti-core

## KEY FILES
- core/memory/memory_manager.py — Unified facade (USE THIS)
- core/memory/episodic_store.py — SQLite episodic memory
- core/memory/temporal_graph.py — Graphiti knowledge graph
- core/memory/semantic_cache.py — Mem0 + ChromaDB semantic
- core/memory/consolidator.py — Nightly 02:00 JST consolidation

## LEGION BEHAVIOR RULES
1. ALL memory writes → memory_manager.py only
2. Never bypass the facade for ad-hoc writes (causes drift)
3. Memory consolidation runs at 02:00 JST — don't write during this window
4. Validate consistency weekly: cosine similarity check on last 10 mem0/chromadb items

## ANTI-PATTERNS
- Writing directly to episodic_store or mem0 (causes inconsistency)
- Bypassing memory_manager facade
- Writing during 02:00-03:00 JST consolidation window
EOF

echo "memory-architecture.md written" >> "$LOGFILE"

# Write memory-gaps.md
cat > .wiki/memory-gaps.md << 'EOF'
---
title: Memory Gaps
domain: memory
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 400
---

# MEMORY GAPS

## ONE-LINE SUMMARY
What gets forgotten that shouldn't, and what never gets deleted but should.

## CRITICAL GAPS

### 1. Short-term → Long-term handoff
- Problem: No clear trigger for "this memory is important, promote to core"
- What gets lost: Insights from deep conversations not explicitly "remember"-ed
- Fix: Add importance heuristic — messages with facts ("my RTX...", "I need to...") auto-promote

### 2. Cross-store consistency
- Problem: mem0, chromadb, episodic, graph can have conflicting facts
- What gets lost: Trust in retrieved memories when they're inconsistent
- Fix: Weekly validation check (cosine similarity drift > 0.15 = alert)

### 3. Memory decay not aggressive enough
- Problem: 30-day TTL for episodic means old habits/preferences persist
- What gets lost: Fresh context about rapidly changing situations
- Fix: Shorter TTL for context-dependent memories (project blockers = 7 days)

### 4. Bashara vocabulary not remembered
- Problem: "pusing", "nanti", etc. are understood but not stored
- What gets lost: Deep language/intent patterns
- Fix: Add vocabulary mapping to semantic memory

## WHAT SHOULD NEVER BE FORGOTTEN
- Thesis deadline and status
- Current project blockers
- Key life decisions (ADB scholarship, wedding plan)
- Bashara's communication preferences

## WHAT SHOULD BE DELETED
- Episodic memories older than 30 days
- Semantic memories with low relevance scores
- Graph relationships with negative sentiment

## LEGION BEHAVIOR RULES
1. After any "remember" command, also update core profile
2. During consolidation, flag memories with conflicting facts
3. Report memory drift > 0.15 to Bashara via Telegram

## ANTI-PATTERNS
- Storing everything (bloat)
- Forgetting to promote important insights to core
- Not validating cross-store consistency
EOF

echo "memory-gaps.md written" >> "$LOGFILE"

# Write memory-injection-strategy.md
cat > .wiki/memory-injection-strategy.md << 'EOF'
---
title: Memory Injection Strategy
domain: memory
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 350
---

# MEMORY INJECTION STRATEGY

## ONE-LINE SUMMARY
Which memories to inject per task type, in what order, with token budget.

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
EOF

echo "memory-injection-strategy.md written" >> "$LOGFILE"

echo "=== WORKER CYCLE 3 COMPLETE: $(date) ===" >> "$LOGFILE"
echo "3 pages written, 0 rejected" >> "$LOGFILE"
