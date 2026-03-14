"""
handlers/overnight_handler.py — Command handlers for overnight jobs and dashboard.

Commands:
  /overnight <goal>    — Plan + start an overnight job (LLM decomposes goal)
  /overnight_status    — Show status of current/last job
  /overnight_cancel    — Cancel running job
  /overnight_pause     — Pause running job
  /overnight_resume    — Resume paused job
  /overnight_jobs      — List all jobs this session
  /dashboard           — Live ASCII dashboard of all agents
  /dashboard_png       — PNG chart dashboard (sends as photo)
"""

from __future__ import annotations

import asyncio
import logging
import time
from io import BytesIO

from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()


def _auth(msg: Message) -> bool:
    from handlers.shared import ALLOWED_USER_ID
    return msg.from_user and msg.from_user.id == ALLOWED_USER_ID


async def _notify(bot, user_id: int, text: str) -> None:
    """Send a message to the user, chunked if needed."""
    MAX = 4000
    for i in range(0, len(text), MAX):
        try:
            await bot.send_message(user_id, text[i:i+MAX], parse_mode="HTML")
        except Exception as e:
            logger.warning("notify failed: %s", e)
        if len(text) > MAX:
            await asyncio.sleep(0.5)


# ── /overnight ─────────────────────────────────────────────────────────────────

@router.message(Command("overnight"))
async def cmd_overnight(msg: Message) -> None:
    if not _auth(msg):
        return
    goal = msg.text.removeprefix("/overnight").strip()
    if not goal:
        await msg.answer(
            "<b>🌙 Overnight Mode</b>\n\n"
            "Give me a goal to work on while you sleep:\n"
            "<code>/overnight &lt;goal&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "  /overnight research latest SOTA on video action recognition and write a comparison report\n"
            "  /overnight audit the codebase for bugs, write fixes, and draft a PR description\n"
            "  /overnight draft 5 LinkedIn posts about WorkerNet and a tweet thread\n"
            "  /overnight analyze my training logs and suggest 3 architecture improvements",
            parse_mode="HTML"
        )
        return

    status_msg = await msg.answer(
        f"🌙 Planning overnight job for: <i>{goal[:100]}</i>\n"
        f"🧠 Architect agent decomposing goal into tasks...",
        parse_mode="HTML"
    )

    try:
        from llm_client import simple_llm_call
        from tools.overnight import plan_job_with_llm, create_job, run_overnight_job, AGENT_STATUS
        from tools.dashboard import build_ascii_dashboard

        # Plan the job
        task_dicts = await plan_job_with_llm(goal, simple_llm_call)
        job_id, tasks = create_job(task_dicts)

        task_preview = "\n".join(
            f"  {i+1}. <b>[{t.agent}]</b> {t.title}"
            for i, t in enumerate(tasks)
        )
        await status_msg.edit_text(
            f"✅ <b>Plan ready</b> — Job <code>{job_id}</code>\n\n"
            f"{task_preview}\n\n"
            f"⚡ Starting execution... You can sleep now 🌙\n"
            f"I'll send updates and a summary when done.",
            parse_mode="HTML"
        )

        bot = msg.bot
        user_id = msg.from_user.id

        async def notify(text: str) -> None:
            await _notify(bot, user_id, text)

        async def update_dashboard() -> None:
            # Update the live dashboard message (edit in place)
            try:
                dash_text = build_ascii_dashboard(
                    AGENT_STATUS,
                    job_id=job_id,
                    job_tasks=tasks,
                    title="Overnight Job Dashboard",
                )
                await bot.send_message(user_id, dash_text, parse_mode="HTML")
            except Exception as e:
                logger.debug("Dashboard update error: %s", e)

        # Run overnight job in background
        asyncio.create_task(
            run_overnight_job(
                job_id=job_id,
                tasks=tasks,
                llm_call=simple_llm_call,
                notify_fn=notify,
                update_dashboard_fn=update_dashboard,
            ),
            name=f"overnight-{job_id}"
        )

    except Exception as e:
        logger.exception("overnight start error: %s", e)
        await status_msg.edit_text(f"❌ Failed to start job: <code>{e}</code>", parse_mode="HTML")


