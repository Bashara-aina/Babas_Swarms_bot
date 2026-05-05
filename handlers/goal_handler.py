"""
handlers/goal_handler.py
Telegram handler for the /goal autonomous delivery system.
Provides /goal, /goal_status, and /goal_stop commands.
"""

import asyncio
import os
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from tools.goal_runner import run_goal


router = Router()


# Authorized user check — only Bashara can run /goal (it runs code locally!)
def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to run /goal commands."""
    authorized_ids_str = os.getenv("TELEGRAM_AUTHORIZED_USER_ID", "0")
    if not authorized_ids_str or authorized_ids_str == "0":
        # No auth set — allow for now (should be set in production)
        return True
    try:
        authorized_ids = [int(x.strip()) for x in authorized_ids_str.split(",")]
        return user_id in authorized_ids
    except ValueError:
        return False


async def goal_command_handler(message: Message) -> None:
    """
    /goal <description>
    Autonomously delivers a feature or project using mini-SWE-agent.
    Runs for hours/days in background. Reports progress via Telegram.
    """
    user_id = message.from_user.id

    if not is_authorized(user_id):
        await message.reply(
            "❌ Unauthorized. /goal is restricted to authorized users only."
        )
        return

    args = message.text.split(" ", 1)
    if len(args) < 2 or not args[1].strip():
        await message.reply(
            "📋 *Usage:* `/goal <description>`\n\n"
            "Examples:\n"
            "• `/goal Build the Rumahlabuh property search page`\n"
            "• `/goal Add BPJS calculator to Wajar Slip`\n"
            "• `/goal Fix all failing tests in tools/`\n\n"
            "The agent runs autonomously and reports back when done.\n\n"
            "⚠️ *Cost limit:* $5 per goal (configurable)\n"
            "💡 *Tip:* Use /goal_status to check progress",
            parse_mode="Markdown"
        )
        return

    goal = args[1].strip()
    chat_id = message.chat.id

    await message.reply(
        f"🎯 *Goal queued:*\n`{goal}`\n\n"
        f"⚙️ Running autonomously in background. I'll message you with progress "
        f"and when it's done.\n\n"
        f"💰 Cost limit: $5 (default)\n"
        f"📋 Status: /goal_status\n"
        f"⛔ Stop: /goal_stop",
        parse_mode="Markdown"
    )

    # Run goal in background (non-blocking)
    asyncio.create_task(
        run_goal_background(goal, chat_id, message.bot)
    )


async def run_goal_background(goal: str, chat_id: int, bot) -> None:
    """Background wrapper that handles errors gracefully."""
    try:
        await run_goal(goal, chat_id=str(chat_id), bot=bot)
    except Exception as e:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ *Goal execution error:*\n`{str(e)[:500]}`",
                parse_mode="Markdown"
            )
        except Exception:
            pass


async def goal_status_handler(message: Message) -> None:
    """/goal_status — Show current goal runner status."""
    status_file = Path(".goal/STATUS.md")
    if status_file.exists():
        status = status_file.read_text()
        await message.reply(f"📊 *Goal Status:*\n\n{status}", parse_mode="Markdown")
    else:
        await message.reply("✅ No goal currently running.")


async def goal_stop_handler(message: Message) -> None:
    """/goal_stop — Stop the current goal run."""
    stop_signal = Path(".goal/STOP_SIGNAL")
    stop_signal.touch()
    await message.reply(
        "⛔ *Stop signal sent.*\n\n"
        "Current task will finish, then the goal will halt.\n"
        "Use /goal_status to monitor progress.",
        parse_mode="Markdown"
    )


def register_goal_handlers() -> Router:
    """Register all goal handlers with the router."""
    router.message.register(goal_command_handler, Command("goal", prefix="/"))
    router.message.register(goal_status_handler, Command("goal_status", prefix="/"))
    router.message.register(goal_stop_handler, Command("goal_stop", prefix="/"))
    return router