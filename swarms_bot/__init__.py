"""swarms_bot — Enterprise-grade agentic AI platform for LegionSwarm.

Provides:
- ChiefOfStaff orchestrator with deterministic routing
- Cost-aware model selection with cascade pattern
- Security guards (prompt injection, PII redaction)
- Audit logging for compliance
- Agent evaluation metrics
"""

from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff, Task, TaskType
from swarms_bot.orchestrator.dag_executor import DAGExecutor
from swarms_bot.orchestrator.model_router import ModelRouter
