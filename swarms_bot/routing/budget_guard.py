"""Budget guard — singleton wrapper around BudgetManager with can_spend() API.

Provides a simple can_spend() interface for guardrails before LLM calls.
"""

from swarms_bot.routing.budget_manager import BudgetManager

_budget_guard: BudgetManager | None = None


class BudgetExceededError(Exception):
    """Raised when a budget cap is exceeded."""


def get_budget_guard() -> BudgetManager:
    """Get or create the global BudgetManager singleton."""
    global _budget_guard
    if _budget_guard is None:
        _budget_guard = BudgetManager()
    return _budget_guard


def set_budget_guard(guard: BudgetManager) -> None:
    """Set the global BudgetManager singleton (for testing)."""
    global _budget_guard
    _budget_guard = guard
