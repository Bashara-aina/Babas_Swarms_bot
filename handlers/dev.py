"""Dev handlers: /scaffold /build /vuln_scan /review /security_review."""

from __future__ import annotations

import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    _cancel_task,
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
        from tools.scaffolder import scaffold_fastapi, scaffold_laravel, scaffold_nextjs

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
            "usage: <code>/review &lt;file_path&gt;</code>\nor reply to a code message with /review",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("🔍 reviewing…")
    try:
        from pathlib import Path

        from tools.code_reviewer import review_code, review_file

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

        await msg.answer(
            f"review error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── /opencode ─────────────────────────────────────────────────────────────────
# ── /codex ────────────────────────────────────────────────────────────────────
@router.message(Command("codex"))
async def cmd_codex(msg: Message) -> None:
    """Route a task to Claude Code via the claude_code_bridge."""
    if not is_allowed(msg):
        return
    task_text = (msg.text or "").removeprefix("/codex").strip()
    if not task_text:
        await msg.answer(
            "usage: <code>/codex &lt;task description&gt;</code>\n\n"
            "Routes task through Claude Code with Legion's review context.\n\n"
            "Example:\n<code>/codex implement rate limiting middleware</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("🤖 Legion dispatching to Claude Code…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from core.claude_code_bridge import run_claude_task

        result = await run_claude_task(
            prompt=task_text,
            timeout=180,
        )

        await _cancel_task(typing_task)
        if result.get("success") and result.get("output"):
            await send_chunked(msg, result["output"])
        else:
            await status_msg.delete()
            await msg.answer(
                f"Claude Code error: {result.get('error', 'unknown')}",
                parse_mode="HTML",
            )
    except Exception as e:
        await _cancel_task(typing_task)
        import html as html_mod

        if "status_msg" in dir():
            await status_msg.edit_text(
                f"codex error: <code>{html_mod.escape(str(e)[:400])}</code>",
                parse_mode="HTML",
            )
        else:
            await msg.answer(
                f"codex error: <code>{html_mod.escape(str(e)[:400])}</code>",
                parse_mode="HTML",
            )


# ── /opencode ─────────────────────────────────────────────────────────────────
@router.message(Command("opencode"))
async def cmd_opencode(msg: Message) -> None:
    """Route a task to opencode CLI via the Legion bridge."""
    if not is_allowed(msg):
        return
    task_text = (msg.text or "").removeprefix("/opencode").strip()
    if not task_text:
        await msg.answer(
            "usage: <code>/opencode &lt;task description&gt;</code>\n\n"
            "Routes task through opencode with Legion's full pipeline:\n"
            "PLAN → IMPLEMENT → REVIEW → TEST → COMMIT → REPORT\n\n"
            "Example:\n<code>/opencode add user authentication to the API</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("🤖 Legion dispatching to opencode…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from core.opencode_bridge import build_opencode_prompt, extract_report, run_opencode_task

        username = msg.from_user.username if msg.from_user else "unknown"
        prompt = build_opencode_prompt(task_text, project="/home/newadmin/swarm-bot", user=username)
        result = await run_opencode_task(prompt, project_dir="/home/newadmin/swarm-bot")
        report = extract_report(result)

        await _cancel_task(typing_task)
        await status_msg.delete()
        await send_chunked(msg, report)
    except Exception as e:
        await _cancel_task(typing_task)
        import html as html_mod

        await status_msg.edit_text(
            f"opencode error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )
