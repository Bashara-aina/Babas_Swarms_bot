"""AI agent handlers: /run /think /agent /swarm /multi_execute /orchestrate /multi_plan /loop* + NL."""
from __future__ import annotations

import asyncio
import html as html_mod

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

import router as agents
from .shared import (
    _user_thread,
    _keep_typing,
    _execute_chat,
    _run_agent_loop,
    is_allowed,
    send_chunked,
)
import handlers.shared as _shared

router = Router()


# ── /think ────────────────────────────────────────────────────────────────────
@router.message(Command("think"))
async def cmd_think(msg: Message) -> None:
    if not is_allowed(msg):
        return
    query = (msg.text or "").removeprefix("/think").strip()
    if not query:
        await msg.answer(
            "usage: <code>/think &lt;hard question&gt;</code>\n"
            "forces QwQ-32b with visible reasoning chain",
            parse_mode="HTML",
        )
        return
    await _execute_chat(msg, query, forced_agent="debug", show_thinking=True)


# ── /run ──────────────────────────────────────────────────────────────────────
@router.message(Command("run"))
async def cmd_run(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/run").strip()
    if not task:
        await msg.answer(
            "usage: <code>/run &lt;task&gt;</code>  — LLM chat only, no computer access\n"
            "for full computer control use <code>/do &lt;task&gt;</code>",
            parse_mode="HTML",
        )
        return
    await _execute_chat(msg, task)


# ── /agent ────────────────────────────────────────────────────────────────────
@router.message(Command("agent"))
async def cmd_agent(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split(maxsplit=2)
    if len(parts) < 3:
        valid = ", ".join(agents.AGENT_MODELS.keys())
        await msg.answer(
            f"usage: <code>/agent &lt;key&gt; &lt;task&gt;</code>\nkeys: <code>{valid}</code>",
            parse_mode="HTML",
        )
        return
    key, task = parts[1].lower(), parts[2]
    if key not in agents.AGENT_MODELS:
        await msg.answer(f"unknown agent: <code>{key}</code>", parse_mode="HTML")
        return
    await _execute_chat(msg, task, forced_agent=key)


# ── /swarm — multi-agent team execution ──────────────────────────────────────
@router.message(Command("swarm"))
async def cmd_swarm(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/swarm").strip()
    if not task:
        await msg.answer(
            "usage: <code>/swarm &lt;complex task&gt;</code>\n\n"
            "decomposes task and runs specialist agents in parallel:\n"
            "strategist, developer, researcher, marketer, analyst, devops, pm\n\n"
            "examples:\n"
            "<code>/swarm analyze IKEA ASM codebase and suggest 3 improvements</code>\n"
            "<code>/swarm build a landing page with API and tests</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("strategist decomposing task...")
    typing_task = asyncio.create_task(_keep_typing(msg))

    async def on_progress(step_text: str) -> None:
        try:
            await status_msg.edit_text(step_text, parse_mode="HTML")
        except Exception:
            pass

    try:
        from tools.orchestrator import decompose_task, execute_parallel, synthesize_results
        subtasks = await decompose_task(task)
        agent_list = "\n".join(f"  [{s['agent']}] {s['task'][:60]}..." for s in subtasks)
        await status_msg.edit_text(
            f"running {len(subtasks)} agents:\n{agent_list}",
            parse_mode="HTML",
        )

        results = await execute_parallel(subtasks, progress_cb=on_progress)
        final = await synthesize_results(task, results, subtasks)

        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, final, model_used="swarm/multi-agent")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"swarm error: <code>{html_mod.escape(str(e)[:400])}</code>", parse_mode="HTML")


# ── /multi_execute — Same task, multiple agents ──────────────────────────────
@router.message(Command("multi_execute"))
async def cmd_multi_execute(msg: Message) -> None:
    """Execute same task with multiple agents and compare results."""
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/multi_execute").strip()
    if not task:
        await msg.answer(
            "<b>usage:</b> <code>/multi_execute &lt;task&gt;</code>\n\n"
            "Runs the same task with 3 agents and compares results.\n"
            "Optionally specify agents: <code>/multi_execute --agents=coding,debug,analyst &lt;task&gt;</code>",
            parse_mode="HTML",
        )
        return

    # FIX #3: Safe --agents= parser — guard against ValueError when no space follows flag value
    agent_keys = ["coding", "architect", "analyst"]
    if "--agents=" in task:
        parts = task.split("--agents=", 1)
        remainder = parts[1]
        if " " in remainder:
            agent_str, task = remainder.split(" ", 1)
            task = task.strip()
        else:
            # Flag present but no task after agent list
            agent_str = remainder
            task = ""
        agent_keys = [a.strip() for a in agent_str.split(",") if a.strip()]

    if not task:
        await msg.answer(
            "\u26a0\ufe0f No task provided after <code>--agents=</code>.\n"
            "Usage: <code>/multi_execute --agents=coding,debug &lt;task&gt;</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(f"\u26a1 Running task with {len(agent_keys)} agents\u2026")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        # Use _shared module references (not local copies) so enterprise objects are live
        if _shared._chief_of_staff:
            from swarms_bot.orchestrator.chief_of_staff import Task as STask
            stask = STask.create(
                user_id=msg.from_user.id,
                chat_id=msg.chat.id,
                description=task,
            )
            responses = await _shared._chief_of_staff.route_multi(stask, agent_keys)

            lines = ["<b>Multi-Execute Comparison</b>\n"]
            for resp in responses:
                icon = "\u2705" if resp.success else "\u274c"
                model = resp.metadata.get("model", "unknown")
                lines.append(
                    f"\n{icon} <b>{resp.agent_name}</b> ({model}, {resp.execution_time_ms}ms):\n"
                    f"{resp.result[:1000] if resp.result else 'No result'}\n"
                )
            full = "\n".join(lines)

            if _shared._audit_logger:
                await _shared._audit_logger.log(
                    user_id=msg.from_user.id,
                    agent_name="multi_execute",
                    action_type="multi_execute",
                    success=any(r.success for r in responses),
                    metadata={"agents": agent_keys},
                )
        else:
            from llm_client import chat
            results = await asyncio.gather(
                *(chat(task, agent_key=a) for a in agent_keys),
                return_exceptions=True,
            )
            lines = ["<b>Multi-Execute Comparison</b>\n"]
            for agent_key, res in zip(agent_keys, results):
                if isinstance(res, Exception):
                    lines.append(f"\n\u274c <b>{agent_key}</b>: {html_mod.escape(str(res)[:200])}\n")
                else:
                    text_r, model = res
                    lines.append(f"\n\u2705 <b>{agent_key}</b> ({model}):\n{text_r[:1000]}\n")
            full = "\n".join(lines)

        await send_chunked(msg, full)
        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        await status_msg.edit_text(
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )
    finally:
        typing_task.cancel()


# ── /multi_plan ───────────────────────────────────────────────────────────────
@router.message(Command("multi_plan"))
async def cmd_multi_plan(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/multi_plan").strip()
    if not task:
        await msg.answer("usage: <code>/multi_plan &lt;task&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer("\U0001f9e0 generating 3 approaches\u2026")
    try:
        from llm_client import chat, chunk_output
        agent_keys = ["architect", "coding", "analyst"]
        results = await asyncio.gather(
            *(chat(task, agent_key=a) for a in agent_keys),
            return_exceptions=True,
        )
        lines = ["<b>Multi-Plan Comparison</b>\n"]
        for agent_key, res in zip(agent_keys, results):
            if isinstance(res, Exception):
                lines.append(f"\n<b>\u26a0\ufe0f {agent_key}</b>: error — {html_mod.escape(str(res)[:200])}\n")
            else:
                text_r, model = res
                lines.append(f"\n<b>\U0001f4cb {agent_key}</b> ({model}):\n{text_r[:1000]}\n")
        full = "\n".join(lines)

        # FIX #10: Use chunk_output() to avoid cutting mid-HTML tag (was slicing at [:4000] directly)
        chunks = chunk_output(full, max_length=4000)
        await status_msg.edit_text(chunks[0], parse_mode="HTML")
        for chunk in chunks[1:]:
            await msg.answer(chunk, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── /orchestrate ──────────────────────────────────────────────────────────────
@router.message(Command("orchestrate"))
async def cmd_orchestrate(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/orchestrate").strip()
    if not task:
        await msg.answer("usage: <code>/orchestrate &lt;complex task&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer("\U0001f3af decomposing task\u2026")

    # FIX #1: progress_cb was a bare lambda (never awaited) — replaced with proper async def
    async def _progress(s: str) -> None:
        try:
            await status_msg.edit_text(f"\u23f3 {s}", parse_mode="HTML")
        except Exception:
            pass

    try:
        from llm_client import chunk_output
        from tools.orchestrate_engine import orchestrate_task
        result = await orchestrate_task(task, progress_cb=_progress)

        # FIX #10: Use chunk_output() to avoid cutting mid-HTML tag
        chunks = chunk_output(result, max_length=4000)
        await status_msg.edit_text(chunks[0], parse_mode="HTML")
        for chunk in chunks[1:]:
            await msg.answer(chunk, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── /loop — Autonomous plan-execute loop ─────────────────────────────────────
@router.message(Command("loop"))
async def cmd_loop(msg: Message) -> None:
    """Autonomous plan-execute loop with safety bounds."""
    if not is_allowed(msg):
        return
    goal = (msg.text or "").removeprefix("/loop").strip()
    if not goal:
        await msg.answer(
            "<b>usage:</b> <code>/loop &lt;goal&gt;</code>\n\n"
            "Runs an autonomous plan\u2192execute loop until the goal is done.\n"
            "Safety bounds: 25 iterations, $0.50 cost ceiling, 30min timeout.\n"
            "Stop anytime with /loop_stop",
            parse_mode="HTML",
        )
        return

    from tools.autonomous_loop import get_active_loop, run_autonomous_loop, LoopConfig

    if get_active_loop(msg.from_user.id):
        await msg.answer(
            "A loop is already running. Use /loop_stop to cancel it first.",
        )
        return

    thread_id = _user_thread.get(msg.from_user.id)

    # FIX #8: msg.bot can be None in aiogram 3.x — guard before use
    _bot = msg.bot
    if not _bot:
        await msg.answer("Internal error: bot context unavailable.")
        return

    await msg.answer(
        f"<b>\U0001f504 Loop started</b>\n"
        f"Goal: <code>{html_mod.escape(goal[:200])}</code>\n\n"
        f"Bounds: 25 iters | $0.50 cost cap | 30min timeout\n"
        f"Progress updates every 5 iterations.\n"
        f"Stop anytime: /loop_stop",
        parse_mode="HTML",
    )

    async def notify(text: str) -> None:
        try:
            await _bot.send_message(msg.chat.id, text, parse_mode="HTML")
        except Exception:
            try:
                await _bot.send_message(msg.chat.id, html_mod.escape(text), parse_mode="HTML")
            except Exception:
                await _bot.send_message(msg.chat.id, text[:4000])

    asyncio.create_task(
        run_autonomous_loop(
            user_id=msg.from_user.id,
            goal=goal,
            notify_cb=notify,
            config=LoopConfig(),
            thread_id=thread_id,
        )
    )


@router.message(Command("loop_stop"))
async def cmd_loop_stop(msg: Message) -> None:
    """Kill switch for the autonomous loop."""
    if not is_allowed(msg):
        return
    from tools.autonomous_loop import stop_loop
    if stop_loop(msg.from_user.id):
        await msg.answer("Loop stop signal sent. It will halt after the current step.")
    else:
        await msg.answer("No active loop running.")


@router.message(Command("loop_status"))
async def cmd_loop_status(msg: Message) -> None:
    """Show status of the current autonomous loop."""
    if not is_allowed(msg):
        return
    from tools.autonomous_loop import get_loop_state, format_loop_status_html
    state = get_loop_state(msg.from_user.id)
    if not state:
        await msg.answer("No loop found. Start one with /loop")
        return
    await msg.answer(format_loop_status_html(state), parse_mode="HTML")


@router.message(Command("loop_pause"))
async def cmd_loop_pause(msg: Message) -> None:
    """Pause the running autonomous loop."""
    if not is_allowed(msg):
        return
    from tools.autonomous_loop import pause_loop
    if pause_loop(msg.from_user.id):
        await msg.answer("\u23f8\ufe0f Loop paused. Resume with /loop_resume")
    else:
        await msg.answer("No running loop to pause.")


@router.message(Command("loop_resume"))
async def cmd_loop_resume(msg: Message) -> None:
    """Resume a paused autonomous loop."""
    if not is_allowed(msg):
        return
    from tools.autonomous_loop import resume_loop
    if resume_loop(msg.from_user.id):
        await msg.answer("\u25b6\ufe0f Loop resumed.")
    else:
        await msg.answer("No paused loop to resume.")


# ── Keyboard button shortcuts ─────────────────────────────────────────────────
@router.message(F.text.in_({"\U0001f41b Debug", "\U0001f4bb Code"}))
async def kbd_agent_hint(msg: Message) -> None:
    if not is_allowed(msg):
        return
    key = "debug" if "Debug" in msg.text else "coding"
    await msg.answer(
        f"<b>{key}</b> mode — just type your task:",
        parse_mode="HTML",
    )


# ── Natural language catch-all (must be registered last) ─────────────────────
@router.message(F.text)
async def handle_nl(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").strip()
    if not task or task.startswith("/"):
        return

    task_lower = task.lower()

    # Check OpenClaw delegation first
    try:
        from tools.openclaw_bridge import should_delegate_to_openclaw, is_openclaw_running, delegate_to_openclaw
        if should_delegate_to_openclaw(task):
            if await is_openclaw_running():
                result = await delegate_to_openclaw(task)
                await send_chunked(msg, result, model_used="openclaw")
                return
    except Exception:
        pass

    # Detect questions (knowledge queries -> chat mode, no tools)
    question_starters = [
        "apa ", "berapa", "bagaimana", "kenapa", "mengapa", "siapa",
        "dimana", "kapan", "gimana", "apakah", "bisakah",
        "what ", "how ", "why ", "when ", "where ", "which ",
        "who ", "is it", "are there", "does ", "do you", "can you",
        "could you", "would you", "should ",
        "ada berapa", "apa saja", "apa itu", "ada apa",
    ]
    is_question = (
        task_lower.rstrip().endswith("?")
        or any(task_lower.startswith(q) for q in question_starters)
    )

    strong_computer = [
        "screenshot", "take screenshot",
        "click on", "click at", "klik pada",
        "drag", "scroll down", "scroll up",
        "open whatsapp", "buka whatsapp", "open chrome", "buka chrome",
        "open browser", "buka browser", "open firefox", "buka firefox",
        "open vscode", "buka vscode", "open terminal", "buka terminal",
        "open supabase", "open gmail", "open spotify", "open telegram",
        "launch ", "jalankan ",
        "search for", "search the web", "cari di internet",
        "browse to", "go to website", "scrape",
        "read pdf", "read excel", "extract table",
        "organize files", "baca dokumen",
        "git commit", "git push", "git pull",
        "run tests", "pytest", "format code",
        "disk space", "check services", "system cleanup",
    ]

    soft_computer = [
        "open", "buka", "show me", "check on",
        "cek langsung", "tolong cek", "lihat di",
        "tampilkan", "periksa", "cari online",
        "monitor", "research", "klik", "ketik",
    ]

    has_strong = any(kw in task_lower for kw in strong_computer)
    has_soft = any(kw in task_lower for kw in soft_computer)

    if has_strong:
        await _run_agent_loop(msg, task)
    elif is_question:
        await _execute_chat(msg, task)
    elif has_soft:
        await _run_agent_loop(msg, task)
    else:
        await _execute_chat(msg, task)