# ── /overnight_status ──────────────────────────────────────────────────────────

@router.message(Command("overnight_status"))
async def cmd_overnight_status(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import get_active_job_id, get_job_tasks, AGENT_STATUS
    from tools.dashboard import build_ascii_dashboard

    job_id = get_active_job_id()
    if not job_id:
        await msg.answer("No overnight job currently running. Start one with /overnight", parse_mode="HTML")
        return

    tasks = get_job_tasks(job_id)
    dash = build_ascii_dashboard(
        AGENT_STATUS,
        job_id=job_id,
        job_tasks=tasks,
        title="Overnight Job Status",
    )
    await msg.answer(dash, parse_mode="HTML")


# ── /overnight_cancel ─────────────────────────────────────────────────────────

@router.message(Command("overnight_cancel"))
async def cmd_overnight_cancel(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import get_active_job_id, cancel_job
    job_id = get_active_job_id()
    if not job_id:
        await msg.answer("No active overnight job to cancel.")
        return
    result = cancel_job(job_id)
    await msg.answer(result)


# ── /overnight_pause / resume ─────────────────────────────────────────────────

@router.message(Command("overnight_pause"))
async def cmd_overnight_pause(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import get_active_job_id, pause_job
    job_id = get_active_job_id()
    if not job_id:
        await msg.answer("No active job.")
        return
    await msg.answer(pause_job(job_id))


@router.message(Command("overnight_resume"))
async def cmd_overnight_resume(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import get_active_job_id, resume_job
    job_id = get_active_job_id()
    if not job_id:
        await msg.answer("No active job.")
        return
    await msg.answer(resume_job(job_id))


# ── /overnight_jobs ───────────────────────────────────────────────────────────

@router.message(Command("overnight_jobs"))
async def cmd_overnight_jobs(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import list_all_jobs
    await msg.answer(list_all_jobs(), parse_mode="HTML")


# ── /dashboard ────────────────────────────────────────────────────────────────

@router.message(Command("dashboard"))
async def cmd_dashboard(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import AGENT_STATUS, get_active_job_id, get_job_tasks
    from tools.dashboard import build_ascii_dashboard

    job_id = get_active_job_id()
    tasks  = get_job_tasks(job_id) if job_id else None
    dash   = build_ascii_dashboard(
        AGENT_STATUS,
        job_id=job_id,
        job_tasks=tasks,
        title="LegionSwarm Live Dashboard",
    )
    await msg.answer(dash, parse_mode="HTML")


# ── /dashboard_png ────────────────────────────────────────────────────────────

@router.message(Command("dashboard_png"))
async def cmd_dashboard_png(msg: Message) -> None:
    if not _auth(msg):
        return
    from tools.overnight import AGENT_STATUS, get_active_job_id, get_job_tasks
    from tools.dashboard import build_png_dashboard, build_ascii_dashboard

    thinking = await msg.answer("📊 Rendering dashboard chart...")

    job_id = get_active_job_id()
    tasks  = get_job_tasks(job_id) if job_id else None

    png_bytes = await build_png_dashboard(AGENT_STATUS, job_id=job_id, job_tasks=tasks)

    if png_bytes:
        await thinking.delete()
        caption = f"📊 LegionSwarm Dashboard — Job {job_id or 'none'}"
        await msg.answer_photo(
            photo=BufferedInputFile(png_bytes, filename="dashboard.png"),
            caption=caption,
        )
    else:
        # Fallback to ASCII if matplotlib unavailable
        dash = build_ascii_dashboard(AGENT_STATUS, job_id=job_id, job_tasks=tasks)
        await thinking.edit_text(dash, parse_mode="HTML")
