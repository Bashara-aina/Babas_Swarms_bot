"""BabasSwarms — Telegram bot for PC control via cloud AI agents.

Commands:
    /start              - Help + status panel
    /run <task>         - Auto-route task to best agent
    /agent <key> <task> - Force a specific agent
    /cmd <shell>        - Execute shell command on your PC
    /screen             - Take desktop screenshot + optional AI analysis
    /think <query>      - Force QwQ reasoning model (shows thinking)
    /models             - Show agent roster + API key status
    /keys               - Check which API keys are loaded
    /thread <name>      - Switch conversation thread
    /threads            - List active threads
    /git                - Git status of workspace
    /stats              - System stats (CPU, GPU, RAM)
    /scrape <url>       - Scrape page text

Natural language works without slash commands too.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

# Load .env FIRST — before any module reads os.getenv()
load_dotenv(Path(__file__).parent / ".env")

import router as agents  # 'agents/' is a package dir; router.py has our routing logic
import llm_client
from llm_client import chat, chunk_output, run_shell_command, verify_api_keys

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

if not BOT_TOKEN:
    logger.critical("TELEGRAM_BOT_TOKEN not set in .env")
    sys.exit(1)
if not ALLOWED_USER_ID:
    logger.critical("ALLOWED_USER_ID not set in .env")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

_user_thread: dict[int, str] = {}
_start_time = time.time()

# Store last screenshot path per user for the "analyze" button
_last_screenshot: dict[int, str] = {}


# ── Auth ─────────────────────────────────────────────────────────────────────
def is_allowed(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id == ALLOWED_USER_ID


# ── UI helpers ────────────────────────────────────────────────────────────────
def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🐛 Debug"),
                KeyboardButton(text="💻 Code"),
                KeyboardButton(text="📊 Analyze"),
            ],
            [
                KeyboardButton(text="📸 Screenshot"),
                KeyboardButton(text="📌 Threads"),
                KeyboardButton(text="⚙️ Status"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Ask anything or use /run <task>…",
    )


def result_keyboard(model_used: str) -> InlineKeyboardMarkup:
    # Show a short provider label, strip long model paths
    parts = model_used.split("/")
    provider = parts[0].upper() if parts else "AI"
    if provider == "OLLAMA_CHAT":
        provider = "OLLAMA🔒"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👍", callback_data="fb:good"),
        InlineKeyboardButton(text="🔄 retry", callback_data="fb:retry"),
        InlineKeyboardButton(text=f"via {provider}", callback_data="fb:info"),
    ]])


def screenshot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔍 Analyze this", callback_data="screen:analyze"),
    ]])


async def send_chunked(message: Message, text: str, model_used: str = "") -> None:
    chunks = chunk_output(text, max_length=4000)
    for i, chunk in enumerate(chunks):
        is_last = (i == len(chunks) - 1)
        markup = result_keyboard(model_used) if (is_last and model_used) else None
        await message.answer(chunk, parse_mode="HTML", reply_markup=markup)
        if not is_last:
            await asyncio.sleep(0.3)


async def _keep_typing(message: Message) -> None:
    while True:
        try:
            await bot.send_chat_action(message.chat.id, "typing")
        except Exception:
            pass
        await asyncio.sleep(4)


def _format_keys_status() -> str:
    status = verify_api_keys()
    lines = ["<b>🔑 API Keys</b>\n"]
    names = {
        "CEREBRAS_API_KEY":   "Cerebras   ⚡ 1,500 tok/s",
        "GROQ_API_KEY":       "Groq       🚀 241 tok/s",
        "GEMINI_API_KEY":     "Gemini     📚 1M context",
        "OPENROUTER_API_KEY": "OpenRouter  🔀 24+ free models",
        "ZAI_API_KEY":        "ZAI/GLM-4  🧠 debug+math specialist",
        "HF_TOKEN":           "HuggingFace 🤗 (optional)",
    }
    for env_var, label in names.items():
        icon = "✅" if status.get(env_var) else "❌"
        lines.append(f"  {icon} {label}")
    lines.append("")
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]
    if any(status.get(k) for k in cloud):
        lines.append("cloud APIs active ✓")
    else:
        lines.append("⚠️ <b>No cloud keys!</b> Add to .env")
    return "\n".join(lines)


# ── Commands ──────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not is_allowed(message):
        return
    status = verify_api_keys()
    active = sum(1 for v in status.values() if v)
    uptime = int(time.time() - _start_time)
    h, m = uptime // 3600, (uptime % 3600) // 60

    text = (
        "yo Bas 👋 Legion's up.\n\n"
        f"⏱ uptime <code>{h}h {m}m</code>  |  🔑 keys <code>{active}/6</code>\n\n"
        "<b>what i can do</b>\n"
        "  <code>/run &lt;task&gt;</code>   — route to best agent\n"
        "  <code>/cmd &lt;shell&gt;</code>  — run shell on your PC\n"
        "  <code>/agent &lt;key&gt; &lt;task&gt;</code> — force an agent\n"
        "  <code>/screen</code>     — grab desktop screenshot\n"
        "  <code>/think &lt;query&gt;</code> — QwQ deep reasoning\n"
        "  <code>/models</code>    — who's in the roster\n"
        "  <code>/stats</code>     — CPU/GPU/RAM\n"
        "  <code>/git</code>       — git status\n"
        "  <code>/scrape &lt;url&gt;</code> — scrape a URL\n\n"
        "or just type naturally, i'll figure it out."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())


@dp.message(Command("keys"))
async def cmd_keys(message: Message) -> None:
    if not is_allowed(message):
        return
    await message.answer(_format_keys_status(), parse_mode="HTML")


@dp.message(Command("models"))
async def cmd_models(message: Message) -> None:
    if not is_allowed(message):
        return
    await message.answer(
        f"{agents.list_agents()}\n\n{_format_keys_status()}",
        parse_mode="HTML",
    )


@dp.message(Command("run"))
async def cmd_run(message: Message) -> None:
    if not is_allowed(message):
        return
    task = (message.text or "").removeprefix("/run").strip()
    if not task:
        await message.answer(
            "usage: <code>/run &lt;task&gt;</code>\ne.g. <code>/run debug this CUDA OOM error</code>",
            parse_mode="HTML",
        )
        return
    await _execute(message, task)


@dp.message(Command("agent"))
async def cmd_agent(message: Message) -> None:
    if not is_allowed(message):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        valid = ", ".join(agents.AGENT_MODELS.keys())
        await message.answer(
            f"usage: <code>/agent &lt;key&gt; &lt;task&gt;</code>\nkeys: <code>{valid}</code>",
            parse_mode="HTML",
        )
        return
    key, task = parts[1].lower(), parts[2]
    if key not in agents.AGENT_MODELS:
        await message.answer(
            f"unknown agent: <code>{key}</code>",
            parse_mode="HTML",
        )
        return
    await _execute(message, task, forced_agent=key)


@dp.message(Command("cmd"))
async def cmd_shell(message: Message) -> None:
    if not is_allowed(message):
        return
    cmd = (message.text or "").removeprefix("/cmd").strip()
    if not cmd:
        await message.answer(
            "usage: <code>/cmd &lt;shell command&gt;</code>\ne.g. <code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )
        return
    # Block obviously destructive patterns
    dangerous = ["rm -rf /", "mkfs", ":(){:|:&};:", "> /dev/sda"]
    for d in dangerous:
        if d in cmd:
            await message.answer(
                f"nope, blocked: <code>{d}</code>",
                parse_mode="HTML",
            )
            return
    status_msg = await message.answer(f"<code>$ {cmd}</code>", parse_mode="HTML")
    output = await run_shell_command(cmd, timeout=30)
    await status_msg.delete()
    await message.answer(
        f"<code>$ {cmd}</code>\n\n<pre>{output[:3800]}</pre>",
        parse_mode="HTML",
    )


@dp.message(Command("screen"))
async def cmd_screen(message: Message) -> None:
    if not is_allowed(message):
        return
    status_msg = await message.answer("📸 grabbing screen…")
    try:
        path = await llm_client.take_screenshot()
        if not path:
            await status_msg.edit_text(
                "couldn't grab screen. make sure scrot or imagemagick is installed:\n"
                "<code>sudo apt install scrot</code>",
                parse_mode="HTML",
            )
            return

        await status_msg.delete()

        # Store for the analyze callback
        _last_screenshot[message.from_user.id] = path

        # Send screenshot as photo
        photo_file = FSInputFile(path)
        await message.answer_photo(
            photo=photo_file,
            caption="🖥 desktop grabbed — hit Analyze to let me describe it",
            reply_markup=screenshot_keyboard(),
        )

    except Exception as e:
        await status_msg.edit_text(
            f"screenshot failed: <code>{e}</code>",
            parse_mode="HTML",
        )


@dp.message(Command("think"))
async def cmd_think(message: Message) -> None:
    """Force QwQ-32b reasoning model with visible thinking steps."""
    if not is_allowed(message):
        return
    query = (message.text or "").removeprefix("/think").strip()
    if not query:
        await message.answer(
            "usage: <code>/think &lt;hard question&gt;</code>\n\n"
            "forces QwQ-32b reasoning — shows the thinking process",
            parse_mode="HTML",
        )
        return
    await _execute(message, query, forced_agent="debug", show_thinking=True)


@dp.message(Command("git"))
async def cmd_git(message: Message) -> None:
    if not is_allowed(message):
        return
    output = await run_shell_command(
        "cd ~/swarm-bot && git status --short && git log --oneline -5",
        timeout=10,
    )
    await message.answer(
        f"<b>📁 git</b>\n\n<pre>{output}</pre>",
        parse_mode="HTML",
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_allowed(message):
        return
    status_msg = await message.answer("pulling stats…")
    cpu, mem, gpu, disk = await asyncio.gather(
        run_shell_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", timeout=5),
        run_shell_command("free -h | grep Mem", timeout=5),
        run_shell_command(
            "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu"
            " --format=csv,noheader,nounits 2>/dev/null || echo 'No GPU'",
            timeout=5,
        ),
        run_shell_command("df -h / | tail -1", timeout=5),
    )
    uptime = int(time.time() - _start_time)
    text = (
        f"<b>📊 system</b>\n\n"
        f"⏱ bot up: {uptime // 3600}h {(uptime % 3600) // 60}m\n"
        f"🖥 cpu: <code>{cpu.strip()}%</code>\n"
        f"💾 mem:\n<pre>{mem.strip()}</pre>\n"
        f"🎮 gpu:\n<pre>{gpu.strip()}</pre>\n"
        f"💿 disk:\n<pre>{disk.strip()}</pre>"
    )
    await status_msg.edit_text(text, parse_mode="HTML")


@dp.message(Command("thread"))
async def cmd_thread(message: Message) -> None:
    if not is_allowed(message):
        return
    name = (message.text or "").removeprefix("/thread").strip()
    if not name:
        current = _user_thread.get(message.from_user.id, "none")
        await message.answer(
            f"current thread: <b>{current}</b>\nuse: <code>/thread &lt;name&gt;</code>",
            parse_mode="HTML",
        )
        return
    _user_thread[message.from_user.id] = name
    await message.answer(f"📌 thread: <b>{name}</b>", parse_mode="HTML")


@dp.message(Command("threads"))
async def cmd_threads(message: Message) -> None:
    if not is_allowed(message):
        return
    await message.answer(agents.list_threads(), parse_mode="HTML")


@dp.message(Command("scrape"))
async def cmd_scrape(message: Message) -> None:
    if not is_allowed(message):
        return
    url = (message.text or "").removeprefix("/scrape").strip()
    if not url:
        await message.answer("usage: <code>/scrape &lt;url&gt;</code>", parse_mode="HTML")
        return
    status_msg = await message.answer(f"🔍 scraping <code>{url}</code>…", parse_mode="HTML")
    output = await run_shell_command(
        f"curl -sL --max-time 15 '{url}' | "
        "python3 -c \""
        "import sys; from html.parser import HTMLParser; "
        "class P(HTMLParser):\n"
        "    def __init__(self): super().__init__(); self.d=[]; self.skip=False\n"
        "    def handle_starttag(self,t,a): self.skip=t in('script','style')\n"
        "    def handle_endtag(self,t): self.skip=False\n"
        "    def handle_data(self,d):\n"
        "        if not self.skip and d.strip(): self.d.append(d.strip())\n"
        "p=P(); p.feed(sys.stdin.read()); print('\\n'.join(p.d[:80]))"
        "\"",
        timeout=20,
    )
    await status_msg.delete()
    await message.answer(
        f"<b>🌐 {url}</b>\n\n<pre>{output[:3000]}</pre>",
        parse_mode="HTML",
    )


# ── Keyboard shortcuts ────────────────────────────────────────────────────────

@dp.message(F.text == "⚙️ Status")
async def kbd_status(message: Message) -> None:
    if is_allowed(message):
        await cmd_stats(message)


@dp.message(F.text == "📌 Threads")
async def kbd_threads(message: Message) -> None:
    if is_allowed(message):
        await cmd_threads(message)


@dp.message(F.text == "📸 Screenshot")
async def kbd_screenshot(message: Message) -> None:
    if is_allowed(message):
        await cmd_screen(message)


@dp.message(F.text == "⚡ Shell")
async def kbd_shell_hint(message: Message) -> None:
    if is_allowed(message):
        await message.answer(
            "type: <code>/cmd &lt;command&gt;</code>\n\ne.g.\n"
            "<code>/cmd ps aux | grep python</code>\n"
            "<code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )


@dp.message(F.text.in_({"🐛 Debug", "💻 Code", "📊 Analyze"}))
async def kbd_agent_hint(message: Message) -> None:
    if not is_allowed(message):
        return
    shortcut_map = {"🐛 Debug": "debug", "💻 Code": "coding", "📊 Analyze": "analyst"}
    key = shortcut_map.get(message.text, "general")
    await message.answer(
        f"ok, <b>{key}</b> agent locked in.\njust type your task or: <code>/agent {key} &lt;task&gt;</code>",
        parse_mode="HTML",
    )


# ── Callbacks ─────────────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("fb:"))
async def cb_feedback(callback: CallbackQuery) -> None:
    action = callback.data.split(":")[1]
    if action == "good":
        await callback.answer("nice 👍")
    elif action == "retry":
        await callback.answer("re-send your message to try again")
    elif action == "info":
        await callback.answer("model info shown in button label")


@dp.callback_query(F.data == "screen:analyze")
async def cb_analyze_screenshot(callback: CallbackQuery) -> None:
    if callback.from_user.id != ALLOWED_USER_ID:
        await callback.answer("not authorized")
        return

    user_id = callback.from_user.id
    path = _last_screenshot.get(user_id)
    if not path or not Path(path).exists():
        await callback.answer("screenshot expired — grab a new one with /screen")
        return

    await callback.answer("analyzing…")
    status_msg = await callback.message.answer("🔍 analyzing screenshot…")

    typing_task = asyncio.create_task(_keep_typing(callback.message))
    try:
        analysis, model_used = await llm_client.analyze_screenshot(
            path, question="Describe what's on screen. What apps are open? Any errors? What's Bas doing?"
        )
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(callback.message, analysis, model_used=model_used)

        # Clean up tmp file
        try:
            Path(path).unlink(missing_ok=True)
            del _last_screenshot[user_id]
        except Exception:
            pass

    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(
            f"analysis failed: <code>{e}</code>",
            parse_mode="HTML",
        )


# ── Natural language catch-all ────────────────────────────────────────────────

@dp.message(F.text)
async def handle_nl(message: Message) -> None:
    if not is_allowed(message):
        return
    task = (message.text or "").strip()
    if not task or task.startswith("/"):
        return
    await _execute(message, task)


# ── Core execution ────────────────────────────────────────────────────────────

async def _execute(
    message: Message,
    task: str,
    forced_agent: Optional[str] = None,
    show_thinking: bool = False,
) -> None:
    agent_key = forced_agent or agents.detect_agent(task)
    thread_id = _user_thread.get(message.from_user.id)

    # Casual status — no more "🤖 SENIOR_PYTHON_DEV" robotic stuff
    agent_labels = {
        "coding":    "💻 coding…",
        "debug":     "🐛 debugging…",
        "math":      "📐 calculating…",
        "architect": "🏗 designing…",
        "analyst":   "📊 analyzing…",
        "vision":    "👁 looking…",
        "general":   "⚡ thinking…",
    }
    label = agent_labels.get(agent_key, "⚡ thinking…")
    status_msg = await message.answer(label)
    typing_task = asyncio.create_task(_keep_typing(message))

    try:
        response, model_used = await llm_client.chat(
            task,
            agent_key=agent_key,
            thread_id=thread_id,
            show_thinking=show_thinking,
        )
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(message, response, model_used=model_used)

    except Exception as e:
        typing_task.cancel()
        err = str(e)
        # Give useful hints on common errors
        hint = ""
        if "All models exhausted" in err:
            hint = "\n\nall providers failed — run <code>/keys</code> to check"
        elif "Auth error" in err:
            hint = "\n\nbad API key — check <code>/keys</code>"
        await status_msg.edit_text(
            f"<code>{err[:400]}</code>{hint}",
            parse_mode="HTML",
        )


# ── Startup ───────────────────────────────────────────────────────────────────

async def on_startup() -> None:
    await bot.set_my_commands([
        BotCommand(command="start",   description="Help + status"),
        BotCommand(command="run",     description="Auto-route a task"),
        BotCommand(command="cmd",     description="Run shell command"),
        BotCommand(command="screen",  description="Take desktop screenshot"),
        BotCommand(command="think",   description="QwQ deep reasoning"),
        BotCommand(command="agent",   description="Force specific agent"),
        BotCommand(command="models",  description="Agent roster"),
        BotCommand(command="keys",    description="API key status"),
        BotCommand(command="stats",   description="CPU/GPU/RAM stats"),
        BotCommand(command="git",     description="Git status"),
        BotCommand(command="thread",  description="Switch thread"),
        BotCommand(command="threads", description="List threads"),
        BotCommand(command="scrape",  description="Scrape a URL"),
    ])
    key_status = verify_api_keys()
    active = [k for k, v in key_status.items() if v]
    missing = [k for k, v in key_status.items() if not v]
    logger.info("=" * 55)
    logger.info("Legion starting up")
    logger.info("✅ Keys: %s", ", ".join(active) or "NONE")
    if missing:
        logger.warning("❌ Missing: %s", ", ".join(missing))
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]
    if not any(key_status.get(k) for k in cloud):
        logger.critical("NO CLOUD KEYS — every request will fail!")
    logger.info("=" * 55)


async def main() -> None:
    dp.startup.register(on_startup)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
