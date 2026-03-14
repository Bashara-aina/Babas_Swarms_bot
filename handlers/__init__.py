"""Register all aiogram Routers with the Dispatcher."""
from aiogram import Dispatcher

from handlers import (
    ai,
    artifact,
    brain,
    computer,
    dev,
    enterprise,
    inline,
    pm,
    research,
    sessions,
    system,
    tasks,
    voice,
)

# ai.py must be second-to-last; inline/voice registered before NL catch-all
_ROUTER_ORDER = [
    computer.router,    # /do /screen /click /type /key /cmd /install /upgrade
    system.router,      # /start /stats /keys /models /git /maintenance /gpu
    research.router,    # /scrape /research /paper /ask_paper
    brain.router,       # /remember /recall /memories /briefing
    sessions.router,    # /save /resume /sessions /audit
    tasks.router,       # /monitor /schedule /tasks /cancel
    dev.router,         # /scaffold /build /vuln_scan /review
    pm.router,          # /task_from /tasks_due /post /email
    enterprise.router,  # /budget /routing_stats /security_stats /audit_summary
    artifact.router,    # /preview
    voice.router,       # F.voice + F.audio
    inline.router,      # inline_query
    ai.router,          # /run /think /agent /swarm /loop* + NL catch-all (LAST)
]


def register_all_routers(dp: Dispatcher) -> None:
    """Include all routers. Order matters — NL catch-all must be last."""
    for r in _ROUTER_ORDER:
        dp.include_router(r)
