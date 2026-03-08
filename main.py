# /home/newadmin/swarm-bot/main.py
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

Natural Language Examples:
    "debug this pytorch error: ..."
    "what's on my screen right now?"
    "click on the terminal"
    "read /home/newadmin/swarm-bot/agents.py"
    "monitor my training every 5 minutes"
    [send voice message] → auto-transcribed
    [upload PDF] → file preview + action buttons
    [upload screenshot] → image action buttons

Shortcut Keyboard Buttons (shown at bottom of chat):
    🐛 Debug | 💻 Code | 📊 Analyze | 💡 Explain | 📌 Threads | ⚙️ Settings
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Document,
    Message,
    PhotoSize,
    Voice,
)
from dotenv import load_dotenv

import core.agent_registry as agents
import core.tools.computer_control as computer_control
import core.utils.formatters as formatters
import core.interpreter_bridge as interpreter_bridge
import core.utils.multimodal_processor as multimodal_processor
import core.utils.notifications as notifications
import core.tools.playwright_agent as playwright_agent
import core.nexus_orchestrator as task_orchestrator
import core.tools.vscode_bridge as vscode_bridge
from core.utils.progress_tracker import TaskProgressTracker
from core.utils.streaming_response import StreamingResponseManager
from core.utils.telegram_ui import TelegramUI

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Secrets ─────────────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
_raw_uid = os.getenv("ALLOWED_USER_ID", "")
ALLOWED_USER_ID: int = int(_raw_uid) if _raw_uid.isdigit() else 0

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")
if not ALLOWED_USER_ID:
    raise RuntimeError("ALLOWED_USER_ID not set or invalid in .env")

# ── Bot Setup ───────────────────────────────────────────────────────────────────

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Per-user active thread and settings
current_thread: dict[int, str] = {}
# User preferences: streaming, show_context, notifications
_user_prefs: dict[int, dict] = {}

# Cache of pending document file_ids for callback handling
# {file_id: (raw_bytes, mime_type, filename)}
_doc_cache: dict[str, tuple[bytes, str, str]] = {}
_img_cache: dict[str, bytes] = {}

_streamer: StreamingResponseManager | None = None


def _prefs(uid: int) -> dict:
    """Get or create default prefs for a user."""
    if uid not in _user_prefs:
        _user_prefs[uid] = {"streaming": True, "show_context": True, "notifications": True}
    return _user_prefs[uid]


# ── Auth Guard ──────────────────────────────────────────────────────────────────

def _authorized(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id == ALLOWED_USER_ID


async def _deny(message: Message) -> None:
    logger.warning("Unauthorized access from user_id=%s", message.from_user and message.from_user.id)


# ── Helpers ─────────────────────────────────────────────────────────────────────

async def _send_chunks(message: Message, text: str, reply_markup=None) -> None:
    """Send text in ≤4000-char HTML chunks."""
    chunks = interpreter_bridge.chunk_output(text)
    for i, chunk in enumerate(chunks):
        markup = reply_markup if i == len(chunks) - 1 else None
        await message.answer(f"<pre>{chunk}</pre>", parse_mode="HTML", reply_markup=markup)


async def _send_desktop_screenshot(message: Message) -> None:
    await message.answer("Taking desktop screenshot…")
    try:
        png_bytes = await computer_control.desktop_screenshot()
        await message.answer_photo(
            BufferedInputFile(png_bytes, filename="desktop.png"),
            caption="Current desktop",
        )
    except Exception as exc:
        await message.answer(f"Screenshot failed: {exc}", parse_mode="HTML")


def _detect_intent(text: str) -> dict:
    """Classify natural language into action + content."""
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

    # Desktop
    if any(kw in t for kw in ["what's on my screen", "what is on screen", "describe my screen", "show my screen"]):
        return {"action": "analyze_screen", "content": text}
    if any(kw in t for kw in ["desktop screenshot", "screenshot my screen", "take a screenshot of desktop"]):
        return {"action": "desktop_shot", "content": ""}
    if any(kw in t for kw in ["read my screen", "ocr screen", "what text is on screen"]):
        return {"action": "read_screen", "content": ""}

    # Click
    click_m = re.search(r"click (?:on )?['\"]?(.+?)['\"]?$", t)
    if click_m:
        return {"action": "click", "content": click_m.group(1).strip()}

    # File/shell
    read_m = re.search(r"read (?:file )?([/~]?\S+\.\w+)", text)
    if read_m:
        return {"action": "read_file", "content": read_m.group(1)}
    if any(kw in t for kw in ["git status", "git log", "show git"]):
        return {"action": "git", "content": ""}
    if any(kw in t for kw in ["terminal output", "what's in terminal", "show terminal"]):
        return {"action": "terminal", "content": ""}

    # Monitor
    if re.search(r"monitor .+ every \d+ min", t):
        return {"action": "monitor", "content": text}

    # Confirmations
    if t.startswith("confirm yes") or t.startswith("yes confirm"):
        parts = t.split()
        return {"action": "confirm_yes", "content": parts[-1] if len(parts) > 2 else ""}
    if t.startswith("confirm no") or t.startswith("no confirm"):
        parts = t.split()
        return {"action": "confirm_no", "content": parts[-1] if len(parts) > 2 else ""}

    # URL ops
    url_m = re.search(r"(https?://\S+)", text)
    if url_m:
        if any(kw in t for kw in ["scrape", "extract text", "get text from"]):
            return {"action": "scrape", "content": url_m.group(1)}
        if any(kw in t for kw in ["screenshot", "capture", "shot of"]):
            return {"action": "shot", "content": url_m.group(1)}

    # Navigation shortcuts from quick keyboard
    if t.strip() in ("🐛 debug", "debug"):
        return {"action": "quick_prompt", "content": "debug"}
    if t.strip() in ("💻 code", "code"):
        return {"action": "quick_prompt", "content": "code"}
    if t.strip() in ("📊 analyze", "analyze"):
        return {"action": "quick_prompt", "content": "analyze"}
    if t.strip() in ("💡 explain", "explain"):
        return {"action": "quick_prompt", "content": "explain"}
    if t.strip() in ("📌 threads", "threads"):
        return {"action": "threads", "content": ""}
    if t.strip() in ("⚙️ settings", "settings"):
        return {"action": "settings", "content": ""}

    if any(kw in t for kw in ["help", "what can you do", "commands"]):
        return {"action": "help", "content": ""}
    if any(kw in t for kw in ["show stats", "performance stats", "usage stats"]):
        return {"action": "stats", "content": ""}
    if any(kw in t for kw in ["circuit status", "circuit breaker"]):
        return {"action": "circuits", "content": ""}
    if any(kw in t for kw in ["usage report", "api usage", "cost report"]):
        return {"action": "usage", "content": ""}

    return {"action": "run", "content": text}


# ── Slash Command Handlers ──────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(
        "<b>LegionSwarm</b> — Autonomous Desktop AI\n\n"
        "Tap a button or just talk naturally:",
        reply_markup=TelegramUI.main_menu(),
        parse_mode="HTML",
    )
    await message.answer(
        "Keyboard shortcuts active 👇",
        reply_markup=TelegramUI.quick_reply_keyboard(),
    )


@dp.message(Command("models"))
async def cmd_models(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(
        agents.list_agents(),
        reply_markup=TelegramUI.back_to_menu(),
        parse_mode="HTML",
    )


@dp.message(Command("desktop"))
async def cmd_desktop(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    await _send_desktop_screenshot(message)


@dp.message(Command("screen"))
async def cmd_screen(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer("Reading screen text via OCR…")
    try:
        text = await computer_control.read_screen()
        await _send_chunks(message, text or "(no text detected)")
    except Exception as exc:
        await message.answer(f"OCR failed: {exc}", parse_mode="HTML")


@dp.message(Command("click"))
async def cmd_click(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/click &lt;text&gt;</code>", parse_mode="HTML")
        return
    target = args[1].strip()
    await message.answer(f"Looking for <code>{target}</code> on screen…", parse_mode="HTML")
    try:
        found = await computer_control.click_on(target)
        if found:
            await message.answer(f"Clicked: <code>{target}</code>", parse_mode="HTML")
        else:
            await message.answer(f"Element not found: <code>{target}</code>", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Click failed: {exc}", parse_mode="HTML")


@dp.message(Command("read"))
async def cmd_read_file(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/read &lt;path&gt;</code>", parse_mode="HTML")
        return
    path = args[1].strip()
    try:
        content = await vscode_bridge.read_file(path)
        await _send_chunks(message, content)
    except FileNotFoundError:
        await message.answer(f"File not found: <code>{path}</code>", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Read error: {exc}", parse_mode="HTML")


@dp.message(Command("cmd"))
async def cmd_shell(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/cmd &lt;command&gt;</code>", parse_mode="HTML")
        return
    cmd = args[1].strip()

    if computer_control.is_destructive(cmd):
        async def _run() -> str:
            return await vscode_bridge.run_command(cmd)

        action_id = task_orchestrator.queue_confirmation(
            f"Run: <code>{cmd}</code>", _run
        )
        await message.answer(
            f"⚠️ Destructive command queued.\n\n"
            f"<code>{cmd}</code>",
            reply_markup=TelegramUI.confirmation(action_id),
            parse_mode="HTML",
        )
        return

    await message.answer(f"Running: <code>{cmd}</code>…", parse_mode="HTML")
    try:
        output = await vscode_bridge.run_command(cmd)
        await _send_chunks(message, output)
    except Exception as exc:
        await message.answer(f"Command error: {exc}", parse_mode="HTML")


@dp.message(Command("git"))
async def cmd_git(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    try:
        status = await vscode_bridge.git_status()
        await _send_chunks(message, status)
    except Exception as exc:
        await message.answer(f"Git error: {exc}", parse_mode="HTML")


@dp.message(Command("thread"))
async def cmd_thread(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        # Show thread selector
        threads = agents.list_threads_raw()
        if threads:
            await message.answer(
                "Select a thread:", reply_markup=TelegramUI.thread_selector(threads), parse_mode="HTML"
            )
        else:
            await message.answer("Usage: <code>/thread &lt;name&gt;</code>", parse_mode="HTML")
        return
    tid = args[1].strip().lower().replace(" ", "_")
    current_thread[message.from_user.id] = tid
    await message.answer(f"Switched to thread: <b>{tid}</b>", parse_mode="HTML")


@dp.message(Command("threads"))
async def cmd_threads(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    threads = agents.list_threads_raw()
    if threads:
        await message.answer(
            "<b>Active Threads</b>",
            reply_markup=TelegramUI.thread_selector(threads),
            parse_mode="HTML",
        )
    else:
        await message.answer(agents.list_threads(), parse_mode="HTML")


@dp.message(Command("context"))
async def cmd_context(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    uid = message.from_user.id
    if uid not in current_thread:
        await message.answer("No active thread.", parse_mode="HTML")
        return
    tid = current_thread[uid]
    ctx = agents.get_thread_context(tid, last_n=5)
    if ctx:
        await message.answer(f"<b>Thread: {tid}</b>\n\n<pre>{ctx}</pre>", parse_mode="HTML")
    else:
        await message.answer(f"Thread <b>{tid}</b> is empty.", parse_mode="HTML")


@dp.message(Command("run"))
async def cmd_run(message: Message) -> None:
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
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            f"Usage: <code>/agent &lt;name&gt; &lt;task&gt;</code>",
            reply_markup=TelegramUI.agent_selector(),
            parse_mode="HTML",
        )
        return

    agent_key = args[1].strip().lower()
    task = args[2].strip()
    model = agents.get_model(agent_key)
    if model is None:
        await message.answer(f"Unknown agent: <b>{agent_key}</b>", parse_mode="HTML")
        return

    uid = message.from_user.id
    tid = current_thread.get(uid)
    full_task = task
    if tid:
        ctx = agents.get_thread_context(tid)
        if ctx:
            full_task = f"{ctx}\n\nCurrent task: {task}"

    await message.answer(f"Using <b>{agent_key}</b> (<code>{model}</code>)…", parse_mode="HTML")
    t0 = time.monotonic()
    try:
        result = await _run_with_streaming(message, model, full_task, agent_key)
    except Exception as exc:
        result = f"Error: {exc}"
    if tid:
        agents.add_to_thread(tid, agent_key, task, result)

    await notifications.task_complete(task, time.monotonic() - t0, agent_key)
    await _send_feedback_prompt(message, agent_key, task)


@dp.message(Command("scrape"))
async def cmd_scrape(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/scrape &lt;url&gt;</code>", parse_mode="HTML")
        return
    url = args[1].strip()
    await message.answer(f"Scraping <code>{url}</code>…", parse_mode="HTML")
    try:
        text = await playwright_agent.scrape(url)
    except Exception as exc:
        text = f"Error: {exc}"
    await _send_chunks(message, text)


@dp.message(Command("shot"))
async def cmd_shot(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/shot &lt;url&gt;</code>", parse_mode="HTML")
        return
    url = args[1].strip()
    await message.answer(f"Screenshotting <code>{url}</code>…", parse_mode="HTML")
    tmp_path: Path | None = None
    try:
        tmp_path = await playwright_agent.screenshot(url)
        await message.answer_photo(
            BufferedInputFile(tmp_path.read_bytes(), filename="screenshot.png"),
            caption=url,
        )
    except Exception as exc:
        await message.answer(f"Screenshot failed: {exc}", parse_mode="HTML")
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


@dp.message(Command("confirm"))
async def cmd_confirm(message: Message) -> None:
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


@dp.message(Command("pending"))
async def cmd_pending(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(task_orchestrator.list_pending(), parse_mode="HTML")


@dp.message(Command("monitors"))
async def cmd_monitors(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(task_orchestrator.list_monitors(), parse_mode="HTML")


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(task_orchestrator.list_monitors(), parse_mode="HTML")
        return
    result = task_orchestrator.cancel_monitor(args[1])
    await message.answer(result, parse_mode="HTML")


# ── Production Monitoring Commands ──────────────────────────────────────────────

@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    parts = []
    try:
        from core.observability.metrics import format_stats
        parts.append(format_stats())
    except Exception as exc:
        parts.append(f"Metrics unavailable: {exc}")
    try:
        from core.optimization.feedback_learner import get_learner
        parts.append(get_learner().summary_report())
    except Exception as exc:
        parts.append(f"Feedback unavailable: {exc}")
    await message.answer(
        "\n\n".join(parts),
        reply_markup=TelegramUI.back_to_menu(),
        parse_mode="HTML",
    )


@dp.message(Command("circuits"))
async def cmd_circuits(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    try:
        from core.reliability.error_recovery import get_recovery
        report = get_recovery().circuit_status()
        await message.answer(report, reply_markup=TelegramUI.back_to_menu(), parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Circuit status unavailable: {exc}", parse_mode="HTML")


@dp.message(Command("usage"))
async def cmd_usage(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    try:
        from core.optimization.usage_tracker import get_tracker
        report = get_tracker().daily_report()
        await message.answer(report, reply_markup=TelegramUI.back_to_menu(), parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Usage report unavailable: {exc}", parse_mode="HTML")


@dp.message(Command("feedback"))
async def cmd_feedback(message: Message) -> None:
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

    if verdict in ("good", "yes", "+1"):
        rating = 1
    elif verdict in ("bad", "no", "-1"):
        rating = -1
    else:
        await message.answer("Rating must be <code>good</code> or <code>bad</code>.", parse_mode="HTML")
        return

    try:
        from core.optimization.feedback_learner import get_learner
        result = get_learner().record(fid, rating, comment)
        await message.answer(result or "Feedback recorded.", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Feedback error: {exc}", parse_mode="HTML")


# ── Inline Callback Handlers ────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("quick:"))
async def cb_quick_action(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    action = callback.data.split(":", 1)[1]
    prompts = {
        "debug":   "🐛 <b>Debug Mode</b>\n\nSend me your error traceback or describe the issue.",
        "code":    "💻 <b>Coding Mode</b>\n\nDescribe what you want to build or ask for code.",
        "analyze": "📊 <b>Analysis Mode</b>\n\nUpload a file (CSV, JSON, logs) or paste data.",
        "explain": "💡 <b>Explain Mode</b>\n\nAsk me to explain any concept, algorithm, or error.",
        "design":  "🏗️ <b>Design Mode</b>\n\nDescribe the system you want to architect.",
        "desktop": None,
    }
    if action == "desktop":
        await callback.answer()
        await _send_desktop_screenshot(callback.message)
        return

    text = prompts.get(action, "How can I help?")
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("nav:"))
async def cb_nav(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    dest = callback.data.split(":", 1)[1]
    if dest == "main_menu":
        await callback.message.edit_text(
            "<b>LegionSwarm</b> — Autonomous Desktop AI\n\nWhat would you like to do?",
            reply_markup=TelegramUI.main_menu(),
            parse_mode="HTML",
        )
    elif dest == "threads":
        threads = agents.list_threads_raw()
        if threads:
            await callback.message.edit_text(
                "<b>Active Threads</b>\n\nSelect one:",
                reply_markup=TelegramUI.thread_selector(threads),
                parse_mode="HTML",
            )
        else:
            await callback.message.answer("No active threads yet.")
    elif dest == "settings":
        uid = callback.from_user.id
        prefs = _prefs(uid)
        await callback.message.edit_text(
            "⚙️ <b>Settings</b>\n\nToggle preferences:",
            reply_markup=TelegramUI.settings_menu(prefs),
            parse_mode="HTML",
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("agent_force:"))
async def cb_agent_force(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    agent_key = callback.data.split(":", 1)[1]
    await callback.message.answer(
        f"<b>{agent_key.upper()} agent selected.</b>\n\nSend your task:",
        parse_mode="HTML",
    )
    # Store pending agent preference temporarily
    _prefs(callback.from_user.id)["pending_agent"] = agent_key
    await callback.answer(f"Agent: {agent_key}")


@dp.callback_query(F.data.startswith("thread_switch:"))
async def cb_thread_switch(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    tid = callback.data.split(":", 1)[1]
    current_thread[callback.from_user.id] = tid
    await callback.message.edit_text(
        f"📌 Switched to thread: <b>{tid}</b>",
        reply_markup=TelegramUI.back_to_menu(),
        parse_mode="HTML",
    )
    await callback.answer(f"Thread: {tid}")


@dp.callback_query(F.data == "thread_new")
async def cb_thread_new(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    await callback.message.answer("Send a name for the new thread (e.g. <code>workernet</code>):", parse_mode="HTML")
    _prefs(callback.from_user.id)["awaiting_thread_name"] = True
    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_yes:"))
async def cb_confirm_yes(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    action_id = callback.data.split(":", 1)[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    result = await task_orchestrator.confirm_action(action_id)
    await callback.message.answer(f"✅ {result}", parse_mode="HTML")
    await callback.answer("Confirmed")


@dp.callback_query(F.data.startswith("confirm_no:"))
async def cb_confirm_no(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    action_id = callback.data.split(":", 1)[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    result = task_orchestrator.deny_action(action_id)
    await callback.message.answer(f"❌ {result}", parse_mode="HTML")
    await callback.answer("Cancelled")


@dp.callback_query(F.data.startswith("doc:"))
async def cb_doc_action(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    parts = callback.data.split(":", 2)
    action = parts[1]
    file_id = parts[2] if len(parts) > 2 else ""
    await callback.answer(f"Processing: {action}…")

    cached = _doc_cache.get(file_id)
    if not cached:
        await callback.message.answer("Document no longer cached. Please re-upload.", parse_mode="HTML")
        return

    raw, mime, fname = cached
    extracted, _label = await multimodal_processor.process_document(raw, mime, fname)
    if not extracted:
        await callback.message.answer("Could not extract text from this document.", parse_mode="HTML")
        return

    prompts_map = {
        "summarize": f"Summarize this document concisely:\n\n{extracted[:6000]}",
        "qa":        f"The following document has been uploaded. Await user questions.\n\n{extracted[:6000]}",
        "extract":   f"Extract all tables, lists, and key data from this document:\n\n{extracted[:6000]}",
        "analyze":   f"Perform a thorough analysis of this document:\n\n{extracted[:6000]}",
    }
    task = prompts_map.get(action, f"Analyze this document:\n\n{extracted[:6000]}")

    if action == "qa":
        uid = callback.from_user.id
        tid = current_thread.get(uid, "doc_context")
        agents.add_to_thread(tid, "document", f"Uploaded: {fname}", extracted[:2000])
        current_thread[uid] = tid
        await callback.message.answer(
            f"📄 <b>{fname}</b> loaded into thread <b>{tid}</b>.\nAsk me anything about it.",
            parse_mode="HTML",
        )
        return

    model = agents.get_model("mentor") or agents.get_model("coding")
    await callback.message.answer(f"Processing <code>{action}</code> on <b>{fname}</b>…", parse_mode="HTML")
    result = await interpreter_bridge.run_task(model, task, "mentor")
    formatted = formatters.format_response(result, "mentor", concept=fname)
    await _send_chunks(callback.message, formatted)


@dp.callback_query(F.data.startswith("img:"))
async def cb_img_action(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    parts = callback.data.split(":", 2)
    action = parts[1]
    file_id = parts[2] if len(parts) > 2 else ""
    await callback.answer(f"Processing: {action}…")

    image_bytes = _img_cache.get(file_id)
    if not image_bytes:
        await callback.message.answer("Image no longer cached. Please re-upload.", parse_mode="HTML")
        return

    questions_map = {
        "describe": "Describe this image in detail.",
        "errors":   "Find and explain any errors, warnings, or problems visible in this image.",
        "ocr":      "Extract and return all text visible in this image.",
        "fix":      "Identify the issue shown and suggest a concrete fix.",
    }
    question = questions_map.get(action, "Describe this image.")
    await callback.message.answer(f"Analyzing image: <i>{question}</i>…", parse_mode="HTML")
    result = await multimodal_processor.analyze_image(image_bytes, question)
    formatted = formatters.format_response(result, "vision")
    await _send_chunks(callback.message, formatted)


@dp.callback_query(F.data.startswith("fb:"))
async def cb_feedback(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    parts = callback.data.split(":", 2)
    verdict = parts[1]
    fid = parts[2] if len(parts) > 2 else ""
    rating = 1 if verdict == "good" else -1

    try:
        from core.optimization.feedback_learner import get_learner
        result = get_learner().record(fid, rating)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer(result or "Feedback recorded!")
    except Exception as exc:
        await callback.answer(f"Error: {exc}")


@dp.callback_query(F.data.startswith("setting:toggle:"))
async def cb_setting_toggle(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    key = callback.data.split(":", 2)[2]
    uid = callback.from_user.id
    prefs = _prefs(uid)
    prefs[key] = not prefs.get(key, True)
    await callback.message.edit_text(
        "⚙️ <b>Settings</b>\n\nToggle preferences:",
        reply_markup=TelegramUI.settings_menu(prefs),
        parse_mode="HTML",
    )
    await callback.answer(f"{key}: {'On' if prefs[key] else 'Off'}")


@dp.callback_query(F.data.startswith("task_cancel:"))
async def cb_task_cancel(callback: CallbackQuery) -> None:
    if not callback.from_user or callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("Unauthorized")
        return
    task_id = callback.data.split(":", 1)[1]
    result = task_orchestrator.cancel_monitor(task_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Cancelled")
    await callback.message.answer(result, parse_mode="HTML")


# ── Multi-Modal Input Handlers ──────────────────────────────────────────────────

@dp.message(F.voice)
async def handle_voice(message: Message) -> None:
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
            f"🎤 <b>Heard:</b>\n\n<i>{text}</i>\n\nProcessing…",
            parse_mode="HTML",
        )
        await _execute_task(message, text)

    except RuntimeError as exc:
        await status_msg.edit_text(f"Transcription unavailable: {exc}", parse_mode="HTML")
    except Exception as exc:
        logger.exception("Voice handler error: %s", exc)
        await status_msg.edit_text(f"Voice error: {exc}", parse_mode="HTML")


@dp.message(F.document)
async def handle_document(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    doc: Document = message.document
    mime = doc.mime_type or ""
    fname = doc.file_name or "document"
    size_kb = (doc.file_size or 0) / 1024

    try:
        file = await bot.get_file(doc.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        raw = file_bytes_io.read()

        # Cache for callback handling
        _doc_cache[doc.file_id] = (raw, mime, fname)
        # Evict old entries (keep last 10)
        if len(_doc_cache) > 10:
            oldest = next(iter(_doc_cache))
            del _doc_cache[oldest]

        preview = formatters.ResponseFormatter.file_preview(fname, size_kb, mime)
        await message.answer(
            preview,
            reply_markup=TelegramUI.document_actions(doc.file_id),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("Document handler error: %s", exc)
        await message.answer(f"Document error: {exc}", parse_mode="HTML")


@dp.message(F.photo)
async def handle_photo(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    photo: PhotoSize = message.photo[-1]

    try:
        file = await bot.get_file(photo.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        image_bytes = file_bytes_io.read()

        # Cache for callback
        _img_cache[photo.file_id] = image_bytes
        if len(_img_cache) > 20:
            oldest = next(iter(_img_cache))
            del _img_cache[oldest]

        caption = message.caption or ""
        if caption:
            # User provided a question — answer immediately
            await message.answer("Analyzing image…")
            result = await multimodal_processor.analyze_image(image_bytes, caption)
            formatted = formatters.format_response(result, "vision")
            await _send_chunks(message, formatted)
        else:
            # Show action buttons
            await message.answer(
                "📷 <b>Image received</b>\n\nWhat would you like me to do?",
                reply_markup=TelegramUI.image_actions(photo.file_id),
                parse_mode="HTML",
            )
    except Exception as exc:
        logger.exception("Photo handler error: %s", exc)
        await message.answer(f"Image error: {exc}", parse_mode="HTML")


# ── Natural Language Handler ─────────────────────────────────────────────────────

@dp.message(F.text)
async def handle_natural(message: Message) -> None:
    if not _authorized(message):
        await _deny(message)
        return
    text = (message.text or "").strip()
    if not text:
        return

    uid = message.from_user.id
    prefs = _prefs(uid)

    # Check if user was asked to name a new thread
    if prefs.pop("awaiting_thread_name", False):
        tid = text.strip().lower().replace(" ", "_")
        current_thread[uid] = tid
        await message.answer(f"✅ Created and switched to thread: <b>{tid}</b>", parse_mode="HTML")
        return

    # Check if a specific agent was pre-selected via button
    forced_agent = prefs.pop("pending_agent", None)
    if forced_agent:
        model = agents.get_model(forced_agent)
        if model:
            await _execute_task(message, text, forced_agent=forced_agent)
            return

    intent = _detect_intent(text)
    action = intent["action"]
    content = intent["content"]

    if action == "thread":
        tid = content.lower().replace(" ", "_")
        current_thread[uid] = tid
        await message.answer(f"Switched to thread: <b>{tid}</b>", parse_mode="HTML")

    elif action == "threads":
        threads = agents.list_threads_raw()
        if threads:
            await message.answer("Select a thread:", reply_markup=TelegramUI.thread_selector(threads), parse_mode="HTML")
        else:
            await message.answer(agents.list_threads(), parse_mode="HTML")

    elif action == "context":
        if uid not in current_thread:
            await message.answer("No active thread.", parse_mode="HTML")
            return
        tid = current_thread[uid]
        ctx = agents.get_thread_context(tid, last_n=5)
        if ctx:
            await message.answer(f"<b>Thread: {tid}</b>\n\n<pre>{ctx}</pre>", parse_mode="HTML")
        else:
            await message.answer(f"Thread <b>{tid}</b> is empty.", parse_mode="HTML")

    elif action == "models":
        await message.answer(agents.list_agents(), parse_mode="HTML")

    elif action == "desktop_shot":
        await _send_desktop_screenshot(message)

    elif action == "analyze_screen":
        await message.answer("Analyzing your screen…")
        try:
            result = await computer_control.analyze_screen(content or "What is visible?")
            await _send_chunks(message, formatters.format_response(result, "vision"))
        except Exception as exc:
            await message.answer(f"Screen analysis error: {exc}", parse_mode="HTML")

    elif action == "read_screen":
        await message.answer("Reading screen via OCR…")
        try:
            text_out = await computer_control.read_screen()
            await _send_chunks(message, text_out or "(no text detected)")
        except Exception as exc:
            await message.answer(f"OCR error: {exc}", parse_mode="HTML")

    elif action == "click":
        await message.answer(f"Clicking: <code>{content}</code>…", parse_mode="HTML")
        try:
            found = await computer_control.click_on(content)
            status = f"Clicked: <code>{content}</code>" if found else f"Not found: <code>{content}</code>"
            await message.answer(status, parse_mode="HTML")
        except Exception as exc:
            await message.answer(f"Click error: {exc}", parse_mode="HTML")

    elif action == "read_file":
        try:
            file_content = await vscode_bridge.read_file(content)
            await _send_chunks(message, file_content)
        except FileNotFoundError:
            await message.answer(f"File not found: <code>{content}</code>", parse_mode="HTML")
        except Exception as exc:
            await message.answer(f"Read error: {exc}", parse_mode="HTML")

    elif action == "git":
        status = await vscode_bridge.git_status()
        await _send_chunks(message, status)

    elif action == "terminal":
        output = await vscode_bridge.get_terminal_output()
        await _send_chunks(message, output)

    elif action == "monitor":
        m = re.search(r"monitor (.+?) every (\d+) min", text, re.IGNORECASE)
        if m:
            desc = m.group(1).strip()
            interval = int(m.group(2)) * 60

            async def _monitor_fn() -> str:
                return await vscode_bridge.run_command(f"echo 'Monitoring: {desc}'")

            async def _notify_fn(msg: str) -> None:
                await message.answer(msg, parse_mode="HTML")

            task_id = await task_orchestrator.start_monitor(desc, interval, _monitor_fn, _notify_fn)
            await message.answer(
                f"Monitor started: <b>{desc}</b> every {m.group(2)} min\n"
                f"ID: <code>{task_id}</code>",
                reply_markup=TelegramUI.task_controls(task_id),
                parse_mode="HTML",
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
        await message.answer(f"Scraping <code>{content}</code>…", parse_mode="HTML")
        try:
            scraped = await playwright_agent.scrape(content)
        except Exception as exc:
            scraped = f"Error: {exc}"
        await _send_chunks(message, scraped)

    elif action == "shot":
        await message.answer(f"Screenshotting <code>{content}</code>…", parse_mode="HTML")
        tmp_path: Path | None = None
        try:
            tmp_path = await playwright_agent.screenshot(content)
            await message.answer_photo(
                BufferedInputFile(tmp_path.read_bytes(), filename="screenshot.png"),
                caption=content,
            )
        except Exception as exc:
            await message.answer(f"Screenshot failed: {exc}", parse_mode="HTML")
        finally:
            if tmp_path:
                tmp_path.unlink(missing_ok=True)

    elif action == "quick_prompt":
        prompts = {
            "debug":   "🐛 <b>Debug Mode</b>\n\nSend me your error or traceback:",
            "code":    "💻 <b>Coding Mode</b>\n\nDescribe what you want to build:",
            "analyze": "📊 <b>Analysis Mode</b>\n\nUpload a file or paste data:",
            "explain": "💡 <b>Explain Mode</b>\n\nWhat concept should I explain?",
        }
        await message.answer(prompts.get(content, "How can I help?"), parse_mode="HTML")

    elif action == "settings":
        await message.answer(
            "⚙️ <b>Settings</b>",
            reply_markup=TelegramUI.settings_menu(_prefs(uid)),
            parse_mode="HTML",
        )

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


# ── Task Execution ──────────────────────────────────────────────────────────────

async def _run_with_streaming(
    message: Message,
    model: str,
    task: str,
    agent_key: str,
) -> str:
    """Run a task, streaming output if user pref is on, else buffered."""
    uid = message.from_user.id if message.from_user else 0
    use_streaming = _prefs(uid).get("streaming", True)

    if use_streaming and _streamer:
        icon_map = {"vision":"👁️","coding":"💻","debug":"🐛","math":"🔢","architect":"🏗️","mentor":"📚","analyst":"📊"}
        icon = icon_map.get(agent_key, "🤖")
        header = f"<b>{icon} {agent_key.upper()}</b>"
        return await _streamer.stream_task(message.chat.id, model, task, agent_key, header)
    else:
        result = await interpreter_bridge.run_task(model, task, agent_key)
        formatted = formatters.format_response(result, agent_key)
        await _send_chunks(message, formatted)
        return result


async def _send_feedback_prompt(message: Message, agent_key: str, task: str) -> None:
    """Register response and show inline feedback buttons."""
    try:
        from core.optimization.feedback_learner import get_learner
        fid = get_learner().register_response(agent_key, task)
        await message.answer(
            "<i>Rate this response:</i>",
            reply_markup=TelegramUI.feedback_buttons(fid),
            parse_mode="HTML",
        )
    except Exception:
        pass


async def _execute_task(
    message: Message,
    task: str,
    forced_agent: Optional[str] = None,
) -> None:
    """Auto-detect agent, run task with progress tracking, store in thread."""
    original_task = task
    agent_key = forced_agent or agents.detect_agent(task)
    model = agents.get_model(agent_key)
    uid = message.from_user.id if message.from_user else 0
    tid = current_thread.get(uid)
    show_ctx = _prefs(uid).get("show_context", True)

    if tid:
        ctx = agents.get_thread_context(tid)
        if ctx:
            task = f"{ctx}\n\nCurrent task: {task}"

    # --- Try supervisor orchestration for complex tasks ---
    result: str | None = None
    try:
        from core.orchestration.supervisor import orchestrate

        async def _run_fn(t: str, a: str = agent_key) -> str:
            m = agents.get_model(a) or model
            return await interpreter_bridge.run_task(m, t, a)

        async def _progress_fn(msg_text: str) -> None:
            await message.answer(f"⚙️ {msg_text}", parse_mode="HTML")

        result = await orchestrate(task, _run_fn, _progress_fn)
        if result:
            formatted = formatters.format_response(result, agent_key)
            await _send_chunks(message, formatted)
    except Exception as exc:
        logger.debug("Supervisor skipped: %s", exc)
        result = None

    # --- Direct agent execution ---
    if result is None:
        t0 = time.monotonic()
        try:
            result = await _run_with_streaming(message, model, task, agent_key)
        except Exception as exc:
            logger.exception("Primary agent failed: %s", exc)
            fallback = agents.get_model(agent_key, use_fallback=True)
            if fallback and fallback != model:
                await message.answer(
                    f"⚠️ Primary failed, trying fallback: <code>{fallback}</code>",
                    parse_mode="HTML",
                )
                try:
                    result = await _run_with_streaming(message, fallback, task, agent_key)
                    await notifications.model_fallback_used(model, fallback, str(exc))
                except Exception as fb_exc:
                    result = f"Both agents failed.\nPrimary: {exc}\nFallback: {fb_exc}"
                    await _send_chunks(message, result)
            else:
                result = f"Error: {exc}"
                await message.answer(
                    formatters.ResponseFormatter.error_box("Agent Error", str(exc)),
                    parse_mode="HTML",
                )
                return

        await notifications.task_complete(original_task, time.monotonic() - t0, agent_key)

    if tid and result:
        agents.add_to_thread(tid, agent_key, original_task, result)

    # Thread context bar
    if tid and show_ctx and result:
        turn = len(agents.get_thread_context(tid).split("\n\n")) if agents.get_thread_context(tid) else 1
        await message.answer(
            formatters.ResponseFormatter.thread_status(tid, turn, agent_key),
            parse_mode="HTML",
        )

    await _send_feedback_prompt(message, agent_key, original_task)


# ── Agency Swarm — New Commands ──────────────────────────────────────────────────

@dp.message(Command("dept"))
async def cmd_dept(message: Message) -> None:
    """/dept <department> <task> — Route to a specific department."""
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=2)
    if len(args) < 3:
        depts = agents.list_all_departments()
        await message.answer(
            "<b>Usage:</b> <code>/dept &lt;department&gt; &lt;task&gt;</code>\n\n"
            "<b>Departments:</b>\n" + "\n".join(f"• <code>{d}</code>" for d in depts),
            parse_mode="HTML",
        )
        return
    dept = args[1].strip().lower()
    task = args[2].strip()
    from core.nexus_orchestrator import nexus as _nexus
    from core.agent_registry import list_all_departments
    if dept not in list_all_departments():
        await message.answer(
            f"❌ Unknown department: <b>{dept}</b>\n\n"
            "Available: " + ", ".join(f"<code>{d}</code>" for d in list_all_departments()),
            parse_mode="HTML",
        )
        return
    decision = await _nexus.route_to_dept(dept, task)
    await message.answer(
        f"🎯 Routing to <b>{decision.agent.name}</b> "
        f"(<code>{decision.agent.department}</code>)\n"
        f"Confidence: {decision.confidence:.0%} | Method: {decision.method}",
        parse_mode="HTML",
    )
    result = await _nexus.execute_task(decision, task, message)
    await _send_chunks(message, result)


@dp.message(Command("swarm"))
async def cmd_swarm(message: Message) -> None:
    """/swarm <task> — Spawn a multi-agent swarm for complex tasks."""
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "<b>Usage:</b> <code>/swarm &lt;complex task&gt;</code>\n\n"
            "Example: <code>/swarm design and implement a FastAPI auth system</code>",
            parse_mode="HTML",
        )
        return
    task = args[1].strip()
    await message.answer("🐝 <b>Swarm Mode Activated</b> — coordinating agents…", parse_mode="HTML")
    from core.nexus_orchestrator import nexus as _nexus
    result = await _nexus.run_swarm(task, message)
    await _send_chunks(message, result)


@dp.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """/status — System dashboard: agents, circuit breakers, API usage."""
    if not _authorized(message):
        await _deny(message)
        return
    from core.agent_registry import get_agent_count, list_all_departments
    counts = get_agent_count()
    total = sum(counts.values())
    lines = [
        "📊 <b>Babas Agency Swarm — Status</b>\n",
        f"<b>Agents loaded:</b> {total} across {len(counts)} departments",
    ]
    for dept, n in sorted(counts.items()):
        lines.append(f"  • {dept.replace('_', ' ').title()}: {n}")
    lines.append("")
    lines.append("Use <code>/usage</code> for API costs | <code>/circuits</code> for circuit states")
    await message.answer("\n".join(lines), parse_mode="HTML")


@dp.message(Command("cost"))
async def cmd_cost(message: Message) -> None:
    """/cost — Alias for /usage (API usage + estimated costs)."""
    if not _authorized(message):
        await _deny(message)
        return
    # Delegate to /usage handler
    await cmd_usage(message)


# ── Entrypoint ──────────────────────────────────────────────────────────────────

async def main() -> None:
    """Start Babas Agency Swarm with all 76 agents + Nexus routing."""
    global _streamer
    _streamer = StreamingResponseManager(bot)
    notifications.init(bot, ALLOWED_USER_ID)

    # Load agent registry
    from core.agent_registry import load_registry
    load_registry()
    from core.agent_registry import AGENT_REGISTRY, DEPARTMENT_INDEX
    logger.info(
        "Babas Agency Swarm starting — %d agents across %d departments",
        len(AGENT_REGISTRY),
        len(DEPARTMENT_INDEX),
    )

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
