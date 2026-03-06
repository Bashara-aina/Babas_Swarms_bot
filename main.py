"""LegionSwarm — Autonomous Desktop AI via Telegram.

Slash Commands (optional — natural language works too):
    /start          — Help menu with interactive buttons
    /run <task>     — Auto-route to best agent
    /agent <n> <t>  — Force a specific agent
    /thread <name>  — Switch conversation thread
    /threads        — List active threads
    /context        — Show current thread history
    /scrape <url>   — Scrape page text
    /shot <url>     — Screenshot a URL
    /desktop        — Screenshot the local desktop
    /screen         — OCR-read current desktop text
    /click <text>   — Click UI element by visible text
    /read <path>    — Read a file from workspace
    /cmd <shell>    — Run a shell command
    /git            — Git status of workspace
    /models         — Show agent roster
    /confirm yes|no <id>  — Approve/deny queued action
    /monitors       — List active monitors
    /cancel <id>    — Cancel a monitor
    /pending        — Show pending confirmations
    /stats          — Performance + usage report
    /circuits       — Circuit breaker status
    /feedback <id> good|bad [comment]  — Rate a response
    /usage          — Daily API usage + cost report
    /keyboard       — Toggle persistent keyboard shortcuts

Natural Language Examples:
    "debug this pytorch error: ..."
    "what's on my screen right now?"
    "click on the terminal"
    "read /home/newadmin/swarm-bot/agents.py"
    "monitor my training every 5 minutes"
    [send voice message] → auto-transcribed
    [upload PDF] → auto-extracted and analyzed with quick action buttons
    [upload screenshot] → auto-analyzed by vision model with quick actions
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    Message,
    Voice,
    Document,
    PhotoSize,
)
from dotenv import load_dotenv

import agents
import computer_control
import interpreter_bridge
import multimodal_processor
import playwright_agent
import task_orchestrator
import vscode_bridge
import telegram_ui
import formatters
import streaming_response
import progress_tracker
import notifications
import callback_handlers

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Secrets ────────────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
_raw_uid = os.getenv("ALLOWED_USER_ID", "")
ALLOWED_USER_ID: int = int(_raw_uid) if _raw_uid.isdigit() else 0

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")
if not ALLOWED_USER_ID:
    raise RuntimeError("ALLOWED_USER_ID not set or invalid in .env")

# ── Bot Setup ──────────────────────────────────────────────────────────────────

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Per-user active thread tracking
current_thread: dict[int, str] = {}

# Per-user keyboard preference
keyboard_enabled: dict[int, bool] = {}

# Notification manager
notif_manager = notifications.NotificationManager(bot)

# Register all callback handlers
callback_handlers.register_callback_handlers(dp, bot)

# ── Auth Guard ─────────────────────────────────────────────────────────────────

def _authorized(message: Message) -> bool:
    """Return True only if sender matches ALLOWED_USER_ID."""
    return message.from_user is not None and message.from_user.id == ALLOWED_USER_ID


async def _deny(message: Message) -> None:
    """Silently log unauthorized access — no reply."""
    logger.warning(
        "Unauthorized access from user_id=%s",
        message.from_user and message.from_user.id,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _send_chunks(message: Message, text: str, agent: str = None) -> None:
    """Send text in ≤4000-char HTML chunks with context bar.

    Args:
        message: Source message (for chat context).
        text: Full output to send.
        agent: Optional agent name for context.
    """
    chunks = interpreter_bridge.chunk_output(text)
    uid = message.from_user.id
    thread_id = current_thread.get(uid)
    
    context_bar = ""
    if thread_id:
        turn_count = agents.get_thread_turn_count(thread_id)
        context_bar = f"\n\n<i>📍 Thread: {thread_id} • Turn {turn_count}</i>"
    
    for i, chunk in enumerate(chunks):
        if agent and i == 0:
            formatted = f"<b>{agent.upper()}</b>\n\n<pre>{chunk}</pre>{context_bar if i == len(chunks) - 1 else ''}"
        else:
            formatted = f"<pre>{chunk}</pre>{context_bar if i == len(chunks) - 1 else ''}"
        await message.answer(formatted, parse_mode="HTML")


async def _notify(message: Message, text: str) -> None:
    """Send a plain HTML notification (used by monitors).

    Args:
        message: Source message for chat context.
        text: Message to send.
    """
    await message.answer(text, parse_mode="HTML")


async def _send_desktop_screenshot(message: Message) -> None:
    """Take and send current desktop screenshot.

    Args:
        message: Source message.
    """
    status_msg = await message.answer("📸 Taking desktop screenshot…")
    try:
        png_bytes = await computer_control.desktop_screenshot()
        await message.answer_photo(
            BufferedInputFile(png_bytes, filename="desktop.png"),
            caption="Current desktop 🖥️",
        )
        await status_msg.delete()
    except Exception as exc:
        await status_msg.edit_text(f"❌ Screenshot failed: {exc}", parse_mode="HTML")


def _detect_intent(text: str) -> dict:
    """Classify natural language message into an action + content.

    Returns:
        dict with keys 'action' and 'content'.
    """
    t = text.lower().strip()

    # Thread switching
    for pattern in [r"switch to (\w+)", r"use thread (\w+)", r"work on (\w+)", r"change to (\w+) thread"]:
        m = re.search(pattern, t)
        if m:
            return {"action": "thread", "content": m.group(1)}

    if any(kw in t for kw in ["show threads", "list threads", "my threads"]):
        return {"action": "threads", "content": ""}
    if any(kw in t for kw in ["show context", "thread history", "what did we discuss"]):
        return {"action": "context", "content": ""}
    if any(kw in t for kw in ["show models", "list agents", "what agents"]):
        return {"action": "models", "content": ""}

    # Desktop control
    if any(kw in t for kw in ["what's on my screen", "what is on screen", "describe my screen", "show my screen"]):
        return {"action": "analyze_screen", "content": text}
    if any(kw in t for kw in ["desktop screenshot", "screenshot my screen", "take a screenshot of desktop"]):
        return {"action": "desktop_shot", "content": ""}
    if any(kw in t for kw in ["read my screen", "ocr screen", "what text is on screen"]):
        return {"action": "read_screen", "content": ""}

    # Click element
    click_m = re.search(r"click (?:on )?['\"]?(.+?)['\"]?$", t)
    if click_m:
        return {"action": "click", "content": click_m.group(1).strip()}

    # VSCode / file operations
    read_m = re.search(r"read (?:file )?([/~]?\S+\.\w+)", text)
    if read_m:
        return {"action": "read_file", "content": read_m.group(1)}
    if any(kw in t for kw in ["git status", "git log", "show git"]):
        return {"action": "git", "content": ""}
    if any(kw in t for kw in ["terminal output", "what's in terminal", "show terminal"]):
        return {"action": "terminal", "content": ""}

    # Monitor
    monitor_m = re.search(r"monitor (.+?) every (\d+) min", t)
    if monitor_m:
        return {"action": "monitor", "content": text}

    # Confirm/deny
    if t.startswith("confirm yes") or t.startswith("yes confirm"):
        parts = t.split()
        aid = parts[-1] if len(parts) > 2 else ""
        return {"action": "confirm_yes", "content": aid}
    if t.startswith("confirm no") or t.startswith("no confirm"):
        parts = t.split()
        aid = parts[-1] if len(parts) > 2 else ""
        return {"action": "confirm_no", "content": aid}

    # URL operations
    url_m = re.search(r"(https?://\S+)", text)
    if url_m:
        if any(kw in t for kw in ["scrape", "extract text", "get text from"]):
            return {"action": "scrape", "content": url_m.group(1)}
        if any(kw in t for kw in ["screenshot", "capture", "shot of"]):
            return {"action": "shot", "content": url_m.group(1)}

    if any(kw in t for kw in ["help", "what can you do", "commands"]):
        return {"action": "help", "content": ""}

    if any(kw in t for kw in ["show stats", "performance stats", "usage stats", "/stats"]):
        return {"action": "stats", "content": ""}

    if any(kw in t for kw in ["circuit status", "circuit breaker", "/circuits"]):
        return {"action": "circuits", "content": ""}

    if any(kw in t for kw in ["usage report", "api usage", "cost report", "/usage"]):
        return {"action": "usage", "content": ""}

    return {"action": "run", "content": text}


# ── Slash Command Handlers ─────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Show interactive main menu with buttons."""
    if not _authorized(message):
        await _deny(message)
        return

    uid = message.from_user.id
    keyboard = telegram_ui.TelegramUI.power_user_keyboard() if keyboard_enabled.get(uid) else None
    
    await message.answer(
        "🤖 <b>LegionSwarm 10/10</b>\n\n"
        "Your autonomous AI assistant is ready!\n\n"
        "<b>Quick Start:</b>\n"
        "  • Tap buttons below for instant actions\n"
        "  • Send voice messages for transcription\n"
        "  • Upload files for automatic analysis\n"
        "  • Just type naturally - I understand\n\n"
        f"<b>Available Agents:</b> {', '.join(agents.AGENT_MODELS.keys())}",
        parse_mode="HTML",
        reply_markup=telegram_ui.TelegramUI.main_menu(),
    )


@dp.message(Command("keyboard"))
async def cmd_keyboard(message: Message) -> None:
    """Toggle persistent keyboard shortcuts."""
    if not _authorized(message):
        await _deny(message)
        return
    
    uid = message.from_user.id
    keyboard_enabled[uid] = not keyboard_enabled.get(uid, False)
    
    if keyboard_enabled[uid]:
        await message.answer(
            "⌨️ <b>Keyboard Shortcuts Enabled</b>\n\n"
            "Quick action buttons are now visible at the bottom of your chat.",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.power_user_keyboard(),
        )
    else:
        await message.answer(
            "⌨️ <b>Keyboard Shortcuts Disabled</b>\n\n"
            "Use /start to access the interactive menu.",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.remove_keyboard(),
        )


@dp.message(Command("models"))
async def cmd_models(message: Message) -> None:
    """Show agent roster with force selection buttons."""
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(
        agents.list_agents() + "\n\n<i>Tap below to force an agent:</i>",
        parse_mode="HTML",
        reply_markup=telegram_ui.TelegramUI.agent_selector(),
    )


@dp.message(Command("desktop"))
async def cmd_desktop(message: Message) -> None:
    """Take and send desktop screenshot."""
    if not _authorized(message):
        await _deny(message)
        return
    await _send_desktop_screenshot(message)


