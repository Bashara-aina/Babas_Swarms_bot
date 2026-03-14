"""Orchestration handler — /orchestrate command using full DAG pipeline.

Exposes the complete multi-agent orchestration to the Telegram user:
  /orchestrate Build a FastAPI CRUD app with auth and tests
  /orchestrate_status  — show current run status
  /orchestrate_approve — approve pending plan
  /orchestrate_cancel  — cancel current run
"""
from __future__ import annotations

import asyncio
import logging
import html as html_mod
from typing import Dict, Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from handlers.shared import is_allowed, send_chunked

logger = logging.getLogger(__name__)
router = Router()

# Track active runs per user
_active_runs: Dict[int, dict] = {}


@router.message(Command("orchestrate"))
async def cmd_orchestrate(msg: Message) -> None:
    """Start a full DAG orchestration run."""
    if not is_allowed(msg):
        return

    goal = (msg.text or "").removeprefix("/orchestrate").strip()
    if not goal:
        await msg.answer(
            "Usage: <code>/orchestrate &lt;goal&gt;</code>\n\n"
            "Example:\n"
            "<code>/orchestrate Build a FastAPI CRUD app with JWT auth and pytest tests</code>\n\n"
            "Legion will:\n"
            "1. Decompose your goal into a task DAG\n"
            "2. Show you the plan for approval\n"
            "3. Execute all subtasks in parallel\n"
            "4. Synthesize a final result",
            parse_mode="HTML",
        )
        return

    user_id = msg.from_user.id
    if user_id in _active_runs:
        await msg.answer(
            "⚠️ An orchestration is already running. Use /orchestrate_cancel to stop it first."
        )
        return

    status_msg = await msg.answer("🚀 Starting orchestration…")
    step_count = 0

    async def progress_cb(text: str) -> None:
        nonlocal step_count
        step_count += 1
        try:
            safe = html_mod.escape(text)
            await status_msg.edit_text(
                f"<code>[{step_count}]</code> {safe}",
                parse_mode="HTML",
            )
        except Exception:
            try:
                await msg.answer(html_mod.escape(text), parse_mode="HTML")
            except Exception:
                pass

    async def send_fn(text: str, markup=None) -> None:
        try:
            await msg.answer(
                html_mod.escape(text) if markup is None else text,
                reply_markup=markup,
                parse_mode="HTML",
            )
        except Exception:
            pass

    try:
        from swarms_bot.orchestrator.orchestration_runner import OrchestrationRunner
        from swarms_bot.orchestrator.registry import build_agent_registry

        registry = build_agent_registry()
        runner = OrchestrationRunner(
            agent_registry=registry,
            send_fn=send_fn,
            require_approval=True,
            approval_timeout=120,
            max_parallel=4,
        )

        _active_runs[user_id] = {"goal": goal, "runner": runner}

        result = await runner.run(
            goal=goal,
            user_id=user_id,
            progress_cb=progress_cb,
        )

        await status_msg.delete()
        await send_chunked(msg, result)

    except Exception as e:
        logger.error("Orchestration error: %s", e)
        err = html_mod.escape(str(e))
        await status_msg.edit_text(
            f"❌ Orchestration failed:\n<code>{err[:400]}</code>",
            parse_mode="HTML",
        )
    finally:
        _active_runs.pop(user_id, None)


@router.message(Command("orchestrate_cancel"))
async def cmd_orchestrate_cancel(msg: Message) -> None:
    if not is_allowed(msg):
        return
    user_id = msg.from_user.id
    if user_id not in _active_runs:
        await msg.answer("No active orchestration run.")
        return
    _active_runs.pop(user_id)
    await msg.answer("⛔ Orchestration cancelled.")


@router.callback_query(lambda c: c.data and c.data.startswith("plan_"))
async def handle_plan_approval(cb: CallbackQuery) -> None:
    """Handle plan approve/reject inline button callbacks."""
    from swarms_bot.orchestrator.human_in_loop import HumanApprovalGate
    action, run_id = cb.data.split(":", 1)
    approved = action == "plan_approve"

    # Find the gate for this run_id
    user_id = cb.from_user.id
    run_data = _active_runs.get(user_id, {})
    runner = run_data.get("runner")

    # The runner's gate resolves via the callback
    # We publish the decision by editing the message
    icon = "✅ Approved" if approved else "❌ Rejected"
    try:
        await cb.message.edit_text(
            f"{cb.message.text}\n\n{icon} by you.",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await cb.answer(icon)
