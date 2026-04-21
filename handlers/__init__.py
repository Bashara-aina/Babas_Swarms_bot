"""Register all aiogram Routers with the Dispatcher.

Router order matters:
- More-specific command routers before general ones.
- overnight_handler before ai to avoid interception.
- ai.router MUST be last (NL catch-all via F.text).
- voice.router handles F.voice + F.audio + /voice_on/off/status/toggle.
  voice_handler.py is intentionally NOT imported here (merged into voice.py).
"""

from aiogram import Dispatcher

from handlers import (
    ai,
    admin_handlers,
    artifact,
    brain,
    communications,
    debate_handlers,
    gstack,
    harvest_review,
    hermes,
    legion_extras,
    legiona_tools,
    business_handler,
    wiki_handler,
    runbook_handler,
    computer,
    ecc_compat,
    dev,
    draft,
    e2e,
    enterprise,
    github_intel_handler,
    inline,
    media_tools,
    memory_commands,
    orchestrate,
    overnight_handler,
    persona_handler,
    plandex_commands,
    pm,
    research,
    session_handler,
    sessions,
    skills,
    swe_commands,
    system,
    tasks,
    threads_mode,
    upgrade,
    voice,
    whatsapp_handler,
)
from handlers.wiki import router as wiki_router

# ai.router must be last (NL catch-all).
# overnight_handler before ai to avoid being intercepted.
_ROUTER_ORDER = [
    legiona_tools.router,  # /logs /ps /kill /sys /ls /find /grep /read /write /disk /window /screen /clipboard /type /key /service /tree
    computer.router,  # /do /screen /click /type /key /cmd /install
    plandex_commands.router,  # /code /diff /apply /abort
    swe_commands.router,  # /fix /fix_dry
    communications.router,  # /emails /inbox /calendar
    runbook_handler.router,  # /runbook
    business_handler.router,  # /db /site_health /bookings /db_schema
    github_intel_handler.router,  # /github_intel /eval_repo /upgrade_from
    whatsapp_handler.router,  # /wa /wa_reply /wa_qr /wa_status
    system.router,  # /start /stats /keys /models /git /maintenance /gpu
    hermes.router,  # /hermes /hermes-search /hermes-delegate /hermes-tools /hermes-smoke
    research.router,  # /scrape /research /paper /ask_paper
    draft.router,  # /draft
    memory_commands.router,  # /memory /remember /recall /emotion /opinions /forget /profile /teach
    wiki_handler.router,  # /wiki /wiki_ingest /wiki_lint
    brain.router,  # /memories /briefing /learn /instincts
    session_handler.router,  # /task /task_done /task_sessions /semantic_set /semantic_get
    sessions.router,  # /save /resume /sessions /audit
    tasks.router,  # /monitor /schedule /tasks /cancel
    threads_mode.router,  # /threads_mode on|off|toggle|status
    dev.router,  # /scaffold /build /vuln_scan /review
    pm.router,  # /task_from /tasks_due /post /email
    enterprise.router,  # /budget /routing_stats /security_stats /audit_summary
    artifact.router,  # /preview
    upgrade.router,  # /upgrade /upgrade_status /upgrade_history
    debate_handlers.router,  # /debate /opinion
    overnight_handler.router,  # /overnight /dashboard /overnight_*
    voice.router,  # F.voice + F.audio + /voice_on /voice_off /voice_status /voice_toggle
    media_tools.router,  # /imagine /search /speak + F.photo (MiniMax media tools)
    inline.router,  # inline_query
    skills.router,  # /skills /skill /skill_reload
    gstack.router,  # /review /ship /officehours /codex /investigate /qa /careful /planreview
    persona_handler.router,  # /persona /mood /persona_reset /persona_note
    ecc_compat.router,  # /harness_audit /model_route /quality_gate /verify /plan /checkpoint
    e2e.router,  # /e2etest /e2eplan /dbquery /dbhealth /dbtables
    orchestrate.router,  # /orchestrate /orchestrate_cancel
    legion_extras.router,  # /simulate /screenpipe_status /mcp_status /voice_room /websearch /quickscrape
    wiki_router,  # /wiki_audit /wiki_flush /wiki_restore /wiki_scan /wiki_stats
    harvest_review.router,  # /harvest_review
    admin_handlers.router,  # /budget /soul (owner-only)
    ai.router,  # /run /think /agent /swarm + NL catch-all (LAST)
]


def register_all_routers(dp: Dispatcher) -> None:
    """Include all routers in order. NL catch-all (ai.router) must be last."""
    for r in _ROUTER_ORDER:
        dp.include_router(r)
