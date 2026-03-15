"""Register all aiogram Routers with the Dispatcher."""
from aiogram import Dispatcher

from handlers import (
    ai,
    artifact,
    brain,
    computer,
    ecc_compat,
    dev,
    e2e,
    enterprise,
    inline,
    orchestrate,
    overnight_handler,
    pm,
    research,
    sessions,
    skills,
    system,
    tasks,
    voice,
)

# ai.router must be last (NL catch-all).
# overnight_handler before ai to avoid being intercepted.
_ROUTER_ORDER = [
    computer.router,          # /do /screen /click /type /key /cmd /install
    system.router,            # /start /stats /keys /models /git /maintenance /gpu
    research.router,          # /scrape /research /paper /ask_paper
    brain.router,             # /remember /recall /memories /briefing
    sessions.router,          # /save /resume /sessions /audit
    tasks.router,             # /monitor /schedule /tasks /cancel
    dev.router,               # /scaffold /build /vuln_scan /review
    pm.router,                # /task_from /tasks_due /post /email
    enterprise.router,        # /budget /routing_stats /security_stats /audit_summary
    artifact.router,          # /preview
    overnight_handler.router, # /overnight /dashboard /overnight_*
    voice.router,             # F.voice + F.audio
    inline.router,            # inline_query
    skills.router,            # /skills /skill /skill_reload
    ecc_compat.router,        # /harness_audit /model_route /quality_gate /verify /plan /checkpoint
    e2e.router,               # /e2etest /e2eplan /dbquery /dbhealth /dbtables
    orchestrate.router,       # /orchestrate /orchestrate_cancel
    ai.router,                # /run /think /agent /swarm + NL catch-all (LAST)
]


def register_all_routers(dp: Dispatcher) -> None:
    """Include all routers in order. NL catch-all (ai.router) must be last."""
    for r in _ROUTER_ORDER:
        dp.include_router(r)
