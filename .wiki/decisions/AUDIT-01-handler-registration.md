# AUDIT-01: Handler Registration Report

## Summary

**Status: 1 MISSING ROUTER FOUND**

`admin_handlers.py` has `router = Router()` but is **NOT registered** in `handlers/__init__.py _ROUTER_ORDER`.

---

## Subtask 1 — Full Router Scan (40 files)

| File | Has Router | Router Name | In _ROUTER_ORDER | Commands/Decorators |
|------|-----------|-------------|------------------|---------------------|
| admin_handlers.py | ✅ | `router` | ❌ **MISSING** | `Command("budget")`, `Command("soul")` |
| ai.py | ✅ | `router` | ✅ ai.router (last) | `Command("think")`, `Command("run")`, `Command("agent")`, `Command("swarm")`, `Command("owl")`, `Command("predict")`, `Command("code_exec")`, `Command("ag2")`, `Command("swarm_viz")`, `Command("agents_viz")`, `Command("multi_execute")`, `Command("multi_plan")`, `Command("orchestrate_legacy")`, `Command("loop")`, `Command("loop_stop")`, `Command("loop_status")`, `Command("loop_pause")`, `Command("loop_resume")`, `F.text` (NL catch-all) |
| artifact.py | ✅ | `router` | ✅ artifact.router | `Command("preview")` |
| brain.py | ✅ | `router` | ✅ brain.router | `Command("briefing")`, `Command("memories")`, `Command("brain_export")`, `Command("learn")`, `Command("om_stats")`, `Command("instincts")`, `Command("forget")`, `Command("self_review")` |
| business_handler.py | ✅ | `router` | ✅ business_handler.router | `Command("db")`, `Command("site_health")`, `Command("bookings")`, `Command("db_schema")`, `Command("biz")` |
| communications.py | ✅ | `router` | ✅ communications.router | `Command("emails")`, `Command("inbox")`, `Command("calendar")` |
| computer.py | ✅ | `router` | ✅ computer.router | `Command("do")`, `Command("do_local")`, `Command("screen")`, `Command("open")`, `Command("click")`, `Command("type")`, `Command("key")`, `Command("cmd")`, `Command("install")`, `Command("upgrade_git")`, `Command("oi")`, `F.text` (×3), `F.data.startswith("fb:")`, `F.data == "screen:analyze"`, `F.data == "screen:do"` |
| debate_handlers.py | ✅ | `router` | ✅ debate_handlers.router | `Command("debate")`, `Command("opinion")` |
| dev.py | ✅ | `router` | ✅ dev.router | `Command("scaffold")`, `Command("build")`, `Command("vuln_scan")`, `Command("review")`, `Command("security_review")`, `Command("opencode")` |
| e2e.py | ✅ | `router` | ✅ e2e.router | `Command("e2etest")`, `Command("e2eplan")`, `Command("dbquery")`, `Command("dbhealth")`, `Command("dbtables")` |
| ecc_compat.py | ✅ | `router` | ✅ ecc_compat.router | `Command("harness_audit")`, `Command("model_route")`, `Command("quality_gate")`, `Command("verify")`, `Command("plan")`, `Command("checkpoint")`, `Command("save_session")`, `Command("resume_session")`, `Command("instinct_status")`, `Command("instinct_export")`, `Command("instinct_import")`, `Command("loop_start")`, `Command("code_review")`, `Command("python_review")`, `Command("refactor_clean")`, `Command("test_coverage")`, `Command("tdd")`, `Command("prompt_optimize")`, `Command("learn_eval")`, `Command("update_docs")`, `Command("update_codemaps")`, `Command("skill_create")`, `Command("eval")`, `Command("build_fix")`, `Command("projects")`, `Command("setup_pm")`, `Command("claw")`, `Command("multi_backend")`, `Command("multi_frontend")`, `Command("multi_workflow")`, `Command("e2e")`, `Command("pm2")`, `Command("go_build")`, `Command("go_test")`, `Command("go_review")`, `Command("gradle_build")`, `Command("kotlin_build")`, `Command("kotlin_test")`, `Command("kotlin_review")`, `Command("promote")`, `Command("evolve")`, `Command("aside")` |
| enterprise.py | ✅ | `router` | ✅ enterprise.router | `Command("budget")`, `Command("routing_stats")`, `Command("security_stats")`, `Command("audit_summary")` |
| github_intel_handler.py | ✅ | `router` | ✅ github_intel_handler.router | `Command("github_intel")`, `Command("eval_repo")`, `Command("upgrade_from")` |
| inline.py | ✅ | `router` | ✅ inline.router | `InlineQueryHandler` |
| legion_extras.py | ✅ | `router` | ✅ legion_extras.router | `Command("jarvis")`, `Command("simulate")`, `Command("screenpipe_status")` |
| media_tools.py | ✅ | `router` | ✅ media_tools.router | `Command("imagine")`, `Command("genimage")`, `Command("draw")`, `Command("search")`, `Command("websearch")`, `Command("google")`, `Command("speak")`, `Command("tts")`, `Command("voice_gen")`, `Command("say")`, `Command("mcp_status")`, `Command("mm_status")`, `F.photo`, `F.video` |
| memory_commands.py | ✅ | `router` | ✅ memory_commands.router | `Command("memory")`, `Command("remember")`, `Command("recall")`, `Command("emotion")`, `Command("opinions")`, `Command("forget")`, `Command("profile")`, `Command("teach")` |
| message_handler.py | ❌ | — (helper only) | N/A | — |
| nihongo_handler.py | ❌ | — (uses python-telegram-bot Update/ContextTypes, not aiogram) | N/A | — |
| orchestrate.py | ✅ | `router` | ✅ orchestrate.router | `Command("orchestrate")`, `Command("orchestrate_cancel")`, `CallbackQueryHandler` (lambda c.data.startswith("plan_")) |
| overnight_handler.py | ✅ | `router` | ✅ overnight_handler.router | `Command("overnight")`, `Command("overnight_status")`, `Command("overnight_cancel")`, `Command("overnight_pause")`, `Command("overnight_resume")`, `Command("overnight_jobs")`, `Command("dashboard")`, `Command("dashboard_png")` |
| persona_handler.py | ✅ | `router` | ✅ persona_handler.router | `Command("persona")`, `Command("mood")`, `Command("persona_reset")`, `Command("persona_note")` |
| pm.py | ✅ | `router` | ✅ pm.router | `Command("task_from")`, `Command("tasks_due")`, `Command("task_done")`, `Command("delegate")`, `Command("post")`, `Command("brand_check")`, `Command("email")` |
| research.py | ✅ | `router` | ✅ research.router | `Command("scrape")`, `Command("research")`, `Command("paper")`, `Command("ask_paper")`, `Command("workernet_papers")` |
| runbook_handler.py | ✅ | `router` | ✅ runbook_handler.router | `Command("runbook")` |
| session_handler.py | ✅ | `router` | ✅ session_handler.router | `Command("task")`, `Command("task_done")`, `Command("task_sessions")`, `Command("semantic_set")`, `Command("semantic_get")` |
| sessions.py | ✅ | `router` | ✅ sessions.router | `Command("save")`, `Command("resume")`, `Command("legion_sessions")`, `Command("audit")` |
| shared.py | ❌ | — (utility module) | N/A | — |
| skills.py | ✅ | `router` | ✅ skills.router | `Command("skills")`, `Command("skill")`, `Command("skill_reload")` |
| streaming.py | ❌ | — (helper only) | N/A | — |
| swarm_handler.py | ❌ | — (helper only) | N/A | — |
| system.py | ✅ | `router` | ✅ system.router | `Command("start")`, `Command("visualize")`, `Command("viz")`, `Command("status")`, `Command("stats")`, `Command("gpu")`, `Command("keys")`, `Command("models")`, `Command("metrics")`, `Command("resources")`, `Command("capability_stats")`, `Command("cap_stats")`, `Command("benchmark")`, `Command("redteam")`, `Command("capability_redteam")`, `F.text` (×5), `CallbackQueryHandler` (lambda c.data.startswith("ui:")) |
| tasks.py | ✅ | `router` | ✅ tasks.router | `Command("monitor")`, `Command("schedule")`, `Command("tasks")`, `Command("cancel")`, `Command("alert")`, `Command("watch_training")`, `Command("n8n")` |
| upgrade.py | ✅ | `router` | ✅ upgrade.router | `Command("upgrade")`, `Command("upgrade_status")`, `Command("upgrade_history")` |
| voice.py | ✅ | `router` | ✅ voice.router | `Command("voice_on")`, `Command("voice_off")`, `Command("voice_status")`, `Command("voice_toggle")`, `Command("vcsearch")`, `F.voice`, `F.audio` |
| whatsapp_handler.py | ✅ | `router` | ✅ whatsapp_handler.router | `Command("wa")`, `Command("wa_reply")`, `Command("wa_qr")`, `Command("wa_status")` |
| wiki.py | ✅ | `router` | ✅ wiki_router | `Command("wiki_audit")`, `Command("wiki_flush")`, `Command("wiki_restore")`, `Command("wiki_scan")`, `Command("wiki_stats")` |
| wiki_handler.py | ✅ | `router` | ✅ wiki_handler.router | `Command("wiki")`, `Command("wiki_ingest")`, `Command("wiki_lint")` |