@dp.message(Command("screen"))
async def cmd_screen(message: Message) -> None:
    """OCR-read current desktop text."""
    if not _authorized(message):
        await _deny(message)
        return
    status_msg = await message.answer("🔍 Reading screen text via OCR…")
    try:
        text = await computer_control.read_screen()
        await status_msg.delete()
        await _send_chunks(message, text or "(no text detected)")
    except Exception as exc:
        await status_msg.edit_text(f"❌ OCR failed: {exc}", parse_mode="HTML")


@dp.message(Command("click"))
async def cmd_click(message: Message) -> None:
    """Click a UI element by visible text.

    Usage: /click <text on screen>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/click &lt;text&gt;</code>", parse_mode="HTML")
        return
    target = args[1].strip()
    status_msg = await message.answer(f"🎯 Looking for <code>{target}</code> on screen…", parse_mode="HTML")
    try:
        found = await computer_control.click_on(target)
        if found:
            await status_msg.edit_text(f"✅ Clicked: <code>{target}</code>", parse_mode="HTML")
        else:
            await status_msg.edit_text(f"❌ Element not found: <code>{target}</code>", parse_mode="HTML")
    except Exception as exc:
        await status_msg.edit_text(f"❌ Click failed: {exc}", parse_mode="HTML")


@dp.message(Command("read"))
async def cmd_read_file(message: Message) -> None:
    """Read a file from the workspace.

    Usage: /read <path>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/read &lt;path&gt;</code>", parse_mode="HTML")
        return
    path = args[1].strip()
    status_msg = await message.answer(f"📖 Reading <code>{path}</code>…", parse_mode="HTML")
    try:
        content = await vscode_bridge.read_file(path)
        await status_msg.delete()
        formatted = formatters.ResponseFormatter.format_code_response(content, "text")
        await message.answer(formatted, parse_mode="HTML")
    except FileNotFoundError:
        await status_msg.edit_text(f"❌ File not found: <code>{path}</code>", parse_mode="HTML")
    except Exception as exc:
        await status_msg.edit_text(f"❌ Read error: {exc}", parse_mode="HTML")


