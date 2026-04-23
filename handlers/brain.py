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


# /remember and /recall are handled by memory_commands.py (registered first)


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
            "usage: <code>/learn &lt;pattern or preference&gt;</code>\nExample: /learn Always use type hints in Python",
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


@router.message(Command("om_stats"))
async def cmd_om_stats(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.open_memory import om_stats

        stats = await om_stats(str(msg.from_user.id))
        if not stats:
            await msg.answer("No OpenMemory entries yet.")
            return
        lines = ["<b>📊 OpenMemory Stats</b>", ""]
        for sector, data in stats.items():
            lines.append(
                f"<b>{sector}</b>: {data['count']} memories | avg importance {data['avg_importance']} | avg accesses {data['avg_accesses']}"
            )
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


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
                f"  <code>#{i['id']}</code> [{i['category']}] {html_mod.escape(i['content'][:80])} (used {i['uses']}×)"
            )
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /forget ───────────────────────────────────────────────────────────────────
@router.message(Command("forget"))
async def cmd_forget(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(
        "ℹ️ /forget now lives in /memory. Use:\n"
        "  /forget <key>  — delete a core memory entry\n"
        "  /forget <id>   — delete an instinct by number"
    )


# ── /self_review ───────────────────────────────────────────────────────────────
@router.message(Command("self_review"))
async def cmd_self_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer("🧠 Running self-review now...")
    try:
        from core.self_improvement import _conversation_buffer, _run_self_review

        if not _conversation_buffer:
            await msg.answer("No conversations buffered yet for review.")
            return
        await _run_self_review()
        await msg.answer("✅ Self-review complete. SOUL.md updated if changes found.")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")