---

## Subtask 2 — Diff Against _ROUTER_ORDER

### Routers in _ROUTER_ORDER (32 total):
ai, artifact, brain, communications, debate_handlers, legion_extras, business_handler, wiki_handler, runbook_handler, computer, ecc_compat, dev, e2e, enterprise, github_intel_handler, inline, media_tools, memory_commands, orchestrate, overnight_handler, persona_handler, pm, research, session_handler, sessions, skills, system, tasks, upgrade, voice, whatsapp_handler, wiki_handler, wiki_router, ai.router

### Missing Routers:
**`admin_handlers.router`** — NOT in _ROUTER_ORDER

---

## Subtask 3 — Handler Type Mapping for Missing Router

### admin_handlers.py
| Decorator | Function | Type |
|-----------|----------|------|
| `@router.message(Command("budget"))` | `cmd_budget` | `CommandHandler("budget", cmd_budget)` |
| `@router.message(Command("soul"))` | `cmd_soul` | `CommandHandler("soul", cmd_soul)` |

**Handler Type**: Command-based (`CommandHandler`)
**Priority**: Should be placed near enterprise.router (also has /budget) — but since admin_handlers.router is owner-only with `_require_owner`, placement is less critical for routing order.

---

## Subtask 4 — Exact Fix Required