@dp.message(Command("cmd"))
async def cmd_shell(message: Message) -> None:
    """Run a shell command on this PC.

    Usage: /cmd <shell command>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/cmd &lt;command&gt;</code>", parse_mode="HTML")
        return
    cmd = args[1].strip()

    # Destructive command → queue for confirmation
    if computer_control.is_destructive(cmd):
        async def _run() -> str:
            return await vscode_bridge.run_command(cmd)

        action_id = task_orchestrator.queue_confirmation(
            f"Run: <code>{cmd}</code>", _run
        )
        await message.answer(
            f"⚠️ <b>Destructive Command Detected</b>\n\n"
            f"<code>{cmd}</code>\n\n"
            f"Confirm to proceed:",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.confirmation_buttons(action_id),
        )
        return

    status_msg = await message.answer(f"⚡ Running: <code>{cmd}</code>…", parse_mode="HTML")
    try:
        output = await vscode_bridge.run_command(cmd)
        await status_msg.delete()
        await _send_chunks(message, output)
    except Exception as exc:
        await status_msg.edit_text(f"❌ Command error: {exc}", parse_mode="HTML")


@dp.message(Command("git"))
async def cmd_git(message: Message) -> None:
    """Show workspace git status."""
    if not _authorized(message):
        await _deny(message)
        return
    status_msg = await message.answer("🔄 Fetching git status…")
    try:
        status = await vscode_bridge.git_status()
        await status_msg.delete()
        await _send_chunks(message, status)
    except Exception as exc:
        await status_msg.edit_text(f"❌ Git error: {exc}", parse_mode="HTML")


@dp.message(Command("thread"))
async def cmd_thread(message: Message) -> None:
    """Switch to a conversation thread.

    Usage: /thread <name>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        # Show thread selector
        thread_list = agents.get_all_threads()
        if thread_list:
            await message.answer(
                "📌 <b>Select a Thread</b>\n\nOr type: <code>/thread your_name</code>",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.thread_selector(thread_list),
            )
        else:
            await message.answer(
                "No active threads. Start one by typing: <code>/thread project_name</code>",
                parse_mode="HTML"
            )
        return
    
    thread_id = args[1].strip().lower().replace(" ", "_")
    current_thread[message.from_user.id] = thread_id
    
    turns = agents.get_thread_turn_count(thread_id)
    ctx = agents.get_thread_context(thread_id, last_n=1)
    
    formatted = formatters.ResponseFormatter.format_thread_summary(
        thread_id, turns, ctx[:100] if ctx else "(new thread)"
    )
    await message.answer(formatted, parse_mode="HTML")


@dp.message(Command("threads"))
async def cmd_threads(message: Message) -> None:
    """List active threads with interactive buttons."""
    if not _authorized(message):
        await _deny(message)
        return
    
    thread_list = agents.get_all_threads()
    if not thread_list:
        await message.answer("📌 No active threads yet.", parse_mode="HTML")
        return
    
    await message.answer(
        agents.list_threads(),
        parse_mode="HTML",
        reply_markup=telegram_ui.TelegramUI.thread_selector(thread_list),
    )


@dp.message(Command("context"))
async def cmd_context(message: Message) -> None:
    """Show current thread history."""
    if not _authorized(message):
        await _deny(message)
        return
    uid = message.from_user.id
    if uid not in current_thread:
        await message.answer("No active thread. Use /thread to create one.", parse_mode="HTML")
        return
    tid = current_thread[uid]
    ctx = agents.get_thread_context(tid, last_n=5)
    turns = agents.get_thread_turn_count(tid)
    
    if not ctx:
        await message.answer(f"📌 Thread <b>{tid}</b> is empty.", parse_mode="HTML")
    else:
        formatted = formatters.ResponseFormatter.format_thread_summary(tid, turns, ctx)
        await message.answer(formatted, parse_mode="HTML")


@dp.message(Command("run"))
async def cmd_run(message: Message) -> None:
    """Auto-detect agent and run task with streaming.

    Usage: /run <task>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/run &lt;task&gt;</code>", parse_mode="HTML")
        return
    await _execute_task(message, args[1].strip())


@dp.message(Command("agent"))
async def cmd_agent(message: Message) -> None:
    """Force a specific agent.

    Usage: /agent <name> <task>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            f"Usage: <code>/agent &lt;name&gt; &lt;task&gt;</code>\n\n"
            f"<b>Available agents:</b>\n{', '.join(agents.AGENT_MODELS.keys())}",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.agent_selector(),
        )
        return

    agent_key = args[1].strip().lower()
    task = args[2].strip()
    model = agents.get_model(agent_key)
    if model is None:
        await message.answer(
            f"❌ Unknown agent: <b>{agent_key}</b>\n\n"
            f"Available: {', '.join(agents.AGENT_MODELS.keys())}",
            parse_mode="HTML"
        )
        return

    uid = message.from_user.id
    tid = current_thread.get(uid)
    full_task = task
    if tid:
        ctx = agents.get_thread_context(tid)
        if ctx:
            full_task = f"{ctx}\n\nCurrent task: {task}"

    # Use streaming response
    streamer = streaming_response.StreamingResponseManager(bot)
    try:
        await streamer.stream_response(
            message.chat.id,
            interpreter_bridge.run_task_streaming(model, full_task, agent_key),
            agent_key
        )
    except Exception as exc:
        formatted = formatters.ResponseFormatter.format_error_analysis(str(exc), "Check logs for details")
        await message.answer(formatted, parse_mode="HTML")
    
    if tid:
        agents.add_to_thread(tid, agent_key, task, "(streamed response)")


