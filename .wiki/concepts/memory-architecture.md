---
title: "Memory Architecture"
created: 2026-05-03
tags: [memory, architecture, legion]
wikilinks: []
---

# Memory Architecture

> ⚠️ STUB — Full content pending. Created 2026-05-03 by audit v2.

## 5-Tier Memory Pyramid

| Tier | Name | Storage | Read | Write | TTL |
|------|------|---------|------|-------|-----|
| T1 | HOT | /tmp/legion_*.txt | session boot | end-of-session | session |
| T2 | WORKING | memory_manager.py facade | facade only | facade only | conversation |
| T3 | EPISODIC | SQLite (aiosqlite) | facade only | facade only | 30 days |
| T4 | SEMANTIC | mem0 vector store | hermes_search_memory | hermes_write_skill | permanent |
| T5 | STRUCTURAL | .wiki/ Obsidian | obsidian_search_notes | obsidian_create_note | permanent |

## Key Files

- `core/memory/memory_manager.py` — facade routing all writes
- `core/memory/episodic_store.py` — SQLite episodic storage
- `core/integrations/graphiti_integration.py` — temporal knowledge graph
- `tools/mem0_client.py` — mem0 vector store client

## Read Routes

See `core/TIER.py` for constant definitions + write routing table.
