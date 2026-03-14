"""Brain handlers: /remember /recall /memories /brain_export /briefing /learn /instincts /forget."""
from __future__ import annotations

import asyncio
import html as html_mod
import time
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    _keep_typing,
    is_allowed,
    send_chunked,
)

router = Router()


# ── /briefing — morning briefing ──────────────────────────────────────────────
@router.message(Command("briefing"))
async def cmd_briefing(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("assembling briefing...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.briefing import generate_briefing
        briefing = await generate_briefing()
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, briefing, model_used="briefing")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"briefing error: <code>{e}</code>", parse_mode="HTML")


# ── /remember ─────────────────────────────────────────────────────────────────
@router.message(Command("remember"))
async def cmd_remember(msg: Message) -> None:
    if not is_allowed(msg):
        return
    note = (msg.text or "").removeprefix("/remember").strip()
    if not note:
        await msg.answer("usage: <code>/remember &lt;note&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.memory import add_memory
        note_id = await add_memory(note, source="telegram")
        await msg.answer(f"saved (id: {note_id})")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /recall ───────────────────────────────────────────────────────────────────
@router.message(Command("recall"))
async def cmd_recall(msg: Message) -> None:
    if not is_allowed(msg):
        return
    query = (msg.text or "").removeprefix("/recall").strip()
    if not query:
        await msg.answer("usage: <code>/recall &lt;query&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.memory import search_memory
        results = await search_memory(query, top_k=5)
        if not results:
            await msg.answer("no matching memories found.")
            return
        lines = ["<b>Matching memories:</b>\n"]
        for r in results:
            ts = time.strftime("%m/%d", time.localtime(r["created_at"]))
            tags = f" [{r['tags']}]" if r.get("tags") else ""
            lines.append(f"  #{r['id']} ({ts}{tags}) rel:{r['relevance']}")
            lines.append(f"  {r['text'][:150]}...\n")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /memories ─────────────────────────────────────────────────────────────────
@router.message(Command("memories"))
async def cmd_memories(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.memory import get_recent_memories
        notes = await get_recent_memories(limit=10)
        if not notes:
            await msg.answer("no memories saved yet. Use <code>/remember &lt;note&gt;</code>", parse_mode="HTML")
            return
        lines = ["<b>Recent memories:</b>\n"]
        for n in notes:
            ts = time.strftime("%m/%d %H:%M", time.localtime(n["created_at"]))
            tags = f" [{n['tags']}]" if n.get("tags") else ""
            lines.append(f"  #{n['id']} ({ts}{tags}) [{n['source']}]")
            lines.append(f"  {n['text'][:120]}...\n")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /brain_export ─────────────────────────────────────────────────────────────
@router.message(Command("brain_export"))
async def cmd_brain_export(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("exporting to Obsidian vault...")
    try:
        from tools.memory import export_to_obsidian
        vault_path = str(Path.home() / "brain")
        result = await export_to_obsidian(vault_path)
        await status_msg.edit_text(result)
    except Exception as e:
        await status_msg.edit_text(f"export error: <code>{e}</code>", parse_mode="HTML")


# ── /learn ────────────────────────────────────────────────────────────────────
@router.message(Command("learn"))
async def cmd_learn(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/learn").strip()
    if not text:
        await msg.answer(
            "usage: <code>/learn &lt;pattern or preference&gt;</code>\n"
            "Example: /learn Always use type hints in Python",
            parse_mode="HTML",
        )
        return
    t = text.lower()
    if any(k in t for k in ("style", "format", "naming", "convention")):
        category = "style"
    elif any(k in t for k in ("prefer", "always", "never", "default")):
        category = "preference"
    elif any(k in t for k in ("fix", "correct", "actually", "instead")):
        category = "correction"
    else:
        category = "pattern"
    try:
        from tools.persistence import add_instinct
        iid = await add_instinct(category, text, source="manual")
        await msg.answer(
            f"✅ Learned [{category}] (id: {iid})\n<i>{html_mod.escape(text[:200])}</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /instincts ────────────────────────────────────────────────────────────────
@router.message(Command("instincts"))
async def cmd_instincts(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.persistence import get_instincts
        items = await get_instincts(limit=30)
        if not items:
            await msg.answer("No instincts yet. Use /learn to add some.")
            return
        lines = ["<b>Instincts</b>\n"]
        for i in items:
            lines.append(
                f"  <code>#{i['id']}</code> [{i['category']}] "
                f"{html_mod.escape(i['content'][:80])} "
                f"(used {i['uses']}×)"
            )
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /forget ───────────────────────────────────────────────────────────────────
@router.message(Command("forget"))
async def cmd_forget(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/forget").strip()
    if not arg.isdigit():
        await msg.answer("usage: <code>/forget &lt;instinct_id&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.persistence import delete_instinct
        ok = await delete_instinct(int(arg))
        if ok:
            await msg.answer(f"✅ Instinct #{arg} deleted.")
        else:
            await msg.answer(f"Instinct #{arg} not found.")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")