@dp.message(Command("scrape"))
async def cmd_scrape(message: Message) -> None:
    """Scrape page text from a URL.

    Usage: /scrape <url>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/scrape &lt;url&gt;</code>", parse_mode="HTML")
        return
    url = args[1].strip()
    status_msg = await message.answer(f"🌐 Scraping <code>{url}</code>…", parse_mode="HTML")
    try:
        text = await playwright_agent.scrape(url)
        await status_msg.delete()
        await _send_chunks(message, text)
    except Exception as exc:
        await status_msg.edit_text(f"❌ Scraping failed: {exc}", parse_mode="HTML")


@dp.message(Command("shot"))
async def cmd_shot(message: Message) -> None:
    """Screenshot a URL.

    Usage: /shot <url>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/shot &lt;url&gt;</code>", parse_mode="HTML")
        return
    url = args[1].strip()
    status_msg = await message.answer(f"📸 Screenshotting <code>{url}</code>…", parse_mode="HTML")
    tmp_path: Path | None = None
    try:
        tmp_path = await playwright_agent.screenshot(url)
        await message.answer_photo(
            BufferedInputFile(tmp_path.read_bytes(), filename="screenshot.png"),
            caption=f"📸 {url}",
        )
        await status_msg.delete()
    except Exception as exc:
        await status_msg.edit_text(f"❌ Screenshot failed: {exc}", parse_mode="HTML")
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


@dp.message(Command("confirm"))
async def cmd_confirm(message: Message) -> None:
    """Approve or deny a queued destructive action.

    Usage: /confirm yes <id> | /confirm no <id>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split()
    if len(args) < 3:
        pending = task_orchestrator.list_pending()
        await message.answer(
            f"Usage: <code>/confirm yes|no &lt;id&gt;</code>\n\n{pending}",
            parse_mode="HTML",
        )
        return

    verdict = args[1].lower()
    action_id = args[2]

    if verdict in ("yes", "y"):
        result = await task_orchestrator.confirm_action(action_id)
        await _send_chunks(message, result)
    elif verdict in ("no", "n"):
        result = task_orchestrator.deny_action(action_id)
        await message.answer(result, parse_mode="HTML")
    else:
        await message.answer(
            "Usage: <code>/confirm yes &lt;id&gt;</code> or <code>/confirm no &lt;id&gt;</code>",
            parse_mode="HTML",
        )


@dp.message(Command("pending"))
async def cmd_pending(message: Message) -> None:
    """List pending confirmations."""
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(task_orchestrator.list_pending(), parse_mode="HTML")


@dp.message(Command("monitors"))
async def cmd_monitors(message: Message) -> None:
    """List active monitoring tasks."""
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(task_orchestrator.list_monitors(), parse_mode="HTML")


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Cancel an active monitor.

    Usage: /cancel <task_id>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(task_orchestrator.list_monitors(), parse_mode="HTML")
        return
    result = task_orchestrator.cancel_monitor(args[1])
    await message.answer(result, parse_mode="HTML")


# ── Multi-Modal Input Handlers ─────────────────────────────────────────────────

@dp.message(F.voice)
async def handle_voice(message: Message) -> None:
    """Transcribe voice message and process as text task with progress."""
    if not _authorized(message):
        await _deny(message)
        return

    status_msg = await message.answer("🎤 Transcribing voice message…")
    try:
        voice: Voice = message.voice
        file = await bot.get_file(voice.file_id)
        file_bytes = await bot.download_file(file.file_path)
        audio_bytes = file_bytes.read()

        text = await multimodal_processor.transcribe_voice(audio_bytes, extension=".ogg")
        await status_msg.edit_text(
            f"🎤 <b>Transcribed:</b>\n\n<i>{text}</i>\n\n⚡ Processing…",
            parse_mode="HTML"
        )
        await _execute_task(message, text)

    except RuntimeError as exc:
        await status_msg.edit_text(f"❌ Transcription unavailable: {exc}", parse_mode="HTML")
    except Exception as exc:
        logger.exception("Voice handler error: %s", exc)
        await status_msg.edit_text(f"❌ Voice error: {exc}", parse_mode="HTML")


@dp.message(F.document)
async def handle_document(message: Message) -> None:
    """Extract document text and provide quick action buttons."""
    if not _authorized(message):
        await _deny(message)
        return

    doc: Document = message.document
    mime = doc.mime_type or ""
    fname = doc.file_name or ""
    file_size = doc.file_size / 1024  # KB

    status_msg = await message.answer(
        f"📄 <b>Processing Document</b>\n\n"
        f"<b>Name:</b> {fname}\n"
        f"<b>Size:</b> {file_size:.1f} KB\n\n"
        f"Extracting content…",
        parse_mode="HTML"
    )

    try:
        file = await bot.get_file(doc.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        raw = file_bytes_io.read()

        extracted, label = await multimodal_processor.process_document(raw, mime, fname)

        if not extracted:
            await status_msg.edit_text(
                f"❌ Cannot process {label}. Supported: PDF, DOCX, TXT",
                parse_mode="HTML"
            )
            return

        # Store for quick actions
        callback_handlers.file_states[doc.file_id] = {
            "text": extracted,
            "filename": fname,
        }

        # Show quick action buttons
        await status_msg.edit_text(
            f"📄 <b>{label} Ready</b>\n\n"
            f"<b>Name:</b> {fname}\n"
            f"<b>Size:</b> {file_size:.1f} KB\n"
            f"<b>Extracted:</b> {len(extracted):,} characters\n\n"
            f"What would you like me to do with it?",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.document_actions(doc.file_id),
        )

        # Add to thread if one is active
        uid = message.from_user.id
        tid = current_thread.get(uid)
        if tid:
            agents.add_to_thread(tid, "document", f"Uploaded: {fname}", extracted[:300])

    except Exception as exc:
        logger.exception("Document handler error: %s", exc)
        await status_msg.edit_text(f"❌ Document error: {exc}", parse_mode="HTML")


@dp.message(F.photo)
async def handle_photo(message: Message) -> None:
    """Analyze uploaded photo with quick action buttons."""
    if not _authorized(message):
        await _deny(message)
        return

    # Get highest-resolution version
    photo: PhotoSize = message.photo[-1]
    file_size = photo.file_size / 1024  # KB
    caption = message.caption or "Describe this image in detail."

    status_msg = await message.answer(
        f"📷 <b>Image Received</b>\n\n"
        f"<b>Size:</b> {file_size:.1f} KB\n\n"
        f"What would you like me to do?",
        parse_mode="HTML"
    )

    try:
        file = await bot.get_file(photo.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        image_bytes = file_bytes_io.read()

        # Store for quick actions
        callback_handlers.file_states[photo.file_id] = {
            "bytes": image_bytes,
        }

        # Show quick action buttons
        await status_msg.edit_text(
            f"📷 <b>Image Ready</b>\n\n"
            f"<b>Size:</b> {file_size:.1f} KB\n\n"
            f"Choose an action:",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.photo_actions(photo.file_id),
        )

    except Exception as exc:
        logger.exception("Photo handler error: %s", exc)
        await status_msg.edit_text(f"❌ Image error: {exc}", parse_mode="HTML")


# ── Natural Language Handler ───────────────────────────────────────────────────

@dp.message(F.text)
async def handle_natural(message: Message) -> None:
    """Route natural language messages with enhanced UX."""
    if not _authorized(message):
        await _deny(message)
        return

    text = (message.text or "").strip()
    if not text:
        return

    # Handle power keyboard buttons
    keyboard_shortcuts = {
        "🐛 Debug": "debug",
        "💻 Code": "code",
        "📊 Analyze": "analyze",
        "💡 Explain": "explain",
        "🖥️ Desktop": "desktop",
        "📌 Threads": "threads",
        "📈 Stats": "stats",
        "⚙️ Settings": "settings",
    }
    
    if text in keyboard_shortcuts:
        action = keyboard_shortcuts[text]
        if action == "desktop":
            await _send_desktop_screenshot(message)
        elif action == "threads":
            await cmd_threads(message)
        elif action == "stats":
            await cmd_stats(message)
        elif action == "settings":
            await message.answer(
                "⚙️ <b>Settings</b>\n\nConfigure your preferences:",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.settings_menu(),
            )
        else:
            prompts = {
                "debug": "🐛 <b>Debug Mode</b>\n\nSend your error or code issue.",
                "code": "💻 <b>Coding Mode</b>\n\nDescribe what to build.",
                "analyze": "📊 <b>Analysis Mode</b>\n\nUpload data or describe analysis needed.",
                "explain": "💡 <b>Explanation Mode</b>\n\nWhat do you want explained?",
            }
            await message.answer(prompts.get(action, "Ready."), parse_mode="HTML")
        return

    intent = _detect_intent(text)
    action = intent["action"]
    content = intent["content"]
    uid = message.from_user.id

    if action == "thread":
        tid = content.lower().replace(" ", "_")
        current_thread[uid] = tid
        turns = agents.get_thread_turn_count(tid)
        ctx = agents.get_thread_context(tid, last_n=1)
        formatted = formatters.ResponseFormatter.format_thread_summary(
            tid, turns, ctx[:100] if ctx else "(new thread)"
        )
        await message.answer(formatted, parse_mode="HTML")

    elif action == "threads":
        thread_list = agents.get_all_threads()
        if thread_list:
            await message.answer(
                agents.list_threads(),
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.thread_selector(thread_list),
            )
        else:
            await message.answer("📌 No active threads yet.", parse_mode="HTML")

    elif action == "context":
        await cmd_context(message)

    elif action == "models":
        await cmd_models(message)

    elif action == "desktop_shot":
        await _send_desktop_screenshot(message)

    elif action == "analyze_screen":
        status_msg = await message.answer("👁️ Analyzing your screen…")
        try:
            result = await computer_control.analyze_screen(content or "What is visible on screen?")
            await status_msg.delete()
            await _send_chunks(message, result, "vision")
        except Exception as exc:
            await status_msg.edit_text(f"❌ Screen analysis error: {exc}", parse_mode="HTML")

    elif action == "read_screen":
        await cmd_screen(message)

    elif action == "click":
        await cmd_click(message)

    elif action == "read_file":
        await cmd_read_file(message)

    elif action == "git":
        await cmd_git(message)

    elif action == "terminal":
        output = await vscode_bridge.get_terminal_output()
        await _send_chunks(message, output)

    elif action == "monitor":
        # Parse "monitor X every N minutes"
        m = re.search(r"monitor (.+?) every (\d+) min", text, re.IGNORECASE)
        if m:
            desc = m.group(1).strip()
            interval = int(m.group(2)) * 60

            async def _monitor_fn() -> str:
                return await vscode_bridge.run_command(f"echo 'Monitoring: {desc}'")

            async def _notify_fn(msg: str) -> None:
                await message.answer(msg, parse_mode="HTML")

            task_id = await task_orchestrator.start_monitor(
                desc, interval, _monitor_fn, _notify_fn
            )
            await message.answer(
                f"📊 <b>Monitor Started</b>\n\n"
                f"<b>Task:</b> {desc}\n"
                f"<b>Interval:</b> Every {m.group(2)} minutes\n"
                f"<b>ID:</b> <code>{task_id}</code>\n\n"
                f"Cancel with: <code>/cancel {task_id}</code>",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.monitor_controls(task_id),
            )
        else:
            await _execute_task(message, text)

    elif action == "confirm_yes":
        if content:
            result = await task_orchestrator.confirm_action(content)
            await _send_chunks(message, result)
        else:
            await message.answer(task_orchestrator.list_pending(), parse_mode="HTML")

    elif action == "confirm_no":
        if content:
            result = task_orchestrator.deny_action(content)
            await message.answer(result, parse_mode="HTML")

    elif action == "scrape":
        await cmd_scrape(message)

    elif action == "shot":
        await cmd_shot(message)

    elif action == "help":
        await cmd_start(message)

    elif action == "stats":
        await cmd_stats(message)

    elif action == "circuits":
        await cmd_circuits(message)

    elif action == "usage":
        await cmd_usage(message)

    else:
        await _execute_task(message, content)


# ── Task Execution with Streaming ──────────────────────────────────────────────

async def _execute_task(message: Message, task: str) -> None:
    """Execute task with streaming responses and rich formatting."""
    import time
    start_time = time.time()
    
    original_task = task
    agent_key = agents.detect_agent(task)
    model = agents.get_model(agent_key)
    uid = message.from_user.id
    tid = current_thread.get(uid)

    if tid:
        ctx = agents.get_thread_context(tid)
        if ctx:
            task = f"{ctx}\n\nCurrent task: {task}"

    # Try streaming response
    streamer = streaming_response.StreamingResponseManager(bot)
    result: str | None = None
    
    try:
        result = await streamer.stream_response(
            message.chat.id,
            interpreter_bridge.run_task_streaming(model, task, agent_key),
            agent_key
        )
    except Exception as exc:
        logger.exception("Streaming failed: %s", exc)
        # Fallback to regular execution
        try:
            result = await interpreter_bridge.run_task(model, task, agent_key)
            formatted = formatters.ResponseFormatter.format_agent_response(result, agent_key)
            await message.answer(formatted, parse_mode="HTML")
        except Exception as fb_exc:
            formatted = formatters.ResponseFormatter.format_error_analysis(str(fb_exc), "Check logs")
            await message.answer(formatted, parse_mode="HTML")
    
    duration = time.time() - start_time
    
    if tid and result:
        agents.add_to_thread(tid, agent_key, original_task, result[:500])

    # Register for feedback
    try:
        from optimization.feedback_learner import get_learner
        fid = get_learner().register_response(agent_key, original_task)
        await message.answer(
            f"<i>Rate this response:</i>",
            parse_mode="HTML",
            reply_markup=telegram_ui.TelegramUI.feedback_buttons(fid),
        )
    except Exception:
        pass

    # Check for rate limit warnings
    if duration > 20:
        await notif_manager.notify_long_task(uid, original_task, duration)


# ── Production Monitoring Commands ─────────────────────────────────────────────

@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show performance metrics, cache stats, and feedback summary."""
    if not _authorized(message):
        await _deny(message)
        return
    parts = []
    try:
        from observability.metrics import format_stats
        parts.append(format_stats())
    except Exception as exc:
        parts.append(f"Metrics unavailable: {exc}")
    try:
        from optimization.feedback_learner import get_learner
        parts.append(get_learner().summary_report())
    except Exception as exc:
        parts.append(f"Feedback unavailable: {exc}")
    await message.answer("\n\n".join(parts), parse_mode="HTML")


