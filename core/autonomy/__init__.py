"""Ruflo Autonomy Layer — transparent nervous system for SwarmBot.

Implements the Autonomy Layer master prompt v2:
  - Part II:  Automatic boot sequence
  - Part III: Task interception / classification
  - Part IV:  Three execution modes (DIRECT / LITE / SWARM)
  - Part V:   Topology + agent assignment lookup
  - Part VI:  Memory auto-routing (ruflo + mem0 + obsidian)
  - Part VII: Context enrichment (pre-flight for every task)
  - Part VIII: Security layer (always-on, invisible)
  - Part IX:  Observability (silent telemetry)
  - Part X:   Session teardown
  - Part XI:   User communication rules
  - Part XII:  Self-healing
  - Part XIII: Neural learning accumulation
"""

from core.autonomy.autonomy_engine import AutonomyEngine, get_autonomy_engine

__all__ = [
    "AutonomyEngine",
    "get_autonomy_engine",
]