"""Orchestration layer for multi-agent collaboration in SwarmBot.

This module provides two complementary orchestration systems:

* **Supervisor** (`supervisor.py`) — Hierarchical task decomposition and execution.
  Breaks complex tasks into atomic SubTasks, schedules them sequentially or in parallel
  (up to MAX_PARALLEL=3), and synthesizes results via the mentor agent.
  Activated when tasks exceed COMPLEXITY_THRESHOLD (120 tokens) or contain
  multi-step keywords or cross-domain indicators.

* **Swarm Patterns** (`swarm_patterns.py`) — Peer-based collaboration patterns.
  - Voting: N agents solve independently → judge selects the best
  - Critique-Refine: producer generates → critic reviews → producer refines (iterative)
  - Debate: agents argue proposals → architect synthesizes consensus
  Includes `select_pattern()` heuristics to pick the right pattern for a task.

Both systems delegate actual LLM calls to the provided `run_fn` callback, keeping
this layer purely about coordination and flow control.
"""

from __future__ import annotations
