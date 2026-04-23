# Stub — all real implementation moved to core/orchestrator.py
# This file re-exports all public symbols for backward compatibility

from core.orchestrator import (
    AgentResult,
    LegionAgentDef,
    LegionSwarmOrchestrator,
    SwarmReport,
    run_legion_swarm,
)

__all__ = [
    "LegionSwarmOrchestrator",
    "LegionAgentDef",
    "SwarmReport",
    "AgentResult",
    "run_legion_swarm",
]
