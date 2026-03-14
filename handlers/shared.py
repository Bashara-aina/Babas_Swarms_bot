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

# ── Shared mutable state ──────────────────────────────────────────────────────────────
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


# ── Auth ─────────────────────────────────────────────────────────────────────────
def is_allowed(msg: Message) -> bool:
    return msg.from_user is not None and msg.from_user.id == ALLOWED_USER_ID


def allowed_cb(cb: CallbackQuery) -> bool:
    return cb.from_user is not None and cb.from_user.id == ALLOWED_USER_ID


# ── UI components ──────────────────────────────────────────────────────────────────
def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🖥 Do task"),
                KeyboardButton(text="📸 Screenshot"),
                KeyboardButton(text="⚡ Shell"),
            ],
            [
                KeyboardButton(text="🐛 Debug"),
                KeyboardButton(text="💻 Code"),
                KeyboardButton(text="⚙️ Status"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Ask anything, or tap a button…",
    )


def result_keyboard(model_used: str) -> InlineKeyboardMarkup:
    parts = model_used.split("/")
    provider = parts[0].upper()
    if provider == "OLLAMA_CHAT":
        provider = "LOCAL🔒"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👍", callback_data="fb:good"),
        InlineKeyboardButton(text="🔄", callback_data="fb:retry"),
        InlineKeyboardButton(text=f"↑{provider}", callback_data="fb:info"),
    ]])


def screenshot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔍 Analyze screen", callback_data="screen:analyze"),
        InlineKeyboardButton(text="🖱 Do task on screen", callback_data="screen:do"),
    ]])


# ── Helper: send chunked messages ─────────────────────────────────────────────────
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


# ── Helper: typing indicator ──────────────────────────────────────────────────────
async def _keep_typing(msg: Message) -> None:
    while True:
        try:
            await msg.bot.send_chat_action(msg.chat.id, "typing")
        except Exception:
            pass
        await asyncio.sleep(4)


# ── Helper: key status string ──────────────────────────────────────────────────────
def _key_status() -> str:
    status = verify_api_keys()
    names = {
        "CEREBRAS_API_KEY":   "Cerebras   ⚡ 1,500 tok/s",
        "GROQ_API_KEY":       "Groq       🚀 function calling",
        "GEMINI_API_KEY":     "Gemini     📚 1M context",
        "OPENROUTER_API_KEY": "OpenRouter  🔀 free models",
        "ZAI_API_KEY":        "ZAI/GLM-4  🧠 debug+math",
        "HF_TOKEN":           "HuggingFace 🤗",
    }
    lines = ["<b>🔑 API Keys</b>\n"]
    for k, label in names.items():
        icon = "✅" if status.get(k) else "❌"
        lines.append(f"  {icon} {label}")
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]
    lines.append("")
    lines.append("cloud active ✓" if any(status.get(k) for k in cloud) else "⚠️ <b>no cloud keys!</b>")
    return "\n".join(lines)


# ── Core: agentic loop handler ──────────────────────────────────────────────────────
async def _run_agent_loop(msg: Message, task: str) -> None:
    """Run the agentic computer-use loop with live progress updates."""
    # FIX #5: Guard against None from_user (e.g. channel posts or anonymous messages)
    if not msg.from_user:
        return

    thread_id = _user_thread.get(msg.from_user.id)

    status_msg = await msg.answer("🤖 on it…")
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
                caption="📸 current screen",
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
            hint = "⏳ rate limited — try again in a minute"
        elif "key" in err.lower() or "auth" in err.lower():
            hint = "🔑 api key issue — run /keys to check"
        elif "all providers" in err.lower():
            hint = "💀 all models failed — run /keys to check"
        else:
            hint = "❌ something went wrong"
        await status_msg.edit_text(
            f"{hint}\n\n<code>{err[:400]}</code>",
            parse_mode="HTML",
        )


# ── Core: single-turn chat handler ───────────────────────────────────────────────
async def _execute_chat(
    msg: Message,
    task: str,
    forced_agent: Optional[str] = None,
    show_thinking: bool = False,
) -> None:
    """Single LLM call without computer tool use."""
    # FIX #5: Guard against None from_user
    if not msg.from_user:
        return

    agent_key = forced_agent or agents.detect_agent(task)
    thread_id = _user_thread.get(msg.from_user.id)

    labels = {
        "coding":    "💻 coding…",
        "debug":     "🐛 debugging…",
        "math":      "📐 calculating…",
        "architect": "🏗 designing…",
        "analyst":   "📊 analyzing…",
        "vision":    "👁 looking…",
        "general":   "⚡ thinking…",
    }
    status_msg = await msg.answer(labels.get(agent_key, "⚡ thinking…"))
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        response, model_used = await chat(
            task,
            agent_key=agent_key,
            thread_id=thread_id,
            show_thinking=show_thinking,
        )
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, response, model_used=model_used)

    except Exception as e:
        typing_task.cancel()
        err = html_mod.escape(str(e))
        if "All models exhausted" in err or "all providers" in err.lower():
            hint = "💀 all models failed — run /keys to check"
        elif "Auth error" in err or "auth" in err.lower():
            hint = "🔑 bad api key — run /keys to check"
        elif "rate" in err.lower():
            hint = "⏳ rate limited — try again in a minute"
        else:
            hint = "❌ something went wrong"
        await status_msg.edit_text(
            f"{hint}\n\n<code>{err[:400]}</code>",
            parse_mode="HTML",
        )
