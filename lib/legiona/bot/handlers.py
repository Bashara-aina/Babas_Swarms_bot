"""
lib/legiona/bot/handlers.py
Minimal aiogram 3.24 router for Legiona bot streaming.
Wires /run and /think commands to stream_response().
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
from typing import Any

import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Update

from pathlib import Path as _Path

from lib.legiona.bot.stream_handler import stream_to_telegram
from lib.legiona.minimax_client import MINIMAX_MODEL, complete_with_tools
from lib.legiona.self_evolve import RULES_FILE, evolve, load_evolved_rules, GLOBAL_MEMORY_FILE
from lib.legiona.tools.registry import TOOL_SCHEMAS
from lib.legiona.tools.mmx_tools import mmx_vision
from lib.legiona.debate import debate
from lib.legiona.observability.cost_log import today_total_jpy

_logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

router = Router()


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text, quote=False)


def _require_owner(func):
    """Decorator: reject messages from non-owners."""
    async def wrapper(message: Message, *args: Any, **kwargs: Any) -> Any:
        if message.from_user.id != ALLOWED_USER_ID:
            _logger.warning("Unauthorized access attempt from %s", message.from_user.id)
            return None
        return await func(message, *args, **kwargs)
    return wrapper


@router.message(F.text & Command("run"))
@_require_owner
async def cmd_run(message: Message, command: CommandObject, state: FSMContext) -> None:
    """
    /run <prompt> — Stream an agent response with tools.
    Progressive edits via Telegram send_message + edit_message_text.
    """
    if not BOT_TOKEN:
        await message.answer("[ERROR] TELEGRAM_BOT_TOKEN not configured")
        return

    prompt = command.args or ""
    if not prompt.strip():
        await message.answer("Usage: /run <prompt>")
        return

    status_msg = await message.answer("🤖 Processing...")
    chat_id = message.chat.id

    messages = [
        {"role": "system", "content": "You are Legiona, Bashara's AI coworker."},
        {"role": "user", "content": prompt},
    ]

    try:
        result = await stream_to_telegram(
            messages=messages,
            bot_token=BOT_TOKEN,
            chat_id=chat_id,
            preset="coding",
        )
        # Final result already sent via progressive edits
        _logger.info("[cmd_run] stream complete, %d chars", len(result))
    except Exception as exc:
        _logger.error("[cmd_run] stream failed: %s", exc)
        await status_msg.edit_text(f"[ERROR] {type(exc).__name__}: {exc}")


@router.message(F.text & Command("think"))
@_require_owner
async def cmd_think(message: Message, command: CommandObject, state: FSMContext) -> None:
    """
    /think <prompt> — Direct M2.7 completion without tools.
    Uses standard send_message (no streaming).
    """
    if not BOT_TOKEN:
        await message.answer("[ERROR] TELEGRAM_BOT_TOKEN not configured")
        return

    prompt = command.args or ""
    if not prompt.strip():
        await message.answer("Usage: /think <prompt>")
        return

    status_msg = await message.answer("🧠 Thinking...")
    chat_id = message.chat.id

    messages = [
        {"role": "system", "content": "You are Legiona, Bashara's AI coworker."},
        {"role": "user", "content": prompt},
    ]

    try:
        result = await _sync_complete(messages)
        await status_msg.edit_text(_escape(result.answer[:4096]), parse_mode="HTML")
    except Exception as exc:
        _logger.error("[cmd_think] failed: %s", exc)
        await status_msg.edit_text(f"[ERROR] {type(exc).__name__}: {exc}")


@router.message(F.text & Command("evolve"))
@_require_owner
async def cmd_evolve(message: Message) -> None:
    """Trigger self-evolution from last 5 sessions."""
    await message.answer("⚙️ Running self-evolution...")
    new_rule = evolve(last_n=5)
    if new_rule:
        await message.answer(f"✅ New rule added:\n\n`{new_rule}`", parse_mode="Markdown")
    else:
        await message.answer("ℹ️ No new rules — not enough session history yet.")


@router.message(F.text & Command("rules"))
@_require_owner
async def cmd_rules(message: Message) -> None:
    """Show current evolved rules."""
    rules = RULES_FILE.read_text() if RULES_FILE.exists() else "(no rules yet)"
    if len(rules) > 3800:
        rules = rules[:3800] + "\n...(truncated)"
    await message.answer(f"📋 **Evolved Rules:**\n\n{rules}", parse_mode="Markdown")


@router.message(F.text & Command("memory"))
@_require_owner
async def cmd_memory(message: Message) -> None:
    """Show global memory preview."""
    memory = GLOBAL_MEMORY_FILE.read_text()[:2000] if GLOBAL_MEMORY_FILE.exists() else "(empty)"
    await message.answer(f"🧠 **Global Memory (preview):**\n\n{memory}", parse_mode="Markdown")


@router.message(F.text & Command("cost"))
@_require_owner
async def cmd_cost(message: Message) -> None:
    """Show today's M2.7 spend in ¥."""
    total = today_total_jpy()
    await message.answer(f"💴 **Today's M2.7 cost:** ¥{total:.2f}")


