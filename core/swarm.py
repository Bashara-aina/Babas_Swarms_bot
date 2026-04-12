"""Swarm enterprise layer initialization.

Extracts the swarms_bot initialization from main.py into a dedicated function.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swarms_bot.audit.audit_logger import AuditLogger
    from swarms_bot.evaluation.evaluator import AgentEvaluator
    from swarms_bot.observability.cost_metrics import CostMetricsCollector
    from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff
    from swarms_bot.routing.budget_manager import BudgetManager
    from swarms_bot.routing.cost_router import CostAwareRouter
    from swarms_bot.security.guard import SecurityGuard
    from swarms_bot.sessions.session_manager import SessionManager

logger = logging.getLogger(__name__)


def init_swarm_layer() -> None:
    """Initialize the swarms_bot enterprise layer and set shared references.

    Sets the following on the handlers.shared module:
        - _cost_router: CostAwareRouter
        - _budget_manager: BudgetManager
        - _security_guard: SecurityGuard
        - _audit_logger: AuditLogger
        - _evaluator: AgentEvaluator
        - _session_manager: SessionManager
        - _cost_metrics: CostMetricsCollector
        - _chief_of_staff: ChiefOfStaff

    All imports and initializations are wrapped in a try/except so failures
    are non-fatal and do not prevent the bot from starting.
    """
    try:
        import handlers.shared as _shared
        from swarms_bot.audit.audit_logger import AuditLogger
        from swarms_bot.evaluation.evaluator import AgentEvaluator
        from swarms_bot.observability.cost_metrics import CostMetricsCollector
        from swarms_bot.observability.logging_config import configure_structured_logging
        from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff
        from swarms_bot.routing.budget_manager import BudgetManager
        from swarms_bot.routing.cost_router import CostAwareRouter
        from swarms_bot.security.guard import SecurityGuard
        from swarms_bot.sessions.session_manager import SessionManager

        _shared._cost_router = CostAwareRouter()
        _shared._budget_manager = BudgetManager()
        _shared._security_guard = SecurityGuard()
        _shared._audit_logger = AuditLogger()
        _shared._evaluator = AgentEvaluator()
        _shared._session_manager = SessionManager()
        _shared._cost_metrics = CostMetricsCollector()

        _shared._chief_of_staff = ChiefOfStaff(
            budget_manager=_shared._budget_manager,
            security_guard=_shared._security_guard,
            audit_logger=_shared._audit_logger,
            cost_metrics=_shared._cost_metrics,
            cost_router=_shared._cost_router,
            session_manager=_shared._session_manager,
        )

        configure_structured_logging()
        logger.info("✅ swarms_bot enterprise layer initialized (with integrations)")
    except Exception as e:
        logger.warning("swarms_bot init failed (non-fatal): %s", e)
