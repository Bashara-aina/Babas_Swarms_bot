"""handlers package — registers all routers with the aiogram Dispatcher.

Import order matters: the NL catch-all handler (in ai.py) must be registered
last so command filters are checked first.
"""
from __future__ import annotations

from aiogram import Dispatcher

from .computer import router as computer_router
from .system import router as system_router
from .research import router as research_router
from .brain import router as brain_router
from .sessions import router as sessions_router
from .tasks import router as tasks_router
from .dev import router as dev_router
from .pm import router as pm_router
from .enterprise import router as enterprise_router
# ai router is last — it contains the F.text NL catch-all which must fire after
# all specific command/text filters have been checked
from .ai import router as ai_router


def register_all_routers(dp: Dispatcher) -> None:
    """Include every handler router into the Dispatcher."""
    dp.include_router(computer_router)
    dp.include_router(system_router)
    dp.include_router(research_router)
    dp.include_router(brain_router)
    dp.include_router(sessions_router)
    dp.include_router(tasks_router)
    dp.include_router(dev_router)
    dp.include_router(pm_router)
    dp.include_router(enterprise_router)
    # NL catch-all last
    dp.include_router(ai_router)


__all__ = ["register_all_routers"]
