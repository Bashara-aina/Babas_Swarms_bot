"""handlers/draft.py — Dify document drafting: /draft command.

Integrates with Dify workflow platform for long-form document drafting,
legal document generation, and structured analysis.
"""

from __future__ import annotations

import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("draft"))
async def cmd_draft(msg: Message) -> None:
    if not is_allowed(msg):
        return

    args = (msg.text or "").removeprefix("/draft").strip().split()
    if not args:
        await msg.answer(
            "<b>Usage:</b> <code>/draft &lt;type&gt; &lt;content&gt;</code>\n\n"
            "<b>Types:</b>\n"
            "• <code>legal</code> — UU PDP / ToS / disclaimer drafting\n"
            "• <code>analysis</code> — document analysis\n"
            "• <code>report</code> — structured report generation\n\n"
            "<b>Example:</b>\n"
            "<code>/draft legal UU PDP dual-checkbox consent for payslip upload</code>",
            parse_mode="HTML",
        )
        return

    task_type = args[0] if args[0] in ["legal", "analysis", "report"] else "default"
    content = " ".join(args[1:] if args[0] in ["legal", "analysis", "report"] else args)

    if not content:
        await msg.answer("Please provide content for drafting.")
        return

    status_msg = await msg.answer(f"✍️ [Dify] drafting {task_type}…", parse_mode="HTML")

    try:
        from core.skills.dify_analysis import execute as dify_execute

        result = await dify_execute(task_type, content)

        if len(result) > 4000:
            result = result[:4000] + "\n\n_[Output truncated]_"

        await status_msg.delete()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Dify draft error: {e}")
        await status_msg.edit_text(f"Draft error: {e}", parse_mode="HTML")
