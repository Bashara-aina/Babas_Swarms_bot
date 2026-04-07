"""
Session continuity handler — mneme task tracking.
Commands: /task, /task_done, /task_sessions, /semantic_set, /semantic_get

NOTE: /sessions (save/resume) lives in handlers/sessions.py.
      This file handles the mneme task-tracking sessions (/task_sessions).
"""
from __future__ import annotations

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router(name="session_handler")


@router.message(Command("task"))
async def cmd_task(message: Message) -> None:
    """Show or set the active task. Usage: /task [description]"""
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        from tools.mneme_session import get_current_task
        task = get_current_task()
        if task.get("task"):
            await message.answer(
                f"⚡ Active task: <b>{task['task']}</b>\nStatus: {task.get('status','?')}",
                parse_mode="HTML",
            )
        else:
            await message.answer("No active task. Use /task <description> to set one.")
        return
    description = args[1].strip()
    from tools.mneme_session import set_current_task
    set_current_task(description)
    await message.answer(f"✅ Task set: {description}")


@router.message(Command("task_done"))
async def cmd_task_done(message: Message) -> None:
    """Mark active task as complete. Usage: /task_done [result summary]"""
    args = (message.text or "").split(maxsplit=1)
    summary = args[1].strip() if len(args) > 1 else "Completed"
    from tools.mneme_session import complete_current_task, get_current_task
    task = get_current_task()
    if not task.get("task"):
        await message.answer("No active task to complete.")
        return
    complete_current_task(summary)
    await message.answer(f"✅ Task completed: {task['task']}\nResult: {summary}")


@router.message(Command("task_sessions"))
async def cmd_task_sessions(message: Message) -> None:
    """Show recent mneme session episodes. (Use /sessions for save/resume sessions.)"""
    from tools.mneme_session import get_recent_episodes
    episodes = get_recent_episodes(10)
    if not episodes:
        await message.answer("No task history yet.")
        return
    lines = ["<b>📚 Recent Task History</b>\n"]
    for ep in reversed(episodes):
        lines.append(f"• {ep.get('task','?')[:60]} → {ep.get('result_summary','?')[:60]}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("semantic_set"))
async def cmd_semantic_set(message: Message) -> None:
    """Store a semantic fact. Usage: /semantic_set key value"""
    args = (message.text or "").split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Usage: /semantic_set <key> <value>")
        return
    from tools.mneme_session import store_semantic_fact
    store_semantic_fact(args[1], args[2])
    await message.answer(f"✅ Stored: {args[1]} = {args[2]}")


@router.message(Command("semantic_get"))
async def cmd_semantic_get(message: Message) -> None:
    """Retrieve a semantic fact. Usage: /semantic_get key"""
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /semantic_get <key>")
        return
    from tools.mneme_session import get_semantic_fact
    val = get_semantic_fact(args[1])
    if val is None:
        await message.answer(f"No fact stored for key: {args[1]}")
    else:
        await message.answer(f"<b>{args[1]}</b>: {val}", parse_mode="HTML")
