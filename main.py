# /home/newadmin/swarm-bot/main.py
"""LegionSwarm — Telegram bot entrypoint.

Commands:
    /start          — Show help menu
    /run <task>     — Auto-detect agent by keyword and execute
    /agent <n> <t>  — Force a specific agent
    /scrape <url>   — Scrape page text via Playwright
    /shot <url>     — Screenshot a URL, send as photo
    /models         — Show active agent roster
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from dotenv import load_dotenv

import agents
import interpreter_bridge
import playwright_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Secrets ──────────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
_raw_uid = os.getenv("ALLOWED_USER_ID", "")
ALLOWED_USER_ID: int = int(_raw_uid) if _raw_uid.isdigit() else 0

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")
if not ALLOWED_USER_ID:
    raise RuntimeError("ALLOWED_USER_ID not set or invalid in .env")

# ── Bot setup ─────────────────────────────────────────────────────────────────

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# ── Auth guard ────────────────────────────────────────────────────────────────

def _authorized(message: Message) -> bool:
    """Return True only if the sender is the configured ALLOWED_USER_ID."""
    return message.from_user is not None and message.from_user.id == ALLOWED_USER_ID


async def _deny(message: Message) -> None:
    """Silently ignore unauthorized requests (no reply)."""
    logger.warning("Unauthorized access attempt from user_id=%s", message.from_user and message.from_user.id)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _send_chunks(message: Message, text: str) -> None:
    """Send text split into ≤4000-char chunks as HTML messages.

    Args:
        message: Originating message (used to reply into the same chat).
        text: Full output text to send.
    """
    chunks = interpreter_bridge.chunk_output(text)
    for chunk in chunks:
        await message.answer(f"<pre>{chunk}</pre>", parse_mode="HTML")


# ── Handlers ──────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Show help menu."""
    if not _authorized(message):
        await _deny(message)
        return

    help_text = (
        "<b>LegionSwarm</b> — Local AI Swarm Control\n\n"
        "<b>/run</b> <i>&lt;task&gt;</i> — auto-route to best agent\n"
        "<b>/agent</b> <i>&lt;name&gt; &lt;task&gt;</i> — force a specific agent\n"
        "<b>/scrape</b> <i>&lt;url&gt;</i> — extract page text\n"
        "<b>/shot</b> <i>&lt;url&gt;</i> — take a screenshot\n"
        "<b>/models</b> — show agent roster\n\n"
        f"Agents: {', '.join(agents.AGENT_MODELS.keys())}"
    )
    await message.answer(help_text, parse_mode="HTML")


@dp.message(Command("models"))
async def cmd_models(message: Message) -> None:
    """Show the active agent roster."""
    if not _authorized(message):
        await _deny(message)
        return
    await message.answer(agents.list_agents(), parse_mode="HTML")


@dp.message(Command("run"))
async def cmd_run(message: Message) -> None:
    """Auto-detect agent by keyword and run the task.

    Usage: /run <task description>
    """
    if not _authorized(message):
        await _deny(message)
        return

    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Usage: <code>/run &lt;task&gt;</code>", parse_mode="HTML")
        return

    task = args[1].strip()
    agent_key = agents.detect_agent(task)
    model = agents.get_model(agent_key)

    await message.answer(
        f"Routing to <b>{agent_key}</b> (<code>{model}</code>)…",
        parse_mode="HTML",
    )

    try:
        result = await interpreter_bridge.run_task(model, task)
    except Exception as exc:
        logger.exception("run_task failed: %s", exc)
        result = f"Error: {exc}"

    await _send_chunks(message, result)


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
        roster = ", ".join(agents.AGENT_MODELS.keys())
        await message.answer(
            f"Usage: <code>/agent &lt;name&gt; &lt;task&gt;</code>\nAgents: {roster}",
            parse_mode="HTML",
        )
        return

    agent_key = args[1].strip().lower()
    task = args[2].strip()
    model = agents.get_model(agent_key)

    if model is None:
        roster = ", ".join(agents.AGENT_MODELS.keys())
        await message.answer(
            f"Unknown agent <b>{agent_key}</b>. Available: {roster}",
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"Using <b>{agent_key}</b> (<code>{model}</code>)…",
        parse_mode="HTML",
    )

    try:
        result = await interpreter_bridge.run_task(model, task)
    except Exception as exc:
        logger.exception("agent run_task failed: %s", exc)
        result = f"Error: {exc}"

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
    if len(args) < 2 or not args[1].strip():
        await message.answer("Usage: <code>/scrape &lt;url&gt;</code>", parse_mode="HTML")
        return

    url = args[1].strip()
    await message.answer(f"Scraping <code>{url}</code>…", parse_mode="HTML")

    try:
        text = await playwright_agent.scrape(url)
    except Exception as exc:
        logger.exception("scrape failed: %s", exc)
        text = f"Error: {exc}"

    await _send_chunks(message, text)


@dp.message(Command("shot"))
async def cmd_shot(message: Message) -> None:
    """Take a screenshot of a URL and send it as a photo.

    Usage: /shot <url>
    """
    if not _authorized(message):
        await _deny(message)
        return

    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Usage: <code>/shot &lt;url&gt;</code>", parse_mode="HTML")
        return

    url = args[1].strip()
    await message.answer(f"Screenshotting <code>{url}</code>…", parse_mode="HTML")

    tmp_path: Path | None = None
    try:
        tmp_path = await playwright_agent.screenshot(url)
        image_bytes = tmp_path.read_bytes()
        await message.answer_photo(
            BufferedInputFile(image_bytes, filename="screenshot.png"),
            caption=url,
        )
    except Exception as exc:
        logger.exception("screenshot failed: %s", exc)
        await message.answer(f"Screenshot failed: {exc}", parse_mode="HTML")
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


# ── Entrypoint ────────────────────────────────────────────────────────────────

async def main() -> None:
    """Start the bot and begin polling."""
    logger.info("LegionSwarm starting — polling for updates")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
