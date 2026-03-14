"""Task/scheduler handlers: /monitor /schedule /tasks /cancel /alert /watch_training."""
from __future__ import annotations

import asyncio
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import is_allowed
import handlers.shared as _shared

router = Router()


# ── /monitor — background recurring task ─────────────────────────────────────
@router.message(Command("monitor"))
async def cmd_monitor(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/monitor").strip()
    if not text:
        await msg.answer(
            "usage: <code>/monitor &lt;seconds&gt; &lt;command&gt;</code>\n\n"
            "runs a command every N seconds in the background.\n\n"
            "examples:\n"
            "<code>/monitor 60 nvidia-smi</code>\n"
            "<code>/monitor 300 df -h /</code>\n\n"
            "add alert condition with --alert:\n"
            "<code>/monitor 120 nvidia-smi --alert \"'90' in result\"</code>",
            parse_mode="HTML",
        )
        return

    alert_cond = ""
    if "--alert" in text:
        parts = text.split("--alert", 1)
        text = parts[0].strip()
        alert_cond = parts[1].strip().strip("'\"")

    words = text.split(maxsplit=1)
    if len(words) < 2:
        await msg.answer("need both interval and command", parse_mode="HTML")
        return

    try:
        interval = int(words[0])
    except ValueError:
        await msg.answer("first argument must be interval in seconds", parse_mode="HTML")
        return

    command = words[1]
    if not _shared._scheduler:
        await msg.answer("scheduler not initialized — try restarting bot")
        return

    task_id = await _shared._scheduler.add_monitor(
        description=command[:50],
        command=command,
        interval_sec=interval,
        alert_condition=alert_cond,
    )
    interval_str = f"{interval}s" if interval < 60 else f"{interval // 60}m"
    response = f"🟢 monitor started: <code>{task_id}</code>\n  ↻ <code>{command}</code> every {interval_str}"
    if alert_cond:
        response += f"\n  🔔 alert: <code>{alert_cond}</code>"
    await msg.answer(response, parse_mode="HTML")


# ── /schedule — one-time future task ─────────────────────────────────────────
@router.message(Command("schedule"))
async def cmd_schedule(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/schedule").strip()
    if not text:
        await msg.answer(
            "usage: <code>/schedule &lt;minutes&gt; &lt;command&gt;</code>\n\n"
            "runs a command once after N minutes.\n\n"
            "examples:\n"
            "<code>/schedule 30 python3 ~/train.py</code>\n"
            "<code>/schedule 5 echo 'reminder: standup meeting'</code>",
            parse_mode="HTML",
        )
        return

    words = text.split(maxsplit=1)
    if len(words) < 2:
        await msg.answer("need both delay (minutes) and command")
        return

    try:
        minutes = int(words[0])
    except ValueError:
        await msg.answer("first argument must be delay in minutes")
        return

    command = words[1]
    run_at = time.time() + (minutes * 60)
    if not _shared._scheduler:
        await msg.answer("scheduler not initialized")
        return

    task_id = await _shared._scheduler.add_scheduled(
        description=command[:50],
        command=command,
        run_at=run_at,
    )
    await msg.answer(
        f"⏰ scheduled: <code>{task_id}</code>\n"
        f"  will run in {minutes}m: <code>{command}</code>",
        parse_mode="HTML",
    )


# ── /tasks — list background tasks ──────────────────────────────────────────
@router.message(Command("tasks"))
async def cmd_tasks(msg: Message) -> None:
    if not is_allowed(msg):
        return
    if not _shared._scheduler:
        await msg.answer("scheduler not initialized")
        return
    result = await _shared._scheduler.list_tasks()
    await msg.answer(result, parse_mode="HTML")


# ── /cancel — cancel a background task ──────────────────────────────────────
@router.message(Command("cancel"))
async def cmd_cancel(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task_id = (msg.text or "").removeprefix("/cancel").strip()
    if not task_id:
        await msg.answer("usage: <code>/cancel &lt;task_id&gt;</code>", parse_mode="HTML")
        return
    if not _shared._scheduler:
        await msg.answer("scheduler not initialized")
        return
    result = await _shared._scheduler.cancel(task_id)
    await msg.answer(f"❌ {result}")


# ── /alert — conditional recurring alert ──────────────────────────────────────
@router.message(Command("alert"))
async def cmd_alert(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/alert").strip()

    if not text:
        await msg.answer(
            "usage: <code>/alert &lt;name&gt; &lt;seconds&gt; &lt;command&gt; --if &lt;condition&gt;</code>\n\n"
            "examples:\n"
            "<code>/alert gpu-temp 120 nvidia-smi --if \"'80' in result\"</code>\n"
            "<code>/alert disk 3600 df -h / --if \"'9' in result.split()[4]\"</code>\n"
            "<code>/alert high-mem 300 free -m --if \"int(result.split()[8]) < 1000\"</code>\n\n"
            "condition has access to <code>result</code> (command output string)\n"
            "alert triggers when condition evaluates to True",
            parse_mode="HTML",
        )
        return

    if "--if" not in text:
        await msg.answer(
            "missing <code>--if</code> condition\n\n"
            "example: <code>/alert gpu 120 nvidia-smi --if \"'80' in result\"</code>",
            parse_mode="HTML",
        )
        return

    before_if, condition = text.split("--if", 1)
    condition = condition.strip().strip("\"'")
    parts = before_if.strip().split(maxsplit=2)

    if len(parts) < 3:
        await msg.answer(
            "usage: <code>/alert &lt;name&gt; &lt;seconds&gt; &lt;command&gt; --if &lt;condition&gt;</code>",
            parse_mode="HTML",
        )
        return

    name = parts[0]
    try:
        interval = int(parts[1])
    except ValueError:
        await msg.answer("interval must be a number (seconds)")
        return

    command = parts[2]

    if not _shared._scheduler:
        await msg.answer("scheduler not initialized — check bot logs")
        return

    task_id = await _shared._scheduler.add_monitor(
        description=f"Alert: {name}",
        command=command,
        interval_sec=interval,
        alert_condition=condition,
    )
    from tools.scheduler import _format_interval
    await msg.answer(
        f"🔔 Alert <code>{name}</code> created\n"
        f"  ID: <code>{task_id}</code>\n"
        f"  Check every: {_format_interval(interval)}\n"
        f"  Command: <code>{command}</code>\n"
        f"  Alert when: <code>{condition}</code>\n\n"
        f"cancel with <code>/cancel {task_id}</code>",
        parse_mode="HTML",
    )


# ── /watch_training — training log monitor ────────────────────────────────────
@router.message(Command("watch_training"))
async def cmd_watch_training(msg: Message) -> None:
    if not is_allowed(msg):
        return
    import os as _os
    log_path = _os.getenv("WORKERNET_LOG_PATH", "")
    if not log_path:
        await msg.answer(
            "WORKERNET_LOG_PATH not set in .env\n"
            "Set it to your training log path.",
        )
        return

    if not _shared._scheduler:
        await msg.answer("scheduler not initialized")
        return

    task_id = await _shared._scheduler.add_monitor(
        description="WorkerNet training watcher",
        command=f"tail -5 '{log_path}'",
        interval_sec=60,
        alert_condition="'nan' in result.lower() or 'inf' in result.lower() or 'best' in result.lower()",
    )
    await msg.answer(
        f"training watcher started: <code>{task_id}</code>\n"
        f"monitoring: {log_path}\n"
        f"alerts on: NaN, Inf, new best model\n\n"
        f"cancel: <code>/cancel {task_id}</code>",
        parse_mode="HTML",
    )
