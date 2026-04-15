"""Plandex command handlers: /code /diff /apply /abort.

Bashara routes coding tasks to Plandex for autonomous multi-file editing.
Plan → Review diff → /apply to confirm or /abort to cancel.
"""

from __future__ import annotations

import html as html_mod

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from tools.plandex_agent import PlandexAgent, PLANDEX_PROJECT_DIR
from handlers.shared import is_allowed

router = Router()

_plandex = PlandexAgent()


# FSM states for plan lifecycle
class PlandexState(StatesGroup):
    plan_ready = State()  # awaiting /apply or /abort
    diff_review = State()  # reviewing diff


def _require_owner(message: Message) -> bool:
    """Return True if the message is from the allowed user, False otherwise."""
    return is_allowed(message)


@router.message(Command("code"))
async def cmd_code(message: Message, state: FSMContext) -> None:
    """
    /code <task description>
    Send a coding task to Plandex. Shows plan first, then waits for /apply.
    Example: /code Refactor intent_router to use keyword tuples
    """
    if not _require_owner(message):
        return
    task = message.text.removeprefix("/code").strip()
    if not task:
        await message.answer(
            "usage: <code>/code &lt;task description&gt;</code>\n\n"
            "Sends a coding task to Plandex for autonomous multi-file editing.\n"
            "Reply <code>/apply</code> to confirm, <code>/abort</code> to cancel.",
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"Planning with Plandex…\n<code>{html_mod.escape(task[:80])}</code>",
        parse_mode="HTML",
    )

    lines = []
    async for line in _plandex.plan(task):
        lines.append(line)
        # Stream every 10 lines to avoid flooding
        if len(lines) % 10 == 0:
            await message.answer(html_mod.escape(line[-200:]))

    plan_id = PlandexAgent.extract_plan_id(lines)
    if not plan_id:
        await message.answer(
            f"Plan created but couldn't extract ID.\n\nLast output:\n{lines[-1]}"
        )
        return

    diff = await _plandex.diff(plan_id)
    await state.update_data(plan_id=plan_id, task=task)
    await state.set_state(PlandexState.plan_ready)

    diff_preview = diff[:3500] if diff else "(no diff)"
    # send_chunked doesn't support parse_mode — use message.answer for HTML rendering
    await message.answer(
        f"Plan ready — ID: <code>{html_mod.escape(plan_id)}</code>\n\n<code>{html_mod.escape(diff_preview)}</code>",
        parse_mode="HTML",
    )
    await message.answer(
        "Reply <code>/apply</code> to apply, <code>/abort</code> to cancel.",
        parse_mode="HTML",
    )


@router.message(Command("apply"))
async def cmd_apply(message: Message, state: FSMContext) -> None:
    """Apply the pending Plandex plan after Bashara reviews the diff."""
    if not _require_owner(message):
        return
    data = await state.get_data()
    plan_id = data.get("plan_id")
    if not plan_id:
        await message.answer("No pending plan. Use <code>/code</code> first.", parse_mode="HTML")
        return

    await message.answer("Applying plan…")
    result = await _plandex.apply(plan_id)
    await state.clear()
    # send_chunked doesn't support parse_mode — use message.answer for HTML rendering
    await message.answer(
        f"Applied:\n<code>{html_mod.escape(result[:4000])}</code>",
        parse_mode="HTML",
    )


@router.message(Command("abort"))
async def cmd_abort(message: Message, state: FSMContext) -> None:
    """Abort the pending Plandex plan."""
    if not _require_owner(message):
        return
    data = await state.get_data()
    plan_id = data.get("plan_id")
    if plan_id:
        await _plandex.abort(plan_id)
        note = f" Aborted plan <code>{plan_id}</code>."
    else:
        note = ""
    await state.clear()
    await message.answer(f"Plan cancelled.{note}", parse_mode="HTML")


@router.message(Command("diff"))
async def cmd_diff(message: Message, state: FSMContext) -> None:
    """Re-show the diff of the pending plan."""
    if not _require_owner(message):
        return
    data = await state.get_data()
    plan_id = data.get("plan_id")
    if not plan_id:
        await message.answer("No pending plan. Use <code>/code</code> first.", parse_mode="HTML")
        return

    diff = await _plandex.diff(plan_id)
    # send_chunked doesn't support parse_mode — use message.answer directly for HTML
    await message.answer(
        f"Diff for <code>{html_mod.escape(plan_id)}</code>:\n\n<code>{html_mod.escape(diff[:3500])}</code>",
        parse_mode="HTML",
    )
