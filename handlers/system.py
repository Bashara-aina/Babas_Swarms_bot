"""System handlers: /start /stats /keys /models /git /maintenance /gpu /thread /threads /metrics."""
from __future__ import annotations

import asyncio
import time

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

import computer_agent
import router as agents
from llm_client import run_shell_command, verify_api_keys
from .shared import (
    _key_status,
    _keep_typing,
    _start_time,
    is_allowed,
    main_keyboard,
    send_chunked,
    _user_thread,
)
import handlers.shared as _shared

router = Router()


# ── /start ────────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status = verify_api_keys()
    active = sum(1 for v in status.values() if v)
    uptime = int(time.time() - _start_time)
    h, m = uptime // 3600, (uptime % 3600) // 60

    text = (
        f"yo Bas — Legion v4 up — {h}h {m}m | {active}/6 keys\n\n"
        "<b>computer control</b>\n"
        "  <code>/do</code> <code>/screen</code> <code>/open</code> <code>/click</code> <code>/type</code> <code>/key</code> <code>/cmd</code>\n\n"
        "<b>AI agents</b>\n"
        "  <code>/run</code>  <code>/think</code>  <code>/swarm</code>  <code>/agent</code>\n\n"
        "<b>research</b>\n"
        "  <code>/paper</code>  <code>/ask_paper</code>  <code>/workernet_papers</code>\n"
        "  <code>/scrape</code>  <code>/research</code>\n\n"
        "<b>second brain</b>\n"
        "  <code>/remember</code>  <code>/recall</code>  <code>/memories</code>  <code>/briefing</code>\n\n"
        "<b>dev tools</b>\n"
        "  <code>/scaffold</code>  <code>/build</code>  <code>/gpu</code>  <code>/vuln_scan</code>\n\n"
        "<b>tasks</b>\n"
        "  <code>/task_from</code>  <code>/tasks_due</code>  <code>/task_done</code>\n\n"
        "<b>content</b>\n"
        "  <code>/post</code>  <code>/brand_check</code>  <code>/delegate</code>\n\n"
        "<b>orchestration</b>\n"
        "  <code>/orchestrate</code>  <code>/multi_execute</code>  <code>/multi_plan</code>\n"
        "  <code>/loop</code>  <code>/loop_stop</code>\n\n"
        "<b>enterprise</b>\n"
        "  <code>/budget</code>  <code>/routing_stats</code>  <code>/audit_summary</code>  <code>/security_stats</code>\n\n"
        "<b>system</b>\n"
        "  <code>/stats</code>  <code>/git</code>  <code>/models</code>  <code>/keys</code>  <code>/maintenance</code>\n\n"
        "or just type naturally — i'll figure it out."
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=main_keyboard())


# ── /stats ────────────────────────────────────────────────────────────────────
@router.message(Command("stats"))
async def cmd_stats(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("pulling stats…")
    cpu, mem, gpu, disk, display = await asyncio.gather(
        run_shell_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", timeout=5),
        run_shell_command("free -h | grep Mem", timeout=5),
        run_shell_command(
            "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu"
            " --format=csv,noheader,nounits 2>/dev/null || echo 'No GPU'",
            timeout=5,
        ),
        run_shell_command("df -h / | tail -1", timeout=5),
        computer_agent.detect_display(),
    )
    uptime = int(time.time() - _start_time)
    text = (
        f"<b>📊 system</b>\n\n"
        f"⏱ bot up: {uptime // 3600}h {(uptime % 3600) // 60}m\n"
        f"🖥 cpu: <code>{cpu.strip()}%</code>\n"
        f"🖥 display: <code>{display}</code>\n"
        f"💾 mem:\n<pre>{mem.strip()}</pre>\n"
        f"🎮 gpu:\n<pre>{gpu.strip()}</pre>\n"
        f"💿 disk:\n<pre>{disk.strip()}</pre>"
    )
    await status_msg.edit_text(text, parse_mode="HTML")


# ── /keys ─────────────────────────────────────────────────────────────────────
@router.message(Command("keys"))
async def cmd_keys(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(_key_status(), parse_mode="HTML")


# ── /models ───────────────────────────────────────────────────────────────────
@router.message(Command("models"))
async def cmd_models(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(
        f"{agents.list_agents()}\n\n{_key_status()}",
        parse_mode="HTML",
    )


# ── /git ──────────────────────────────────────────────────────────────────────
@router.message(Command("git"))
async def cmd_git(msg: Message) -> None:
    if not is_allowed(msg):
        return
    output = await run_shell_command(
        "cd ~/swarm-bot && git status --short && echo '---' && git log --oneline -5",
        timeout=10,
    )
    await msg.answer(f"<b>📁 git</b>\n\n<pre>{output}</pre>", parse_mode="HTML")


# ── /thread / /threads ────────────────────────────────────────────────────────
@router.message(Command("thread"))
async def cmd_thread(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/thread").strip()
    if not name:
        current = _user_thread.get(msg.from_user.id, "none")
        await msg.answer(
            f"current thread: <b>{current}</b>\nuse: <code>/thread &lt;name&gt;</code>",
            parse_mode="HTML",
        )
        return
    _user_thread[msg.from_user.id] = name
    await msg.answer(f"📌 thread: <b>{name}</b>", parse_mode="HTML")


@router.message(Command("threads"))
async def cmd_threads(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(agents.list_threads(), parse_mode="HTML")


# ── /maintenance — full system health check ───────────────────────────────────
@router.message(Command("maintenance"))
async def cmd_maintenance(msg: Message) -> None:
    if not is_allowed(msg):
        return

    status_msg = await msg.answer("🏥 running full system health check…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from tools.system_maintenance import full_maintenance_check
        result = await full_maintenance_check()
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="maintenance")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(
            f"maintenance check failed: <code>{e}</code>",
            parse_mode="HTML",
        )


# ── /gpu — enhanced GPU status ────────────────────────────────────────────────
@router.message(Command("gpu"))
async def cmd_gpu(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.devops import check_gpu_health
        result = await check_gpu_health()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"GPU error: <code>{e}</code>", parse_mode="HTML")


# ── /metrics — Performance dashboard ─────────────────────────────────────────
@router.message(Command("metrics"))
async def cmd_metrics(msg: Message) -> None:
    """Show performance and cost metrics dashboard."""
    if not is_allowed(msg):
        return
    if not _shared._cost_metrics:
        await msg.answer("Cost metrics collector not initialized.")
        return
    text = _shared._cost_metrics.format_dashboard_html()
    await msg.answer(text, parse_mode="HTML")


# ── Keyboard button shortcuts ─────────────────────────────────────────────────
@router.message(F.text == "⚙️ Status")
async def kbd_status(msg: Message) -> None:
    if is_allowed(msg):
        await cmd_stats(msg)


