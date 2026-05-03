"""Maintenance runbooks: /runbook [id]"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed
from tools.runbook_engine import execute_runbook, list_runbook_summaries

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("runbook"))
async def cmd_runbook(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").replace("/runbook", "", 1).strip()
    if not arg:
        await msg.answer(list_runbook_summaries(), parse_mode="HTML")
        return
    first = arg.split()[0].strip()
    try:
        report = await execute_runbook(first)
        await msg.answer(report[:4000], parse_mode="HTML")
    except Exception as e:
        logger.warning("[runbook] %s", e)
        await msg.answer(f"Runbook failed: <code>{str(e)[:300]}</code>", parse_mode="HTML")