@router.message(F.text & Command("debate"))
@_require_owner
async def cmd_debate(message: Message, command: CommandObject) -> None:
    """Run 3-agent debate: /debate your question."""
    question = command.args or ""
    if not question.strip():
        await message.answer("Usage: /debate your question here")
        return
    await message.answer(f"⚖️ Running 3-agent debate on:\n_{question}_", parse_mode="Markdown")
    try:
        verdict = await debate(question)
        await message.answer(
            f"**Verdict** (confidence: {verdict.confidence}):\n\n{verdict.answer[:4000]}",
            parse_mode="Markdown",
        )
    except Exception as exc:
        _logger.error("[cmd_debate] failed: %s", exc)
        await message.answer(f"[ERROR] {type(exc).__name__}: {exc}")


@router.message(F.text & Command("status"))
@_require_owner
async def cmd_status(message: Message) -> None:
    """Show Legiona system status."""
    rules_count = 0
    if RULES_FILE.exists():
        rules_count = len(RULES_FILE.read_text().splitlines())
    await message.answer(
        f"🤖 **Legiona M2.7 Status**\n\n"
        f"-  Model: `MiniMax-M2.7`\n"
        f"-  Tools: {len(TOOL_SCHEMAS)}\n"
        f"-  Evolved rules: ~{rules_count} lines\n"
        f"-  Today's cost: ¥{today_total_jpy():.2f}\n"
        f"-  Temperature: 1.0 ✓\n"
        f"-  reasoning_split: True ✓",
        parse_mode="Markdown",
    )


@router.message(F.text & Command("vision"))
@_require_owner
async def cmd_vision(message: Message, command: CommandObject) -> None:
    """
    /vision [--prompt "text"] <image_path> — Analyze an image file with mmx vision.
    Use --prompt to set a custom prompt; otherwise uses a default description prompt.
    """
    if not BOT_TOKEN:
        await message.answer("[ERROR] TELEGRAM_BOT_TOKEN not configured")
        return

    args = command.args or ""
    if not args.strip():
        await message.answer("Usage: /vision [--prompt 'describe this'] /path/to/image.jpg")
        return

    # Parse --prompt flag
    prompt = "Describe this image in detail."
    image_path = args

    if args.startswith("--prompt"):
        parts = args.split(" --prompt ", 1)
        if len(parts) == 2:
            image_path = parts[0].strip()
            prompt = parts[1].strip().strip('"').strip("'")
        else:
            image_path = args.replace("--prompt", "").strip()

    status_msg = await message.answer("👁️ Analyzing...")
    image_path = image_path.strip()

    # Resolve relative paths
    if not image_path.startswith("/"):
        image_path = str(_Path("/home/newadmin/swarm-bot") / image_path)

    try:
        result = mmx_vision(image_path, prompt)
        if result.startswith("ERROR"):
            await status_msg.edit_text(f"Vision failed: {result}")
        else:
            await status_msg.edit_text(f"**Analysis:**\n\n{result[:4096]}", parse_mode="Markdown")
    except Exception as exc:
        _logger.error("[cmd_vision] failed: %s", exc)
        await status_msg.edit_text(f"[ERROR] {type(exc).__name__}: {exc}")


@router.message(F.photo)
@_require_owner
async def handle_vision_photo(message: Message, state: FSMContext) -> None:
    """
    Handle photo messages — run mmx vision analysis.
    Send photo first with a caption, then reply with M2.7 analysis.
    """
    if not BOT_TOKEN:
        await message.answer("[ERROR] TELEGRAM_BOT_TOKEN not configured")
        return

    status_msg = await message.answer("👁️ Analyzing image...")
    chat_id = message.chat.id
    bot = message.bot

    try:
        # Get largest photo size
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)

        # Download to temp file
        import tempfile
        suffix = f".{photo.file_id[:8]}.jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        await bot.download_file(file.file_path, tmp_path)

        # Default prompt — use caption if present
        prompt = message.caption or "Describe this image in detail."

        # Run mmx vision
        vision_result = mmx_vision(tmp_path, prompt)

        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        if vision_result.startswith("ERROR"):
            await status_msg.edit_text(f"Vision failed: {vision_result}")
            return

        # Send photo to user with caption
        await message.answer_photo(
            photo=photo.file_id,
            caption=f"**Vision Analysis:**\n\n{vision_result[:4096]}",
            parse_mode="Markdown",
        )
        await status_msg.delete()

    except Exception as exc:
        _logger.error("[handle_vision_photo] failed: %s", exc)
        await status_msg.edit_text(f"[ERROR] {type(exc).__name__}: {exc}")


async def _sync_complete(messages: list[dict[str, Any]]):
    """Run synchronous complete() in thread pool to avoid blocking event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: complete_with_tools(messages, tool_schemas=TOOL_SCHEMAS, preset="coding"),
    )


def create_dp() -> Dispatcher:
    """Build and return configured Dispatcher with Legiona router."""
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def create_bot() -> Bot:
    """Create and return configured Bot instance."""
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    return Bot(token=BOT_TOKEN)
