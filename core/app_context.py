"""AppContext — single shared state object injected at startup.

Replaces module-level globals in handlers/shared.py.
Usage:
    from core.app_context import get_context, AppContext
    ctx = get_context()
    ctx.chief_of_staff.process(task)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Holds all shared enterprise singletons."""
    chief_of_staff: Optional[Any] = field(default=None)
    cost_router: Optional[Any] = field(default=None)
    budget_manager: Optional[Any] = field(default=None)
    security_guard: Optional[Any] = field(default=None)
    audit_logger: Optional[Any] = field(default=None)
    metrics_collector: Optional[Any] = field(default=None)
    session_manager: Optional[Any] = field(default=None)
    scheduler: Optional[Any] = field(default=None)

    def is_ready(self) -> bool:
        """Returns True if at minimum the ChiefOfStaff is initialised."""
        return self.chief_of_staff is not None

    def summary(self) -> str:
        loaded = [k for k, v in self.__dict__.items() if v is not None]
        missing = [k for k, v in self.__dict__.items() if v is None]
        return f"✅ Loaded: {loaded}\n⚠️ Missing: {missing}"


_ctx: Optional[AppContext] = None


def init_context(**kwargs) -> AppContext:
    """Initialise the global AppContext. Call once in on_startup."""
    global _ctx
    _ctx = AppContext(**kwargs)
    logger.info("AppContext initialised: %s", _ctx.summary())
    return _ctx


def get_context() -> AppContext:
    """Get the global AppContext. Raises if not yet initialised."""
    if _ctx is None:
        raise RuntimeError("AppContext not initialised — call init_context() in on_startup first")
    return _ctx