### Import Statement (handlers/__init__.py line ~13-45)
Add `admin_handlers` to the import block:
```python
from handlers import (
    ai,
    admin_handlers,   # ← ADD THIS
    artifact,
    ...
)
```

### _ROUTER_ORDER Registration
Add `admin_handlers.router` BEFORE `ai.router` (line ~82):
```python
_ROUTER_ORDER = [
    ...
    legion_extras.router,
    wiki_router,
    admin_handlers.router,  # ← ADD BEFORE ai.router
    ai.router,  # /run /think /agent /swarm + NL catch-all (LAST)
]
```

---

## Subtask 5 — Proposed Position in _ROUTER_ORDER

Given:
- `admin_handlers.router` handles `/budget` and `/soul` (owner-only admin commands)
- `enterprise.router` also handles `/budget` (but as a dashboard view)
- NL catch-all (`ai.router`) MUST stay last
- `overnight_handler.router` must be before `ai.router` to avoid interception

**Recommended position**: Before `legion_extras.router` (line ~80) or immediately before `wiki_router` (line ~81).

Rationale: admin_handlers commands are owner-only (not commonly invoked), so exact position is less critical. Placed near end before NL catch-all.

---

## Current _ROUTER_ORDER (Correct with fix applied):

```python
_ROUTER_ORDER = [
    computer.router,           # /do /screen /click /type /key /cmd /install
    communications.router,    # /emails /inbox /calendar
    runbook_handler.router,   # /runbook
    business_handler.router,   # /db /site_health /bookings /db_schema
    github_intel_handler.router,  # /github_intel /eval_repo /upgrade_from
    whatsapp_handler.router,   # /wa /wa_reply /wa_qr /wa_status
    system.router,            # /start /stats /keys /models /git /maintenance /gpu
    research.router,          # /scrape /research /paper /ask_paper
    memory_commands.router,    # /memory /remember /recall /emotion /opinions /forget /profile /teach
    wiki_handler.router,       # /wiki /wiki_ingest /wiki_lint
    brain.router,             # /memories /briefing /learn /instincts
    session_handler.router,    # /task /task_done /task_sessions /semantic_set /semantic_get
    sessions.router,          # /save /resume /sessions /audit
    tasks.router,             # /monitor /schedule /tasks /cancel
    dev.router,               # /scaffold /build /vuln_scan /review
    pm.router,                # /task_from /tasks_due /post /email
    enterprise.router,        # /budget /routing_stats /security_stats /audit_summary
    artifact.router,           # /preview
    upgrade.router,           # /upgrade /upgrade_status /upgrade_history
    debate_handlers.router,    # /debate /opinion
    overnight_handler.router,  # /overnight /dashboard /overnight_*
    voice.router,             # F.voice + F.audio + /voice_on /voice_off /voice_status /voice_toggle
    media_tools.router,        # /imagine /search /speak + F.photo (MiniMax media tools)
    inline.router,            # inline_query
    skills.router,            # /skills /skill /skill_reload
    persona_handler.router,    # /persona /mood /persona_reset /persona_note
    ecc_compat.router,         # /harness_audit /model_route /quality_gate /verify /plan /checkpoint
    e2e.router,               # /e2etest /e2eplan /dbquery /dbhealth /dbtables
    orchestrate.router,        # /orchestrate /orchestrate_cancel
    legion_extras.router,       # /simulate /screenpipe_status /mcp_status /voice_room /websearch /quickscrape
    wiki_router,               # /wiki_audit /wiki_flush /wiki_restore /wiki_scan /wiki_stats
    admin_handlers.router,      # /budget /soul ← ADD THIS (owner-only)
    ai.router,                 # /run /think /agent /swarm + NL catch-all (LAST)
]
```

---

## Files to Modify

1. **`handlers/__init__.py`**
   - Add `admin_handlers` to import block (line ~13)
   - Add `admin_handlers.router` to `_ROUTER_ORDER` before `ai.router` (line ~82)
