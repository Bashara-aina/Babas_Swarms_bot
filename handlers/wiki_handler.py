"""Telegram commands for Legion LLM Wiki (Karpathy pattern)."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.wiki_manager import get_wiki_manager
from handlers.shared import is_allowed
from llm_client import chunk_output

router = Router()


@router.message(Command("wiki"))
async def cmd_wiki(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").replace("/wiki", "", 1).strip()
    if not text:
        await msg.answer("Usage: /wiki <question>")
        return
    wm = get_wiki_manager()
    result = await wm.query(text, top_k=5)
    if not result:
        await msg.answer("No relevant wiki pages found for that query yet.")
        return
    for part in chunk_output(result, max_length=4000):
        await msg.answer(part)


@router.message(Command("wiki_ingest"))
async def cmd_wiki_ingest(msg: Message) -> None:
    if not is_allowed(msg):
        return
    source = ""
    if msg.reply_to_message and msg.reply_to_message.text:
        source = msg.reply_to_message.text
    elif msg.document:
        await msg.answer("File ingestion: paste text or reply to a text message for now.")
        return
    else:
        await msg.answer("Reply to a message with /wiki_ingest to ingest it into the wiki.")
        return

    await msg.answer("Ingesting into wiki…")
    pages = await get_wiki_manager().ingest(
        source=source,
        source_type="manual",
        context="Telegram /wiki_ingest",
    )
    if not pages:
        await msg.answer("No pages were updated (model returned empty plan or failed).")
        return
    lines = "\n".join(f"• {p}" for p in pages)
    await msg.answer(f"Wiki updated. Pages:\n{lines}")


@router.message(Command("wiki_lint"))
async def cmd_wiki_lint(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer("Running wiki lint (may take ~30s)…")
    report = await get_wiki_manager().lint()
    for part in chunk_output(report, max_length=4000):
        await msg.answer(part)
