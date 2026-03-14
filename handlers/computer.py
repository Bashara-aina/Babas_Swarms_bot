"""Computer control handlers: /do /screen /open /click /type /key /cmd /install /upgrade."""
from __future__ import annotations

import asyncio
import html as html_mod
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

import computer_agent
from llm_client import run_shell_command
import llm_client
from .shared import (
    _last_screenshot,
    _keep_typing,
    _run_agent_loop,
    allowed_cb,
    is_allowed,
    screenshot_keyboard,
    send_chunked,
)

router = Router()


# ── /do — Agentic computer control ───────────────────────────────────────────
@router.message(Command("do"))
async def cmd_do(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/do").strip()
    if not task:
        await msg.answer(
            "usage: <code>/do &lt;task&gt;</code>\n\n"
            "i'll autonomously:\n"
            "• take screenshots to see what's on screen\n"
            "• click, type, open apps, run commands\n"
            "• loop until the task is done\n\n"
            "examples:\n"
            "<code>/do open whatsapp and send 'hello' to the first chat</code>\n"
            "<code>/do open vscode with swarm-bot folder</code>\n"
            "<code>/do check supabase dashboard and tell me table sizes</code>",
            parse_mode="HTML",
        )
        return
    await _run_agent_loop(msg, task)


# ── /screen ───────────────────────────────────────────────────────────────────
@router.message(Command("screen"))
async def cmd_screen(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("📸 grabbing screen…")
    try:
        path = await computer_agent.take_screenshot()
        if not path:
            await status_msg.edit_text(
                "screenshot failed. run this to debug:\n"
                "<code>echo $DISPLAY</code>\n"
                "If empty: <code>export DISPLAY=:0</code> then restart the bot.\n\n"
                "Also install: <code>sudo apt install scrot xdotool wmctrl xclip</code>",
                parse_mode="HTML",
            )
            return

        await status_msg.delete()
        _last_screenshot[msg.from_user.id] = path

        await msg.answer_photo(
            photo=FSInputFile(path),
            caption="🖥 desktop — tap Analyze or give me a task to do on screen",
            reply_markup=screenshot_keyboard(),
        )
    except Exception as e:
        await status_msg.edit_text(f"screenshot error: <code>{e}</code>", parse_mode="HTML")


# ── /open ─────────────────────────────────────────────────────────────────────
@router.message(Command("open"))
async def cmd_open(msg: Message) -> None:
    if not is_allowed(msg):
        return
    target = (msg.text or "").removeprefix("/open").strip()
    if not target:
        await msg.answer(
            "usage: <code>/open &lt;app or url&gt;</code>\n\n"
            "e.g. <code>/open whatsapp</code>, <code>/open https://supabase.com</code>, "
            "<code>/open vscode</code>, <code>/open ~/projects</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer(f"opening {target}…")
    if target.startswith("http") or target.startswith("www."):
        result = await computer_agent.open_url(target)
    elif target.startswith("~/") or target.startswith("/"):
        result = await computer_agent.open_folder_gui(target)
    else:
        result = await computer_agent.open_app(target)
    await status_msg.edit_text(result)


# ── /click ────────────────────────────────────────────────────────────────────
@router.message(Command("click"))
async def cmd_click(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) < 3:
        await msg.answer(
            "usage: <code>/click &lt;x&gt; &lt;y&gt; [left|right|double]</code>\n"
            "use /screen first to find coordinates",
            parse_mode="HTML",
        )
        return
    try:
        x, y = int(parts[1]), int(parts[2])
        button = parts[3] if len(parts) > 3 else "left"
        result = await computer_agent.mouse_click(x, y, button)
        await msg.answer(f"🖱 {result}")
    except (ValueError, IndexError):
        await msg.answer("bad coordinates — use integers: <code>/click 500 300</code>", parse_mode="HTML")


# ── /type ─────────────────────────────────────────────────────────────────────
@router.message(Command("type"))
async def cmd_type(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text_to_type = (msg.text or "").removeprefix("/type").strip()
    if not text_to_type:
        await msg.answer("usage: <code>/type &lt;text to type&gt;</code>", parse_mode="HTML")
        return
    result = await computer_agent.keyboard_type(text_to_type)
    await msg.answer(f"⌨️ {result}")


# ── /key ──────────────────────────────────────────────────────────────────────
@router.message(Command("key"))
async def cmd_key(msg: Message) -> None:
    if not is_allowed(msg):
        return
    combo = (msg.text or "").removeprefix("/key").strip()
    if not combo:
        await msg.answer(
            "usage: <code>/key &lt;combo&gt;</code>\n\n"
            "examples: <code>ctrl+t</code>  <code>alt+Tab</code>  "
            "<code>ctrl+shift+n</code>  <code>Return</code>  <code>super</code>",
            parse_mode="HTML",
        )
        return
    result = await computer_agent.key_press(combo)
    await msg.answer(f"⌨️ {result}")


# ── /cmd ──────────────────────────────────────────────────────────────────────
@router.message(Command("cmd"))
async def cmd_shell(msg: Message) -> None:
    if not is_allowed(msg):
        return
    cmd = (msg.text or "").removeprefix("/cmd").strip()
    if not cmd:
        await msg.answer(
            "usage: <code>/cmd &lt;shell command&gt;</code>\ne.g. <code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )
        return
    # Block obviously destructive patterns
    blocked = ["rm -rf /", "mkfs", ":(){:|:&};:", "> /dev/sda", "dd if=/dev/zero"]
    for b in blocked:
        if b in cmd:
            await msg.answer(f"blocked dangerous pattern: <code>{b}</code>", parse_mode="HTML")
            return

    status_msg = await msg.answer(f"<code>$ {cmd[:100]}</code>", parse_mode="HTML")
    output = await run_shell_command(cmd, timeout=60)
    await status_msg.delete()
    await msg.answer(
        f"<code>$ {cmd[:100]}</code>\n\n<pre>{output[:3800]}</pre>",
        parse_mode="HTML",
    )


# ── /install ──────────────────────────────────────────────────────────────────
@router.message(Command("install"))
async def cmd_install(msg: Message) -> None:
    if not is_allowed(msg):
        return
    packages_str = (msg.text or "").removeprefix("/install").strip()
    if not packages_str:
        await msg.answer(
            "usage: <code>/install &lt;package1&gt; &lt;package2&gt; ...</code>\n"
            "e.g. <code>/install playwright httpx rich</code>\n\n"
            "bot will install then restart automatically.",
            parse_mode="HTML",
        )
        return

    packages = packages_str.split()
    status_msg = await msg.answer(
        f"📦 installing: <code>{', '.join(packages)}</code>\n(this may take a moment…)",
        parse_mode="HTML",
    )

    result = await computer_agent.install_packages(packages)

    await status_msg.edit_text(
        f"📦 install output:\n<pre>{result[:2000]}</pre>\n\n🔄 restarting bot…",
        parse_mode="HTML",
    )

    await asyncio.sleep(2)

    await msg.answer("back in a sec 👋")
    computer_agent.restart_bot()


# ── /upgrade ──────────────────────────────────────────────────────────────────
@router.message(Command("upgrade"))
async def cmd_upgrade(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("⬆️ pulling latest from GitHub…")

    result = await computer_agent.upgrade_from_git()
    await status_msg.edit_text(
        f"<b>git pull</b>\n<pre>{result}</pre>\n\n🔄 restarting…",
        parse_mode="HTML",
    )

    if "Already up to date" in result:
        await status_msg.edit_text(
            f"<b>git pull</b>\n<pre>{result}</pre>\nalready up to date, no restart needed.",
            parse_mode="HTML",
        )
        return

    await asyncio.sleep(2)
    await msg.answer("restarting with updates 🔄")
    computer_agent.restart_bot()


# ── Keyboard button shortcuts ─────────────────────────────────────────────────
@router.message(F.text == "🖥 Do task")
async def kbd_do_hint(msg: Message) -> None:
    if is_allowed(msg):
        await msg.answer(
            "tell me what to do on the computer:\n\n"
            "just type your task naturally, or use <code>/do &lt;task&gt;</code>\n\n"
            "examples:\n"
            "• open whatsapp\n"
            "• check what's in my swarm-bot folder\n"
            "• take a screenshot and tell me what's open\n"
            "• open supabase dashboard",
            parse_mode="HTML",
        )


@router.message(F.text == "📸 Screenshot")
async def kbd_screenshot(msg: Message) -> None:
    if is_allowed(msg):
        await cmd_screen(msg)


@router.message(F.text == "⚡ Shell")
async def kbd_shell_hint(msg: Message) -> None:
    if is_allowed(msg):
        await msg.answer(
            "type: <code>/cmd &lt;command&gt;</code>\ne.g. <code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )


# ── Callbacks ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("fb:"))
async def cb_feedback(cb: CallbackQuery) -> None:
    action = cb.data.split(":")[1]
    responses = {
        "good":  "👍 nice",
        "retry": "re-send your message to retry",
        "info":  "provider shown in button label",
    }
    await cb.answer(responses.get(action, "ok"))


@router.callback_query(F.data == "screen:analyze")
async def cb_analyze_screenshot(cb: CallbackQuery) -> None:
    if not allowed_cb(cb):
        await cb.answer("not authorized")
        return

    path = _last_screenshot.get(cb.from_user.id)
    if not path or not Path(path).exists():
        await cb.answer("screenshot expired — grab a new one with /screen")
        return

    await cb.answer("analyzing…")
    status_msg = await cb.message.answer("🔍 analyzing screen…")
    typing_task = asyncio.create_task(_keep_typing(cb.message))

    try:
        analysis, model_used = await llm_client.analyze_screenshot(
            path,
            question=(
                "Describe everything you see on this screen in detail: "
                "which applications are open, what content is visible, "
                "any errors/warnings, what the user appears to be working on."
            )
        )
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(cb.message, analysis, model_used=model_used)

        try:
            Path(path).unlink(missing_ok=True)
            del _last_screenshot[cb.from_user.id]
        except Exception:
            pass
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"analysis failed: <code>{e}</code>", parse_mode="HTML")


@router.callback_query(F.data == "screen:do")
async def cb_screen_do(cb: CallbackQuery) -> None:
    if not allowed_cb(cb):
        await cb.answer("not authorized")
        return
    await cb.answer()
    await cb.message.answer(
        "what do you want me to do on screen?\n\n"
        "just reply with your task, or use <code>/do &lt;task&gt;</code>",
        parse_mode="HTML",
    )
