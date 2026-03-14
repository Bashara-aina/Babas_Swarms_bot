"""Self-upgrade Telegram handler.

Commands:
  /upgrade <request>   — natural language upgrade request
  /upgrade_status      — show last upgrade result
  /upgrade_rollback    — rollback last upgrade
  /upgrade_history     — list all upgrades

Examples:
  /upgrade add a /dashboard command that reads data from a CSV and sends a chart
  /upgrade add a /translate command that translates any text to English
  /upgrade add a /weather command using wttr.in API
"""
from __future__ import annotations

import html as html_mod
import logging
import time
from pathlib import Path
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed, send_chunked

logger = logging.getLogger(__name__)
router = Router()

_last_result = None    # UpgradeResult from last run
_upgrade_history = []  # list of dicts


@router.message(Command("upgrade"))
async def cmd_upgrade(msg: Message) -> None:
    """Trigger a self-upgrade from natural language."""
    if not is_allowed(msg):
        return

    request = (msg.text or "").removeprefix("/upgrade").strip()
    if not request:
        await msg.answer(
            "🧠 <b>Legion Self-Upgrade</b>\n\n"
            "Tell me what feature to add and I'll implement it myself:\n\n"
            "Examples:\n"
            "<code>/upgrade add a /dashboard command that reads CSV and makes a chart</code>\n"
            "<code>/upgrade add /translate command for any text to English</code>\n"
            "<code>/upgrade add /weather command using wttr.in</code>\n"
            "<code>/upgrade add /stocks command showing live price chart</code>\n\n"
            "⚠️ All generated code is syntax-checked and safety-scanned before execution.",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(
        f"🔄 <b>Upgrading Legion…</b>\n\n"
        f"Request: <i>{html_mod.escape(request[:200])}</i>\n\n"
        f"⏳ Generating code…",
        parse_mode="HTML",
    )

    step_log = []
    step_count = 0

    async def notify(text: str) -> None:
        nonlocal step_count
        step_count += 1
        step_log.append(text)
        try:
            # Show last 4 steps in the status message
            recent = step_log[-4:]
            display = "\n".join(f"<code>[{i+1}]</code> {html_mod.escape(l)}" for i, l in enumerate(recent))
            await status_msg.edit_text(
                f"🔄 <b>Upgrading…</b> (step {step_count})\n\n{display}",
                parse_mode="HTML",
            )
        except Exception:
            pass

    try:
        from core.self_upgrade import SelfUpgradeEngine
        engine = SelfUpgradeEngine(
            bot_root=Path("."),
            notify_cb=notify,
        )
        result = await engine.upgrade(request, user_id=msg.from_user.id)

        global _last_result
        _last_result = result
        _upgrade_history.append({
            "ts": time.time(),
            "request": request[:200],
            "feature": result.feature_name,
            "success": result.success,
            "files": result.files_written,
            "deps": result.deps_installed,
            "method": result.reload_method,
            "error": result.error,
        })

        if result.success:
            files_str = "\n".join(f"  • <code>{f}</code>" for f in result.files_written)
            deps_str = ", ".join(f"<code>{d}</code>" for d in result.deps_installed) or "none"
            await status_msg.edit_text(
                f"✅ <b>Upgrade complete!</b>\n\n"
                f"<b>Feature:</b> {html_mod.escape(result.feature_name)}\n\n"
                f"<b>Files written:</b>\n{files_str}\n\n"
                f"<b>Dependencies:</b> {deps_str}\n"
                f"<b>Reload method:</b> <code>{result.reload_method}</code>\n\n"
                f"💡 New commands are live immediately. No reconnect needed.",
                parse_mode="HTML",
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Upgrade failed</b>\n\n"
                f"{html_mod.escape(result.error[:400])}\n\n"
                f"Previous version restored automatically.",
                parse_mode="HTML",
            )

    except Exception as e:
        logger.error("Upgrade handler error: %s", e)
        await status_msg.edit_text(
            f"❌ <b>Upgrade error:</b>\n<code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("upgrade_status"))
async def cmd_upgrade_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    if not _last_result:
        await msg.answer("No upgrades run yet. Use /upgrade <request>")
        return
    r = _last_result
    status = "✅ Success" if r.success else f"❌ Failed: {r.error[:100]}"
    files = "\n".join(f"  • {f}" for f in r.files_written)
    await msg.answer(
        f"<b>Last Upgrade:</b> {html_mod.escape(r.feature_name)}\n"
        f"Status: {status}\n"
        f"Files:\n{files}\n"
        f"Deps: {', '.join(r.deps_installed) or 'none'}\n"
        f"Method: {r.reload_method}",
        parse_mode="HTML",
    )


@router.message(Command("upgrade_history"))
async def cmd_upgrade_history(msg: Message) -> None:
    if not is_allowed(msg):
        return
    if not _upgrade_history:
        await msg.answer("No upgrade history yet.")
        return
    lines = ["<b>📜 Upgrade History</b>\n"]
    for i, entry in enumerate(reversed(_upgrade_history[-10:]), 1):
        ts = time.strftime("%m/%d %H:%M", time.localtime(entry["ts"]))
        icon = "✅" if entry["success"] else "❌"
        lines.append(
            f"{icon} <code>{ts}</code> <b>{html_mod.escape(entry['feature'])}</b>\n"
            f"   {html_mod.escape(entry['request'][:80])}"
        )
    await msg.answer("\n".join(lines), parse_mode="HTML")
