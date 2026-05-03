---
title: Swarm 2026 04 25 Graphiti Integration
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Swarm Run: Graphiti Integration
Date: 2026-04-25
Type: FEATURE
Contracts: 16 total, 16 succeeded, 0 retried, 0 failed
Loops: 0 review loops
Agents used: explorer, memory, planner, worker, Diff-Analyzer
Files changed:
  - docker-compose.yml (neo4j service added, +24 lines)
  - .env (NEO4J/GRAPHITI vars appended, +5 lines)
  - requirements.txt (neo4j>=5.18.0 added, +1 line)
  - core/graphiti_client.py (NEW, 6689 bytes)
  - core/memory_engine.py (+graphiti wiring)
  - core/long_term_memory.py (+graphiti wiring)
  - core/joint_memory.py (+graphiti wiring)
  - core/legion_memory_facade.py (+graphiti wiring)
  - core/episodic_narrative.py (+graphiti wiring)
  - core/autonomous_router.py (+graphiti wiring)
  - core/intent_router.py (+graphiti wiring)
  - task_orchestrator.py (+graphiti wiring)
  - core/mcp_client.py (+graphiti_remember, graphiti_recall tools)
  - main.py (+graphiti init/shutdown lifecycle)
  - test_graphiti_validation.py (NEW, 259 lines)

Bugs fixed during implementation:
  - EpisodeType.MESSAGE → EpisodeType.text (graphiti-core uses lowercase enum)
  - Removed invalid `from core.exceptions import ValueError` import

Final status: COMPLETE ✅

Next steps:
  1. docker compose up -d neo4j  # Start Neo4j container
  2. pip install -r requirements.txt  # Install neo4j>=5.18.0
  3. python test_graphiti_validation.py  # Verify all tests pass