---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/memory-architecture.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.060866"
}
---

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
