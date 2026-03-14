"""Session handlers: /save /resume /sessions /audit."""
from __future__ import annotations

import html as html_mod

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    _user_thread,
    is_allowed,
)
import handlers.shared as _shared

router = Router()


# ── /save ─────────────────────────────────────────────────────────────────────
@router.message(Command("save"))
async def cmd_save(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/save").strip()
    if not name:
        await msg.answer("usage: <code>/save &lt;session_name&gt;</code>", parse_mode="HTML")
        return
    try:
        if _shared._session_manager:
            thread_id = _user_thread.get(msg.from_user.id, f"tg_{msg.chat.id}")
            _shared._session_manager.get_or_create_session(
                user_id=msg.from_user.id,
                chat_id=msg.chat.id,
                thread_id=thread_id,
            )
            session = await _shared._session_manager.save_session(msg.from_user.id, name)
            if session:
                await msg.answer(
                    f"✅ Session <b>{html_mod.escape(name)}</b> saved\n"
                    f"ID: <code>{session.session_id}</code>\n"
                    f"Tasks: {session.task_count} | "
                    f"Cost: ${session.total_cost_usd:.4f} | "
                    f"Tokens: {session.total_tokens:,}\n"
                    f"Resume: <code>/resume {html_mod.escape(name)}</code>",
                    parse_mode="HTML",
                )
                return

        # Fallback to legacy persistence
        import json as _json
        import uuid
        from agents import ACTIVE_THREADS
        from tools.persistence import save_session
        thread_id = f"tg_{msg.chat.id}"
        context = ACTIVE_THREADS.get(thread_id, [])
        session_id = uuid.uuid4().hex[:12]
        await save_session(
            session_id=session_id,
            name=name,
            thread_id=thread_id,
            agent_key="general",
            context_json=_json.dumps(context, default=str),
        )
        await msg.answer(
            f"✅ Session <b>{html_mod.escape(name)}</b> saved ({len(context)} messages)\n"
            f"ID: <code>{session_id}</code>\nResume: <code>/resume {html_mod.escape(name)}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /resume ───────────────────────────────────────────────────────────────────
@router.message(Command("resume"))
async def cmd_resume(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/resume").strip()
    if not name:
        await msg.answer("usage: <code>/resume &lt;session_name&gt;</code>", parse_mode="HTML")
        return
    try:
        if _shared._session_manager:
            session = await _shared._session_manager.resume_session(msg.from_user.id, name)
            if session:
                if session.thread_id:
                    _user_thread[msg.from_user.id] = session.thread_id
                await msg.answer(
                    f"✅ Resumed <b>{html_mod.escape(session.name)}</b>\n"
                    f"Tasks: {session.task_count} | "
                    f"Cost: ${session.total_cost_usd:.4f}\n"
                    f"Thread: <code>{session.thread_id or 'new'}</code>",
                    parse_mode="HTML",
                )
                return
            else:
                await msg.answer(
                    f"Session <b>{html_mod.escape(name)}</b> not found.",
                    parse_mode="HTML",
                )
                return

        # Fallback to legacy persistence
        from agents import ACTIVE_THREADS
        from tools.persistence import load_session
        session = await load_session(name=name)
        if not session:
            await msg.answer(f"session not found: <b>{html_mod.escape(name)}</b>", parse_mode="HTML")
            return
        import json as _json
        thread_id = session["thread_id"]
        context = _json.loads(session.get("context_json", "[]"))
        ACTIVE_THREADS[thread_id] = context
        _user_thread[msg.from_user.id] = thread_id
        await msg.answer(
            f"✅ Resumed <b>{html_mod.escape(name)}</b> ({len(context)} messages)\n"
            f"Thread: <code>{thread_id}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /sessions ─────────────────────────────────────────────────────────────────
@router.message(Command("sessions"))
async def cmd_sessions(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        if _shared._session_manager:
            sessions = await _shared._session_manager.list_sessions(msg.from_user.id)
            if not sessions:
                await msg.answer("No sessions saved yet. Use /save to save the current session.")
                return
            lines = ["<b>Saved Sessions</b>\n"]
            for s in sessions[:10]:
                lines.append(
                    f"  <b>{html_mod.escape(s.name)}</b> | "
                    f"{s.task_count} tasks | "
                    f"${s.total_cost_usd:.4f}\n"
                    f"  Resume: <code>/resume {html_mod.escape(s.name)}</code>\n"
                )
            await msg.answer("\n".join(lines), parse_mode="HTML")
            return

        # Fallback
        from tools.persistence import list_sessions
        sessions = await list_sessions()
        if not sessions:
            await msg.answer("No sessions saved yet.")
            return
        lines = ["<b>Sessions</b>\n"]
        for s in sessions:
            lines.append(
                f"  <code>{s['session_id']}</code> <b>{html_mod.escape(s['name'])}</b> "
                f"({s.get('message_count', 0)} msgs)\n"
                f"  Resume: <code>/resume {html_mod.escape(s['name'])}</code>\n"
            )
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /audit ────────────────────────────────────────────────────────────────────
@router.message(Command("audit"))
async def cmd_audit(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/audit").strip()
    hours = int(arg) if arg.isdigit() else 24
    try:
        from tools.persistence import get_audit_summary
        summary = await get_audit_summary(hours=hours)
        if not summary["breakdown"]:
            await msg.answer(f"No activity in the last {hours}h.")
            return
        lines = [f"<b>Audit — last {hours}h</b>\n"]
        total_tin = total_tout = total_err = 0
        for row in summary["breakdown"]:
            tin = row["tin"] or 0
            tout = row["tout"] or 0
            total_tin += tin
            total_tout += tout
            total_err += row["errors"] or 0
            lines.append(
                f"  <code>{row['action']:12}</code> ×{row['cnt']} "
                f"({tin + tout} tok, {row['errors'] or 0} err)"
            )
        lines.append(f"\nTotal: {total_tin + total_tout} tokens, {total_err} errors")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")
