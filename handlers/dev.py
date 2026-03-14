"""Dev handlers: /scaffold /build /vuln_scan /review /security_review."""
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


# ── /scaffold ─────────────────────────────────────────────────────────────────
@router.message(Command("scaffold"))
async def cmd_scaffold(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/scaffold").strip()
    if not text:
        await msg.answer(
            "usage: <code>/scaffold &lt;framework&gt; &lt;description&gt;</code>\n\n"
            "frameworks: nextjs, fastapi, laravel\n\n"
            "examples:\n"
            "<code>/scaffold nextjs personal portfolio with blog</code>\n"
            "<code>/scaffold fastapi todo API with JWT auth</code>",
            parse_mode="HTML",
        )
        return
    parts = text.split(maxsplit=1)
    framework = parts[0].lower()
    desc = parts[1] if len(parts) > 1 else framework

    features = []
    desc_lower = desc.lower()
    if "auth" in desc_lower:
        features.append("auth")
    if "supabase" in desc_lower:
        features.append("supabase")
    if "database" in desc_lower or "db" in desc_lower:
        features.append("database")

    project_name = desc.split()[:3]
    project_name = "-".join(w.lower() for w in project_name if w.isalnum())[:30] or framework

    status_msg = await msg.answer(f"scaffolding {framework} project: {project_name}...")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from tools.scaffolder import scaffold_nextjs, scaffold_fastapi, scaffold_laravel
        if framework in ("nextjs", "next"):
            result = await scaffold_nextjs(project_name, features)
        elif framework in ("fastapi", "fast"):
            result = await scaffold_fastapi(project_name, features)
        elif framework == "laravel":
            result = await scaffold_laravel(project_name, features)
        else:
            typing_task.cancel()
            await status_msg.edit_text(f"unknown framework: {framework}\nSupported: nextjs, fastapi, laravel")
            return
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used=f"scaffold/{framework}")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"scaffold error: <code>{e}</code>", parse_mode="HTML")


# ── /build ────────────────────────────────────────────────────────────────────
@router.message(Command("build"))
async def cmd_build(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/build").strip()
    if not task:
        await msg.answer(
            "usage: <code>/build &lt;task&gt;</code>\n\n"
            "runs frontend + backend agents in parallel.\n\n"
            "example:\n<code>/build e-commerce product page with cart API</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("frontend + backend agents running in parallel...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.scaffolder import parallel_fullstack
        result = await parallel_fullstack(task)
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="build/parallel")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"build error: <code>{e}</code>", parse_mode="HTML")


# ── /vuln_scan — vulnerability scan ──────────────────────────────────────────
@router.message(Command("vuln_scan"))
async def cmd_vuln_scan(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("scanning dependencies...")
    try:
        from tools.devops import check_vulnerabilities
        result = await check_vulnerabilities()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="devops/vuln-scan")
    except Exception as e:
        await status_msg.edit_text(f"scan error: <code>{e}</code>", parse_mode="HTML")


# ── /review ───────────────────────────────────────────────────────────────────
@router.message(Command("review"))
async def cmd_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/review").strip()
    if not arg:
        await msg.answer(
            "usage: <code>/review &lt;file_path&gt;</code>\n"
            "or reply to a code message with /review",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("🔍 reviewing…")
    try:
        from tools.code_reviewer import review_file, review_code
        from pathlib import Path
        if Path(arg).exists():
            result = await review_file(arg)
        else:
            result = await review_code(arg, language="python")
        import html as html_mod
        await status_msg.edit_text(result[:4000], parse_mode="HTML")
    except Exception as e:
        import html as html_mod
        await status_msg.edit_text(
            f"review error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── /security_review ──────────────────────────────────────────────────────────
@router.message(Command("security_review"))
async def cmd_security_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/security_review").strip()
    if not arg:
        await msg.answer("usage: <code>/security_review &lt;file_path&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer("🛡 security review…")
    try:
        from tools.code_reviewer import review_file
        result = await review_file(arg, review_type="security")
        import html as html_mod
        await status_msg.edit_text(result[:4000], parse_mode="HTML")
    except Exception as e:
        import html as html_mod
        await status_msg.edit_text(
            f"review error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )
