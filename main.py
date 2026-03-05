# /home/newadmin/swarm-bot/main.py
"""LegionSwarm — Autonomous Desktop AI via Telegram.

Slash Commands (optional — natural language works too):
    /start          — Help menu
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

Natural Language Examples:
    "debug this pytorch error: ..."
    "what's on my screen right now?"
    "click on the terminal"
    "read /home/newadmin/swarm-bot/agents.py"
    "monitor my training every 5 minutes"
    [send voice message] → auto-transcribed
    [upload PDF] → auto-extracted and analyzed
    [upload screenshot] → auto-analyzed by vision model
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

async def _send_chunks(message: Message, text: str) -> None:
    """Send text in ≤4000-char HTML chunks.

    Args:
        message: Source message (for chat context).
        text: Full output to send.
    """
    chunks = interpreter_bridge.chunk_output(text)
    for chunk in chunks:
        await message.answer(f"<pre>{chunk}</pre>", parse_mode="HTML")


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

    return {"action": "run", "content": text}


# ── Slash Command Handlers ─────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Show help menu."""
    if not _authorized(message):
        await _deny(message)
        return

    await message.answer(
        "<b>LegionSwarm</b> — Autonomous Desktop AI\n\n"
        "<b>Just talk naturally:</b>\n"
        "  • <i>debug this pytorch error: ...</i>\n"
        "  • <i>what's on my screen?</i>\n"
        "  • <i>click on the terminal</i>\n"
        "  • <i>read ~/swarm-bot/main.py</i>\n"
        "  • <i>monitor training every 5 minutes</i>\n"
        "  • [send voice] → auto-transcribed\n"
        "  • [upload PDF] → auto-analyzed\n"
        "  • [upload image] → vision analysis\n\n"
        "<b>Commands:</b>\n"
        "/desktop — screenshot this PC\n"
        "/screen — OCR current desktop\n"
        "/git — workspace git status\n"
        "/monitors — active monitors\n"
        "/pending — pending confirmations\n"
        "/models — agent roster\n\n"
        f"<b>Agents:</b> {', '.join(agents.AGENT_MODELS.keys())}",
        parse_mode="HTML",
    )


@dp.message(Command("models"))
async def cmd_models(message: Message) -> None:
    """Show agent roster."""
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(agents.list_agents(), parse_mode="HTML")


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
    await message.answer("Reading screen text via OCR…")
    try:
        text = await computer_control.read_screen()
        await _send_chunks(message, text or "(no text detected)")
    except Exception as exc:
        await message.answer(f"OCR failed: {exc}", parse_mode="HTML")


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
    try:
        content = await vscode_bridge.read_file(path)
        await _send_chunks(message, content)
    except FileNotFoundError:
        await message.answer(f"File not found: <code>{path}</code>", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"Read error: {exc}", parse_mode="HTML")


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
            f"⚠️ Destructive command queued.\n\n"
            f"<code>{cmd}</code>\n\n"
            f"Confirm: <code>/confirm yes {action_id}</code>\n"
            f"Cancel:  <code>/confirm no {action_id}</code>",
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
    """Show workspace git status."""
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
    """Switch to a conversation thread.

    Usage: /thread <name>
    """
    if not _authorized(message):
        await _deny(message)
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/thread &lt;name&gt;</code>", parse_mode="HTML")
        return
    thread_id = args[1].strip().lower().replace(" ", "_")
    current_thread[message.from_user.id] = thread_id
    await message.answer(f"Switched to thread: <b>{thread_id}</b>", parse_mode="HTML")


@dp.message(Command("threads"))
async def cmd_threads(message: Message) -> None:
    """List active threads."""
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(agents.list_threads(), parse_mode="HTML")


@dp.message(Command("context"))
async def cmd_context(message: Message) -> None:
    """Show current thread history."""
    if not _authorized(message):
        await _deny(message)
        return
    uid = message.from_user.id
    if uid not in current_thread:
        await message.answer("No active thread.", parse_mode="HTML")
        return
    tid = current_thread[uid]
    ctx = agents.get_thread_context(tid, last_n=5)
    if not ctx:
        await message.answer(f"Thread <b>{tid}</b> is empty.", parse_mode="HTML")
    else:
        await message.answer(f"<b>Thread: {tid}</b>\n\n<pre>{ctx}</pre>", parse_mode="HTML")


@dp.message(Command("run"))
async def cmd_run(message: Message) -> None:
    """Auto-detect agent and run task.

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
            f"Usage: <code>/agent &lt;name&gt; &lt;task&gt;</code>\n"
            f"Agents: {', '.join(agents.AGENT_MODELS.keys())}",
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
    try:
        result = await interpreter_bridge.run_task(model, full_task, agent_key)
    except Exception as exc:
        result = f"Error: {exc}"
    if tid:
        agents.add_to_thread(tid, agent_key, task, result)
    await _send_chunks(message, result)


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
    await message.answer(f"Scraping <code>{url}</code>…", parse_mode="HTML")
    try:
        text = await playwright_agent.scrape(url)
    except Exception as exc:
        text = f"Error: {exc}"
    await _send_chunks(message, text)


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
    """Transcribe voice message and process as text task."""
    if not _authorized(message):
        await _deny(message)
        return

    await message.answer("Transcribing voice message…")
    try:
        voice: Voice = message.voice
        file = await bot.get_file(voice.file_id)
        file_bytes = await bot.download_file(file.file_path)
        audio_bytes = file_bytes.read()

        text = await multimodal_processor.transcribe_voice(audio_bytes, extension=".ogg")
        await message.answer(f"<i>Heard:</i> {text}", parse_mode="HTML")
        await _execute_task(message, text)

    except RuntimeError as exc:
        await message.answer(f"Transcription unavailable: {exc}", parse_mode="HTML")
    except Exception as exc:
        logger.exception("Voice handler error: %s", exc)
        await message.answer(f"Voice error: {exc}", parse_mode="HTML")


@dp.message(F.document)
async def handle_document(message: Message) -> None:
    """Extract document text and analyze it with the appropriate agent."""
    if not _authorized(message):
        await _deny(message)
        return

    doc: Document = message.document
    mime = doc.mime_type or ""
    fname = doc.file_name or ""

    await message.answer(f"Processing document: <code>{fname}</code>…", parse_mode="HTML")

    try:
        file = await bot.get_file(doc.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        raw = file_bytes_io.read()

        extracted, label = await multimodal_processor.process_document(raw, mime, fname)

        if not extracted:
            await message.answer(
                f"Cannot process {label}. Supported: PDF, DOCX, TXT", parse_mode="HTML"
            )
            return

        # Store in active thread if one is set
        uid = message.from_user.id
        tid = current_thread.get(uid)
        if tid:
            agents.add_to_thread(tid, "document", f"Uploaded: {fname}", extracted[:300])
            await message.answer(
                f"{label} added to thread <b>{tid}</b>. Ask me anything about it.",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"{label} extracted ({len(extracted)} chars). Summarizing with mentor agent…",
                parse_mode="HTML",
            )
            model = agents.get_model("mentor") or agents.get_model("coding")
            summary = await interpreter_bridge.run_task(
                model,
                f"Summarize this document concisely:\n\n{extracted[:6000]}",
                "mentor",
            )
            await _send_chunks(message, summary)

    except Exception as exc:
        logger.exception("Document handler error: %s", exc)
        await message.answer(f"Document error: {exc}", parse_mode="HTML")


@dp.message(F.photo)
async def handle_photo(message: Message) -> None:
    """Analyze uploaded photo with vision model."""
    if not _authorized(message):
        await _deny(message)
        return

    # Get highest-resolution version
    photo: PhotoSize = message.photo[-1]
    caption = message.caption or "Describe this image in detail. If it shows code or an error, analyze it."

    await message.answer("Analyzing image with vision model…")
    try:
        file = await bot.get_file(photo.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        image_bytes = file_bytes_io.read()

        analysis = await multimodal_processor.analyze_image(image_bytes, caption)
        await _send_chunks(message, analysis)

    except Exception as exc:
        logger.exception("Photo handler error: %s", exc)
        await message.answer(f"Image analysis error: {exc}", parse_mode="HTML")


# ── Natural Language Handler ───────────────────────────────────────────────────

@dp.message(F.text)
async def handle_natural(message: Message) -> None:
    """Route natural language messages to the appropriate action."""
    if not _authorized(message):
        await _deny(message)
        return

    text = (message.text or "").strip()
    if not text:
        return

    intent = _detect_intent(text)
    action = intent["action"]
    content = intent["content"]
    uid = message.from_user.id

    if action == "thread":
        tid = content.lower().replace(" ", "_")
        current_thread[uid] = tid
        await message.answer(f"Switched to thread: <b>{tid}</b>", parse_mode="HTML")

    elif action == "threads":
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
            result = await computer_control.analyze_screen(content or "What is visible on screen?")
            await _send_chunks(message, result)
        except Exception as exc:
            await message.answer(f"Screen analysis error: {exc}", parse_mode="HTML")

    elif action == "read_screen":
        await message.answer("Reading screen text via OCR…")
        try:
            text_out = await computer_control.read_screen()
            await _send_chunks(message, text_out or "(no text detected)")
        except Exception as exc:
            await message.answer(f"OCR error: {exc}", parse_mode="HTML")

    elif action == "click":
        await message.answer(f"Clicking: <code>{content}</code>…", parse_mode="HTML")
        try:
            found = await computer_control.click_on(content)
            if found:
                await message.answer(f"Clicked: <code>{content}</code>", parse_mode="HTML")
            else:
                await message.answer(f"Not found on screen: <code>{content}</code>", parse_mode="HTML")
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
                f"Monitor started: <b>{desc}</b> every {m.group(2)} min\n"
                f"ID: <code>{task_id}</code> — cancel with <code>/cancel {task_id}</code>",
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

    elif action == "help":
        await cmd_start(message)

    else:
        await _execute_task(message, content)


# ── Task Execution ─────────────────────────────────────────────────────────────

async def _execute_task(message: Message, task: str) -> None:
    """Auto-detect agent, inject thread context, run task, store result."""
    original_task = task
    agent_key = agents.detect_agent(task)
    model = agents.get_model(agent_key)
    uid = message.from_user.id
    tid = current_thread.get(uid)

    if tid:
        ctx = agents.get_thread_context(tid)
        if ctx:
            task = f"{ctx}\n\nCurrent task: {task}"

    await message.answer(
        f"Routing to <b>{agent_key}</b> (<code>{model}</code>)…",
        parse_mode="HTML",
    )

    try:
        result = await interpreter_bridge.run_task(model, task, agent_key)
    except Exception as exc:
        logger.exception("Primary agent failed: %s", exc)
        fallback = agents.get_model(agent_key, use_fallback=True)
        if fallback and fallback != model:
            await message.answer(
                f"⚠️ Primary failed, trying fallback: <code>{fallback}</code>",
                parse_mode="HTML",
            )
            try:
                result = await interpreter_bridge.run_task(fallback, task, agent_key)
            except Exception as fb_exc:
                result = f"Both agents failed.\nPrimary: {exc}\nFallback: {fb_exc}"
        else:
            result = f"Error: {exc}"

    if tid:
        agents.add_to_thread(tid, agent_key, original_task, result)

    await _send_chunks(message, result)


# ── Entrypoint ─────────────────────────────────────────────────────────────────

async def main() -> None:
    """Start bot polling."""
    logger.info("LegionSwarm starting — polling for updates")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
