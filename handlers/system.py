"""System info handlers: /status /gpu /keys /models /resources."""
from __future__ import annotations

import asyncio
import html as html_mod
import platform
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    _start_time,
    _key_status,
    is_allowed,
    send_chunked,
)

router = Router()


# ── /status ───────────────────────────────────────────────────────────────────
@router.message(Command("status"))
@router.message(F.text == "\u2699\ufe0f Status")
async def cmd_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    uptime_s  = int(time.time() - _start_time)
    h, rem    = divmod(uptime_s, 3600)
    m, s      = divmod(rem, 60)
    uptime    = f"{h}h {m}m {s}s"
    py_ver    = platform.python_version()
    os_info   = f"{platform.system()} {platform.release()}"

    key_block = _key_status()

    try:
        from tools.resource_monitor import get_resource_snapshot
        snap = await get_resource_snapshot()
        local_line = (
            "\U0001f916 Ollama: \u2705 ready"
            if snap.local_allowed
            else f"\U0001f916 Ollama: \u26a0\ufe0f bypassed ({snap.block_reason[:60]})"
        )
        ram_line = f"\U0001f9e0 RAM free: {snap.ram_free_gb:.1f}GB"
        gpu_line = (
            f"\U0001f3ae VRAM free: {snap.vram_free_gb:.1f}GB"
            if snap.vram_free_gb is not None
            else "\U0001f3ae GPU: not detected"
        )
        resource_block = f"\n{ram_line}\n{gpu_line}\n{local_line}"
    except Exception:
        resource_block = ""

    text = (
        f"<b>\U0001f916 Legion Status</b>\n\n"
        f"\u23f1 uptime: <code>{uptime}</code>\n"
        f"\U0001f40d Python: <code>{py_ver}</code>\n"
        f"\U0001f4bb OS: <code>{os_info}</code>\n"
        f"{resource_block}\n\n"
        f"{key_block}"
    )
    await msg.answer(text, parse_mode="HTML")


# ── /gpu ──────────────────────────────────────────────────────────────────────
@router.message(Command("gpu"))
async def cmd_gpu(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f3ae checking GPU\u2026")
    try:
        from tools.resource_monitor import get_resource_snapshot, format_resource_html
        snap = await get_resource_snapshot(force=True)
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")
    except Exception as e:
        # Fallback to raw nvidia-smi
        try:
            from llm_client import run_shell_command
            out = await run_shell_command("nvidia-smi", timeout=10)
            await status_msg.edit_text(
                f"<pre>{html_mod.escape(out[:3000])}</pre>",
                parse_mode="HTML",
            )
        except Exception as e2:
            await status_msg.edit_text(
                f"GPU info unavailable: <code>{html_mod.escape(str(e2))}</code>",
                parse_mode="HTML",
            )


# ── /keys ──────────────────────────────────────────────────────────────────────
@router.message(Command("keys"))
async def cmd_keys(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(_key_status(), parse_mode="HTML")


# ── /models ────────────────────────────────────────────────────────────────────
@router.message(Command("models"))
async def cmd_models(msg: Message) -> None:
    if not is_allowed(msg):
        return
    import router as agents
    await msg.answer(agents.list_agents(), parse_mode="HTML")


# ── /resources — live RAM + GPU + local model policy ──────────────────────────
@router.message(Command("resources"))
async def cmd_resources(msg: Message) -> None:
    """Show live RAM, GPU VRAM, and whether local Ollama is currently allowed."""
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f4ca reading system resources\u2026")
    try:
        from tools.resource_monitor import get_resource_snapshot, format_resource_html
        # force=True to bypass cache and get a fresh reading
        snap = await get_resource_snapshot(force=True)
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"\u274c resource monitor error:\n<code>{html_mod.escape(str(e)[:400])}</code>\n\n"
            "Make sure <code>psutil</code> is installed: "
            "<code>pip install psutil pynvml</code>",
            parse_mode="HTML",
        )