@dp.message(Command("circuits"))
async def cmd_circuits(message: Message) -> None:
    """Show circuit breaker status for all agents."""
    if not _authorized(message):
        await _deny(message)
        return
    try:
        from reliability.error_recovery import get_recovery
        report = get_recovery().circuit_status()
        await message.answer(report, parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Circuit status unavailable: {exc}", parse_mode="HTML")


@dp.message(Command("usage"))
async def cmd_usage(message: Message) -> None:
    """Show daily API usage and estimated cost report."""
    if not _authorized(message):
        await _deny(message)
        return
    try:
        from optimization.usage_tracker import get_tracker
        report = get_tracker().daily_report()
        await message.answer(report, parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Usage report unavailable: {exc}", parse_mode="HTML")


@dp.message(Command("feedback"))
async def cmd_feedback(message: Message) -> None:
    """Rate a previous agent response.

    Usage: /feedback <id> good|bad [optional comment]
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=3)
    if len(args) < 3:
        await message.answer(
            "Usage: <code>/feedback &lt;id&gt; good|bad [comment]</code>",
            parse_mode="HTML",
        )
        return
    fid = args[1].strip()
    verdict = args[2].strip().lower()
    comment = args[3].strip() if len(args) > 3 else ""

    if verdict in ("good", "yes", "👍", "+1"):
        rating = 1
    elif verdict in ("bad", "no", "👎", "-1"):
        rating = -1
    else:
        await message.answer(
            "Rating must be <code>good</code> or <code>bad</code>.", parse_mode="HTML"
        )
        return

    try:
        from optimization.feedback_learner import get_learner
        result = get_learner().record(fid, rating, comment)
        formatted = formatters.ResponseFormatter.format_feedback_confirmation(verdict)
        await message.answer(formatted, parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Feedback error: {exc}", parse_mode="HTML")


# ── Entrypoint ─────────────────────────────────────────────────────────────────

async def main() -> None:
    """Start bot polling with enhanced UX."""
    logger.info("🚀 LegionSwarm starting with complete UX enhancement")
    logger.info("📱 Interactive buttons, streaming, and progress tracking enabled")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
