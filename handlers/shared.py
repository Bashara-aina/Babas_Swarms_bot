"""Shared state, helpers, and core runner functions for all handler modules."""
from __future__ import annotations

import asyncio
import html as html_mod
import time
from pathlib import Path
from typing import Optional

from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

import router as agents
import llm_client
from llm_client import agent_loop, chat, chunk_output, verify_api_keys

# ── Shared mutable state ──────────────────────────────────────────────────────
ALLOWED_USER_ID: int = 0          # set by main.py at startup
_user_thread: dict[int, str] = {}
_last_screenshot: dict[int, str] = {}
_start_time: float = time.time()

# Scheduler (initialised in on_startup)
_scheduler = None

# swarms_bot enterprise layer (initialised in on_startup)
_chief_of_staff = None
_cost_router = None
_budget_manager = None
_security_guard = None
_audit_logger = None
_evaluator = None
_session_manager = None
_cost_metrics = None


# ── Auth ──────────────────────────────────────────────────────────────────────
def is_allowed(msg: Message) -> bool:
    return msg.from_user is not None and msg.from_user.id == ALLOWED_USER_ID


def allowed_cb(cb: CallbackQuery) -> bool:
    return cb.from_user is not None and cb.from_user.id == ALLOWED_USER_ID


# ── UI components ─────────────────────────────────────────────────────────────
def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="\U0001f5a5 Do task"),
                KeyboardButton(text="\U0001f4f8 Screenshot"),
                KeyboardButton(text="\u26a1 Shell"),
            ],
            [
                KeyboardButton(text="\U0001f41b Debug"),
                KeyboardButton(text="\U0001f4bb Code"),
                KeyboardButton(text="\u2699\ufe0f Status"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Ask anything, or tap a button\u2026",
    )


def result_keyboard(model_used: str) -> InlineKeyboardMarkup:
    parts = model_used.split("/")
    provider = parts[0].upper()
    if provider == "OLLAMA_CHAT":
        provider = "LOCAL\U0001f512"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\U0001f44d", callback_data="fb:good"),
        InlineKeyboardButton(text="\U0001f504", callback_data="fb:retry"),
        InlineKeyboardButton(text=f"\u2191{provider}", callback_data="fb:info"),
    ]])


def screenshot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\U0001f50d Analyze screen", callback_data="screen:analyze"),
        InlineKeyboardButton(text="\U0001f5b1 Do task on screen", callback_data="screen:do"),
    ]])


# ── Helper: send chunked messages ─────────────────────────────────────────────
async def send_chunked(msg: Message, text: str, model_used: str = "") -> None:
    if not text:
        return
    chunks = chunk_output(text, max_length=4000)
    for i, chunk in enumerate(chunks):
        is_last = (i == len(chunks) - 1)
        markup = result_keyboard(model_used) if (is_last and model_used) else None
        try:
            await msg.answer(chunk, parse_mode="HTML", reply_markup=markup)
        except Exception:
            try:
                safe = html_mod.escape(chunk)
                await msg.answer(safe, parse_mode="HTML", reply_markup=markup)
            except Exception:
                await msg.answer(chunk, reply_markup=markup)
        if not is_last:
            await asyncio.sleep(0.3)


# ── Helper: typing indicator ──────────────────────────────────────────────────
async def _keep_typing(msg: Message) -> None:
    while True:
        try:
            await msg.bot.send_chat_action(msg.chat.id, "typing")
        except Exception:
            pass
        await asyncio.sleep(4)


# ── Helper: key status string ─────────────────────────────────────────────────
def _key_status() -> str:
    status = verify_api_keys()
    names = {
        "CEREBRAS_API_KEY":   "Cerebras   \u26a1 1,500 tok/s",
        "GROQ_API_KEY":       "Groq       \U0001f680 function calling",
        "GEMINI_API_KEY":     "Gemini     \U0001f4da 1M context",
        "OPENROUTER_API_KEY": "OpenRouter  \U0001f500 free models",
        "ZAI_API_KEY":        "ZAI/GLM-4  \U0001f9e0 debug+math",
        "HF_TOKEN":           "HuggingFace \U0001f917",
    }
    lines = ["<b>\U0001f511 API Keys</b>\n"]
    for k, label in names.items():
        icon = "\u2705" if status.get(k) else "\u274c"
        lines.append(f"  {icon} {label}")
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]
    lines.append("")
    lines.append("cloud active \u2713" if any(status.get(k) for k in cloud) else "\u26a0\ufe0f <b>no cloud keys!</b>")
    return "\n".join(lines)


# ── Core: agentic loop handler ────────────────────────────────────────────────
async def _run_agent_loop(msg: Message, task: str) -> None:
    """Run the agentic computer-use loop with live progress updates."""
    # FIX #5: Guard against msg.from_user being None (aiogram 3.x can send None for system messages)
    if not msg.from_user:
        return

    thread_id = _user_thread.get(msg.from_user.id)

    status_msg = await msg.answer("\U0001f916 on it\u2026")
    step_count = 0

    async def on_progress(step_text: str) -> None:
        nonlocal step_count
        step_count += 1
        try:
            await status_msg.edit_text(
                f"<code>[{step_count}]</code> {step_text}",
                parse_mode="HTML",
            )
        except Exception:
            pass

    async def on_photo(path: str) -> None:
        try:
            photo_file = FSInputFile(path)
            await msg.answer_photo(
                photo=photo_file,
                caption="\U0001f4f8 current screen",
                reply_markup=screenshot_keyboard(),
            )
            _last_screenshot[msg.from_user.id] = path
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to send screenshot photo: %s", e)

    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        response, model_used = await agent_loop(
            task,
            progress_cb=on_progress,
            photo_cb=on_photo,
            thread_id=thread_id,
        )
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, response, model_used=model_used)

    except Exception as e:
        typing_task.cancel()
        err = html_mod.escape(str(e))
        if "rate" in err.lower():
            hint = "\u23f3 rate limited \u2014 try again in a minute"
        elif "key" in err.lower() or "auth" in err.lower():
            hint = "\U0001f511 api key issue \u2014 run /keys to check"
        elif "all providers" in err.lower():
            hint = "\U0001f480 all models failed \u2014 run /keys to check"
        else:
            hint = "\u274c something went wrong"
        await status_msg.edit_text(
            f"{hint}\n\n<code>{err[:400]}</code>",
            parse_mode="HTML",
        )


# ── Core: single-turn chat handler ────────────────────────────────────────────
async def _execute_chat(
    msg: Message,
    task: str,
    forced_agent: Optional[str] = None,
    show_thinking: bool = False,
) -> None:
    """Single-turn LLM chat with typing indicator and chunked output."""
    # FIX #5: Guard against msg.from_user being None
    if not msg.from_user:
        return

    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        response, model_used = await chat(
            task,
            agent_key=forced_agent,
            show_thinking=show_thinking,
            user_id=str(msg.from_user.id),
        )
        typing_task.cancel()
        await send_chunked(msg, response, model_used=model_used)
    except Exception as e:
        typing_task.cancel()
        err = html_mod.escape(str(e))
        if "rate" in err.lower():
            hint = "\u23f3 rate limited"
        elif "key" in err.lower() or "auth" in err.lower():
            hint = "\U0001f511 api key issue"
        else:
            hint = "\u274c error"
        await msg.answer(
            f"{hint}: <code>{err[:400]}</code>",
            parse_mode="HTML",
        )
