"""PM/content/email handlers: /task_from /tasks_due /task_done /delegate /post /brand_check /email."""
from __future__ import annotations

import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    _keep_typing,
    is_allowed,
    send_chunked,
)

router = Router()


# ── /task_from ────────────────────────────────────────────────────────────────
@router.message(Command("task_from"))
async def cmd_task_from(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/task_from").strip()
    if not text:
        await msg.answer(
            "usage: <code>/task_from &lt;text or transcript&gt;</code>\n\n"
            "extracts structured tasks from any text.\n\n"
            "example:\n"
            "<code>/task_from discussed: add auth by friday, deploy monday, john handles DB</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("extracting tasks...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.project_manager import transcript_to_tasks, save_tasks_local
        tasks = await transcript_to_tasks(text)
        await save_tasks_local(tasks, "telegram")
        typing_task.cancel()
        await status_msg.delete()
        lines = [f"<b>Extracted {len(tasks)} tasks:</b>\n"]
        priority_icons = {"high": "!!", "mid": "!", "low": ""}
        for t in tasks:
            icon = priority_icons.get(t.get("priority", "mid"), "")
            lines.append(f"  {icon} {t['task'][:80]}")
            lines.append(f"    owner: {t.get('owner', '?')} | deadline: {t.get('deadline', 'TBD')}\n")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /tasks_due ────────────────────────────────────────────────────────────────
@router.message(Command("tasks_due"))
async def cmd_tasks_due(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.project_manager import check_deadlines
        result = await check_deadlines()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /task_done ────────────────────────────────────────────────────────────────
@router.message(Command("task_done"))
async def cmd_task_done(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task_id_str = (msg.text or "").removeprefix("/task_done").strip()
    if not task_id_str:
        await msg.answer("usage: <code>/task_done &lt;id&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.project_manager import complete_task
        result = await complete_task(int(task_id_str))
        await msg.answer(result)
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /delegate — OpenClaw delegation ───────────────────────────────────────────
@router.message(Command("delegate"))
async def cmd_delegate(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/delegate").strip()
    if not task:
        await msg.answer(
            "usage: <code>/delegate &lt;task&gt;</code>\n\n"
            "sends task to OpenClaw (smart home, Obsidian, Spotify, etc.)",
            parse_mode="HTML",
        )
        return
    try:
        from tools.openclaw_bridge import delegate_to_openclaw
        result = await delegate_to_openclaw(task)
        await send_chunked(msg, result, model_used="openclaw")
    except Exception as e:
        await msg.answer(f"delegate error: <code>{e}</code>", parse_mode="HTML")


# ── /post — social media drafting ─────────────────────────────────────────────
@router.message(Command("post"))
async def cmd_post(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/post").strip()
    if not text:
        await msg.answer(
            "usage: <code>/post &lt;platform&gt; &lt;topic&gt;</code>\n\n"
            "platforms: linkedin, tweet, thread\n\n"
            "example:\n<code>/post linkedin my WorkerNet model achieves 60% accuracy on IKEA ASM</code>",
            parse_mode="HTML",
        )
        return
    parts = text.split(maxsplit=1)
    platform = parts[0].lower()
    topic = parts[1] if len(parts) > 1 else text
    status_msg = await msg.answer(f"drafting {platform} post...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.content import draft_linkedin_post, draft_tweet
        if platform == "linkedin":
            result = await draft_linkedin_post(topic)
        elif platform == "tweet":
            result = await draft_tweet(topic, thread=False)
        elif platform == "thread":
            result = await draft_tweet(topic, thread=True)
        else:
            typing_task.cancel()
            await status_msg.edit_text("platforms: linkedin, tweet, thread")
            return
        typing_task.cancel()
        await status_msg.delete()
        await msg.answer(f"<b>{platform.upper()} draft:</b>\n\n{result}", parse_mode="HTML")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /brand_check — brand monitoring ───────────────────────────────────────────
@router.message(Command("brand_check"))
async def cmd_brand_check(msg: Message) -> None:
    if not is_allowed(msg):
        return
    keyword = (msg.text or "").removeprefix("/brand_check").strip()
    if not keyword:
        await msg.answer("usage: <code>/brand_check &lt;keyword&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer(f"searching for: {keyword}...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.content import monitor_brand
        result = await monitor_brand([keyword])
        typing_task.cancel()
        await status_msg.delete()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /email — email management ────────────────────────────────────────────────
@router.message(Command("email"))
async def cmd_email(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/email").strip()

    if not text:
        status_msg = await msg.answer("📧 checking inbox…")
        typing_task = asyncio.create_task(_keep_typing(msg))
        try:
            from tools.email_client import check_inbox
            result = await check_inbox(limit=10, unread_only=True)
            typing_task.cancel()
            await status_msg.delete()
            await msg.answer(
                f"<pre>{result[:3800]}</pre>",
                parse_mode="HTML",
            )
        except Exception as e:
            typing_task.cancel()
            await status_msg.edit_text(f"email error: <code>{e}</code>", parse_mode="HTML")
        return

    parts = text.split(maxsplit=1)
    subcmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if subcmd == "check":
        status_msg = await msg.answer("📧 checking…")
        from tools.email_client import check_inbox
        result = await check_inbox(limit=10, unread_only="unread" in arg or not arg)
        await status_msg.delete()
        await msg.answer(f"<pre>{result[:3800]}</pre>", parse_mode="HTML")

    elif subcmd == "read" and arg:
        status_msg = await msg.answer("📧 reading…")
        from tools.email_client import read_email
        result = await read_email(arg.strip())
        await status_msg.delete()
        await send_chunked(msg, result, model_used="email")

    elif subcmd == "search" and arg:
        status_msg = await msg.answer(f"🔍 searching: {arg}…")
        from tools.email_client import search_emails
        result = await search_emails(arg.strip())
        await status_msg.delete()
        await msg.answer(f"<pre>{result[:3800]}</pre>", parse_mode="HTML")

    else:
        await msg.answer(
            "usage:\n"
            "  <code>/email</code>           — show unread\n"
            "  <code>/email check</code>     — list unread\n"
            "  <code>/email read &lt;uid&gt;</code>  — read email\n"
            "  <code>/email search &lt;q&gt;</code>  — search by subject\n\n"
            "or use <code>/do check my email</code> for AI-powered inbox management",
            parse_mode="HTML",
        )
