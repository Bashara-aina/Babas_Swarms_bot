"""Legion — Telegram PC control bot.

Core modes:
  Natural language → auto-routed (chat or computer control)
  /do <task>       → full agentic computer use (sees screen, clicks, types, opens apps)
  /run <task>      → LLM chat only (no computer use)
  /cmd <shell>     → raw shell command
  /screen          → screenshot → optional AI analysis
  /think <query>   → QwQ reasoning mode
  /open <app>      → open app or URL
  /click <x> <y>   → click at coordinates
  /type <text>     → type text
  /key <combo>     → keyboard shortcut
  /install <pkgs>  → pip install + restart
  /upgrade         → git pull + restart
  /agent <key> <t> → force specific agent
  /models          → agent roster
  /keys            → API key status
  /stats           → CPU/GPU/RAM
  /git             → git status
  /threads         → conversation threads
  /scrape <url>    → scrape a webpage
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
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

# ── Load env FIRST before any module reads os.getenv() ──────────────────────
load_dotenv(Path(__file__).parent / ".env")

import router as agents
import llm_client
import computer_agent
from llm_client import (
    agent_loop,
    chat,
    chunk_output,
    run_shell_command,
    verify_api_keys,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
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
_last_screenshot: dict[int, str] = {}  # user_id → screenshot path for analyze button
_scheduler = None  # initialized in on_startup


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


# ── Helper: send chunked messages ────────────────────────────────────────────
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
            # Fallback: strip HTML and send as plain text
            await msg.answer(chunk, reply_markup=markup)
        if not is_last:
            await asyncio.sleep(0.3)


# ── Helper: typing indicator ─────────────────────────────────────────────────
async def _keep_typing(msg: Message) -> None:
    while True:
        try:
            await bot.send_chat_action(msg.chat.id, "typing")
        except Exception:
            pass
        await asyncio.sleep(4)


# ── Helper: key status string ─────────────────────────────────────────────────
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


# ── /start ────────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status = verify_api_keys()
    active = sum(1 for v in status.values() if v)
    uptime = int(time.time() - _start_time)
    h, m = uptime // 3600, (uptime % 3600) // 60

    text = (
        f"yo Bas 👋 Legion's up — {h}h {m}m | {active}/6 keys\n\n"
        "<b>computer control</b>\n"
        "  <code>/do &lt;task&gt;</code>      — autonomous: sees screen, clicks, types, opens apps\n"
        "  <code>/screen</code>          — grab desktop screenshot\n"
        "  <code>/open &lt;app/url&gt;</code>  — open anything\n"
        "  <code>/click &lt;x&gt; &lt;y&gt;</code>    — click at coordinates\n"
        "  <code>/type &lt;text&gt;</code>     — type keyboard\n"
        "  <code>/key &lt;combo&gt;</code>     — keyboard shortcut\n"
        "  <code>/cmd &lt;shell&gt;</code>     — run shell command\n\n"
        "<b>AI agents</b>\n"
        "  <code>/run &lt;task&gt;</code>      — chat only (no computer use)\n"
        "  <code>/think &lt;query&gt;</code>   — force QwQ reasoning\n"
        "  <code>/agent &lt;key&gt; &lt;task&gt;</code>\n\n"
        "<b>self-management</b>\n"
        "  <code>/install &lt;packages&gt;</code> — pip install + restart\n"
        "  <code>/upgrade</code>          — git pull + restart\n\n"
        "<b>web &amp; research</b>\n"
        "  <code>/scrape &lt;url&gt;</code>    — JS-rendered page scrape\n"
        "  <code>/research &lt;topic&gt;</code> — deep multi-page research\n\n"
        "<b>system</b>\n"
        "  <code>/stats</code>  <code>/git</code>  <code>/models</code>  <code>/keys</code>\n\n"
        "or just type naturally — i'll figure it out."
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=main_keyboard())


# ── /do — Agentic computer control ───────────────────────────────────────────
@dp.message(Command("do"))
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
@dp.message(Command("screen"))
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
@dp.message(Command("open"))
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
@dp.message(Command("click"))
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
@dp.message(Command("type"))
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
@dp.message(Command("key"))
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
@dp.message(Command("cmd"))
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


# ── /think ────────────────────────────────────────────────────────────────────
@dp.message(Command("think"))
async def cmd_think(msg: Message) -> None:
    if not is_allowed(msg):
        return
    query = (msg.text or "").removeprefix("/think").strip()
    if not query:
        await msg.answer(
            "usage: <code>/think &lt;hard question&gt;</code>\n"
            "forces QwQ-32b with visible reasoning chain",
            parse_mode="HTML",
        )
        return
    await _execute_chat(msg, query, forced_agent="debug", show_thinking=True)


# ── /run ──────────────────────────────────────────────────────────────────────
@dp.message(Command("run"))
async def cmd_run(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/run").strip()
    if not task:
        await msg.answer(
            "usage: <code>/run &lt;task&gt;</code>  — LLM chat only, no computer access\n"
            "for full computer control use <code>/do &lt;task&gt;</code>",
            parse_mode="HTML",
        )
        return
    await _execute_chat(msg, task)


# ── /agent ────────────────────────────────────────────────────────────────────
@dp.message(Command("agent"))
async def cmd_agent(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split(maxsplit=2)
    if len(parts) < 3:
        valid = ", ".join(agents.AGENT_MODELS.keys())
        await msg.answer(
            f"usage: <code>/agent &lt;key&gt; &lt;task&gt;</code>\nkeys: <code>{valid}</code>",
            parse_mode="HTML",
        )
        return
    key, task = parts[1].lower(), parts[2]
    if key not in agents.AGENT_MODELS:
        await msg.answer(f"unknown agent: <code>{key}</code>", parse_mode="HTML")
        return
    await _execute_chat(msg, task, forced_agent=key)


# ── /install ──────────────────────────────────────────────────────────────────
@dp.message(Command("install"))
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

    # Show install output
    await status_msg.edit_text(
        f"📦 install output:\n<pre>{result[:2000]}</pre>\n\n🔄 restarting bot…",
        parse_mode="HTML",
    )

    await asyncio.sleep(2)  # Give Telegram time to send the message

    # Restart so new packages are loaded
    await msg.answer("back in a sec 👋")
    computer_agent.restart_bot()


# ── /upgrade ──────────────────────────────────────────────────────────────────
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("⬆️ pulling latest from GitHub…")

    result = await computer_agent.upgrade_from_git()
    await status_msg.edit_text(
        f"<b>git pull</b>\n<pre>{result}</pre>\n\n🔄 restarting…",
        parse_mode="HTML",
    )

    # Check if anything changed
    if "Already up to date" in result:
        await status_msg.edit_text(
            f"<b>git pull</b>\n<pre>{result}</pre>\nalready up to date, no restart needed.",
            parse_mode="HTML",
        )
        return

    await asyncio.sleep(2)
    await msg.answer("restarting with updates 🔄")
    computer_agent.restart_bot()


# ── /keys ─────────────────────────────────────────────────────────────────────
@dp.message(Command("keys"))
async def cmd_keys(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(_key_status(), parse_mode="HTML")


# ── /models ───────────────────────────────────────────────────────────────────
@dp.message(Command("models"))
async def cmd_models(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(
        f"{agents.list_agents()}\n\n{_key_status()}",
        parse_mode="HTML",
    )


# ── /stats ────────────────────────────────────────────────────────────────────
@dp.message(Command("stats"))
async def cmd_stats(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("pulling stats…")
    cpu, mem, gpu, disk, display = await asyncio.gather(
        run_shell_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", timeout=5),
        run_shell_command("free -h | grep Mem", timeout=5),
        run_shell_command(
            "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu"
            " --format=csv,noheader,nounits 2>/dev/null || echo 'No GPU'",
            timeout=5,
        ),
        run_shell_command("df -h / | tail -1", timeout=5),
        computer_agent.detect_display(),
    )
    uptime = int(time.time() - _start_time)
    text = (
        f"<b>📊 system</b>\n\n"
        f"⏱ bot up: {uptime // 3600}h {(uptime % 3600) // 60}m\n"
        f"🖥 cpu: <code>{cpu.strip()}%</code>\n"
        f"🖥 display: <code>{display}</code>\n"
        f"💾 mem:\n<pre>{mem.strip()}</pre>\n"
        f"🎮 gpu:\n<pre>{gpu.strip()}</pre>\n"
        f"💿 disk:\n<pre>{disk.strip()}</pre>"
    )
    await status_msg.edit_text(text, parse_mode="HTML")


# ── /git ──────────────────────────────────────────────────────────────────────
@dp.message(Command("git"))
async def cmd_git(msg: Message) -> None:
    if not is_allowed(msg):
        return
    output = await run_shell_command(
        "cd ~/swarm-bot && git status --short && echo '---' && git log --oneline -5",
        timeout=10,
    )
    await msg.answer(f"<b>📁 git</b>\n\n<pre>{output}</pre>", parse_mode="HTML")


# ── /thread / /threads ────────────────────────────────────────────────────────
@dp.message(Command("thread"))
async def cmd_thread(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/thread").strip()
    if not name:
        current = _user_thread.get(msg.from_user.id, "none")
        await msg.answer(
            f"current thread: <b>{current}</b>\nuse: <code>/thread &lt;name&gt;</code>",
            parse_mode="HTML",
        )
        return
    _user_thread[msg.from_user.id] = name
    await msg.answer(f"📌 thread: <b>{name}</b>", parse_mode="HTML")


@dp.message(Command("threads"))
async def cmd_threads(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(agents.list_threads(), parse_mode="HTML")


# ── /scrape ───────────────────────────────────────────────────────────────────
@dp.message(Command("scrape"))
async def cmd_scrape(msg: Message) -> None:
    if not is_allowed(msg):
        return
    url = (msg.text or "").removeprefix("/scrape").strip()
    if not url:
        await msg.answer("usage: <code>/scrape &lt;url&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer(f"🔍 scraping <code>{url}</code>…", parse_mode="HTML")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from tools.web_browser import browse_url
        result = await browse_url(url)
        typing_task.cancel()
        await status_msg.delete()

        title = result.get("title", "")
        text = result.get("text", "")[:3500]
        screenshot_path = result.get("screenshot_path", "")

        if screenshot_path and Path(screenshot_path).exists():
            _last_screenshot[msg.from_user.id] = screenshot_path
            await msg.answer_photo(
                photo=FSInputFile(screenshot_path),
                caption=f"🌐 {title[:100]}" if title else "🌐 page screenshot",
            )

        await msg.answer(
            f"<b>🌐 {title}</b>\n\n<pre>{text}</pre>",
            parse_mode="HTML",
        )
    except Exception as e:
        typing_task.cancel()
        # Fallback to curl-based scraping if Playwright not installed
        output = await run_shell_command(
            f"curl -sL --max-time 15 --user-agent 'Mozilla/5.0' '{url}' | "
            "python3 -c \""
            "import sys; from html.parser import HTMLParser\n"
            "class P(HTMLParser):\n"
            "    def __init__(self): super().__init__(); self.d=[]; self.skip=False\n"
            "    def handle_starttag(self,t,a): self.skip=t in('script','style','head')\n"
            "    def handle_endtag(self,t): self.skip=False\n"
            "    def handle_data(self,d):\n"
            "        if not self.skip and d.strip(): self.d.append(d.strip())\n"
            "p=P(); p.feed(sys.stdin.read()); print('\\n'.join(p.d[:100]))"
            "\"",
            timeout=25,
        )
        await status_msg.delete()
        await msg.answer(
            f"<b>🌐 {url}</b>\n\n<pre>{output[:3500]}</pre>",
            parse_mode="HTML",
        )


# ── /research ────────────────────────────────────────────────────────────────
@dp.message(Command("research"))
async def cmd_research(msg: Message) -> None:
    if not is_allowed(msg):
        return
    topic = (msg.text or "").removeprefix("/research").strip()
    if not topic:
        await msg.answer(
            "usage: <code>/research &lt;topic&gt;</code>\n\n"
            "deep multi-page web research — searches, visits pages, "
            "extracts and compiles findings.\n\n"
            "examples:\n"
            "<code>/research latest pytorch transformer architectures</code>\n"
            "<code>/research padang food delivery market jakarta 2026</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer(f"🔬 researching: <i>{topic[:80]}</i>…", parse_mode="HTML")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from tools.web_browser import deep_research
        result = await deep_research(topic)
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="playwright+web")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(
            f"research failed: <code>{e}</code>\n\n"
            "make sure Playwright is installed:\n"
            "<code>/install playwright</code> then <code>playwright install chromium</code>",
            parse_mode="HTML",
        )


# ── /monitor — background recurring task ─────────────────────────────────────
@dp.message(Command("monitor"))
async def cmd_monitor(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/monitor").strip()
    if not text:
        await msg.answer(
            "usage: <code>/monitor &lt;seconds&gt; &lt;command&gt;</code>\n\n"
            "runs a command every N seconds in the background.\n\n"
            "examples:\n"
            "<code>/monitor 60 nvidia-smi</code>\n"
            "<code>/monitor 300 df -h /</code>\n\n"
            "add alert condition with --alert:\n"
            "<code>/monitor 120 nvidia-smi --alert \"'90' in result\"</code>",
            parse_mode="HTML",
        )
        return

    # Parse: <seconds> <command> [--alert "<condition>"]
    alert_cond = ""
    if "--alert" in text:
        parts = text.split("--alert", 1)
        text = parts[0].strip()
        alert_cond = parts[1].strip().strip("'\"")

    words = text.split(maxsplit=1)
    if len(words) < 2:
        await msg.answer("need both interval and command", parse_mode="HTML")
        return

    try:
        interval = int(words[0])
    except ValueError:
        await msg.answer("first argument must be interval in seconds", parse_mode="HTML")
        return

    command = words[1]
    global _scheduler
    if not _scheduler:
        await msg.answer("scheduler not initialized — try restarting bot")
        return

    task_id = await _scheduler.add_monitor(
        description=command[:50],
        command=command,
        interval_sec=interval,
        alert_condition=alert_cond,
    )
    interval_str = f"{interval}s" if interval < 60 else f"{interval // 60}m"
    response = f"🟢 monitor started: <code>{task_id}</code>\n  ↻ <code>{command}</code> every {interval_str}"
    if alert_cond:
        response += f"\n  🔔 alert: <code>{alert_cond}</code>"
    await msg.answer(response, parse_mode="HTML")


# ── /schedule — one-time future task ─────────────────────────────────────────
@dp.message(Command("schedule"))
async def cmd_schedule(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/schedule").strip()
    if not text:
        await msg.answer(
            "usage: <code>/schedule &lt;minutes&gt; &lt;command&gt;</code>\n\n"
            "runs a command once after N minutes.\n\n"
            "examples:\n"
            "<code>/schedule 30 python3 ~/train.py</code>\n"
            "<code>/schedule 5 echo 'reminder: standup meeting'</code>",
            parse_mode="HTML",
        )
        return

    words = text.split(maxsplit=1)
    if len(words) < 2:
        await msg.answer("need both delay (minutes) and command")
        return

    try:
        minutes = int(words[0])
    except ValueError:
        await msg.answer("first argument must be delay in minutes")
        return

    command = words[1]
    run_at = time.time() + (minutes * 60)
    global _scheduler
    if not _scheduler:
        await msg.answer("scheduler not initialized")
        return

    task_id = await _scheduler.add_scheduled(
        description=command[:50],
        command=command,
        run_at=run_at,
    )
    await msg.answer(
        f"⏰ scheduled: <code>{task_id}</code>\n"
        f"  will run in {minutes}m: <code>{command}</code>",
        parse_mode="HTML",
    )


# ── /tasks — list background tasks ──────────────────────────────────────────
@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message) -> None:
    if not is_allowed(msg):
        return
    global _scheduler
    if not _scheduler:
        await msg.answer("scheduler not initialized")
        return
    result = await _scheduler.list_tasks()
    await msg.answer(result, parse_mode="HTML")


# ── /cancel — cancel a background task ──────────────────────────────────────
@dp.message(Command("cancel"))
async def cmd_cancel(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task_id = (msg.text or "").removeprefix("/cancel").strip()
    if not task_id:
        await msg.answer("usage: <code>/cancel &lt;task_id&gt;</code>", parse_mode="HTML")
        return
    global _scheduler
    if not _scheduler:
        await msg.answer("scheduler not initialized")
        return
    result = await _scheduler.cancel(task_id)
    await msg.answer(f"❌ {result}")


# ── /swarm — multi-agent parallel execution ──────────────────────────────────
@dp.message(Command("swarm"))
async def cmd_swarm(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/swarm").strip()
    if not task:
        await msg.answer(
            "usage: <code>/swarm &lt;complex task&gt;</code>\n\n"
            "decomposes the task into sub-tasks and runs multiple "
            "AI agents in parallel.\n\n"
            "examples:\n"
            "<code>/swarm write a FastAPI endpoint with tests and documentation</code>\n"
            "<code>/swarm analyze my codebase and suggest improvements</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("🧠 decomposing task…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    async def on_progress(step_text: str) -> None:
        try:
            await status_msg.edit_text(step_text, parse_mode="HTML")
        except Exception:
            pass

    try:
        from tools.orchestrator import smart_route
        result, model = await smart_route(task, progress_cb=on_progress)
        typing_task.cancel()

        if result:
            await status_msg.delete()
            await send_chunked(msg, result, model_used=model)
        else:
            # Fall back to regular agent loop
            await status_msg.edit_text("single-agent task — routing to /do…")
            typing_task.cancel()
            await _run_agent_loop(msg, task)
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"swarm error: <code>{e}</code>", parse_mode="HTML")


# ── /email — email management ────────────────────────────────────────────────
@dp.message(Command("email"))
async def cmd_email(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/email").strip()

    if not text:
        # Default: summarize inbox
        status_msg = await msg.answer("📧 checking inbox…")
        typing_task = asyncio.create_task(_keep_typing(msg))
        try:
            from tools.email_client import check_inbox
            result = await check_inbox(limit=10, unread_only=True)
            typing_task.cancel()
            await status_msg.delete()
            await msg.answer(
                f"<pre>{result[:3800]}</pre>",
                parse_mode="HTML",
            )
        except Exception as e:
            typing_task.cancel()
            await status_msg.edit_text(f"email error: <code>{e}</code>", parse_mode="HTML")
        return

    parts = text.split(maxsplit=1)
    subcmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if subcmd == "check":
        status_msg = await msg.answer("📧 checking…")
        from tools.email_client import check_inbox
        result = await check_inbox(limit=10, unread_only="unread" in arg or not arg)
        await status_msg.delete()
        await msg.answer(f"<pre>{result[:3800]}</pre>", parse_mode="HTML")

    elif subcmd == "read" and arg:
        status_msg = await msg.answer("📧 reading…")
        from tools.email_client import read_email
        result = await read_email(arg.strip())
        await status_msg.delete()
        await send_chunked(msg, result, model_used="email")

    elif subcmd == "search" and arg:
        status_msg = await msg.answer(f"🔍 searching: {arg}…")
        from tools.email_client import search_emails
        result = await search_emails(arg.strip())
        await status_msg.delete()
        await msg.answer(f"<pre>{result[:3800]}</pre>", parse_mode="HTML")

    else:
        await msg.answer(
            "usage:\n"
            "  <code>/email</code>           — show unread\n"
            "  <code>/email check</code>     — list unread\n"
            "  <code>/email read &lt;uid&gt;</code>  — read email\n"
            "  <code>/email search &lt;q&gt;</code>  — search by subject\n\n"
            "or use <code>/do check my email</code> for AI-powered inbox management",
            parse_mode="HTML",
        )


# ── /alert — conditional recurring alert ──────────────────────────────────────
@dp.message(Command("alert"))
async def cmd_alert(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/alert").strip()

    if not text:
        await msg.answer(
            "usage: <code>/alert &lt;name&gt; &lt;seconds&gt; &lt;command&gt; --if &lt;condition&gt;</code>\n\n"
            "examples:\n"
            "<code>/alert gpu-temp 120 nvidia-smi --if \"'80' in result\"</code>\n"
            "<code>/alert disk 3600 df -h / --if \"'9' in result.split()[4]\"</code>\n"
            "<code>/alert high-mem 300 free -m --if \"int(result.split()[8]) < 1000\"</code>\n\n"
            "condition has access to <code>result</code> (command output string)\n"
            "alert triggers when condition evaluates to True",
            parse_mode="HTML",
        )
        return

    # Parse: name seconds command --if condition
    if "--if" not in text:
        await msg.answer(
            "missing <code>--if</code> condition\n\n"
            "example: <code>/alert gpu 120 nvidia-smi --if \"'80' in result\"</code>",
            parse_mode="HTML",
        )
        return

    before_if, condition = text.split("--if", 1)
    condition = condition.strip().strip("\"'")
    parts = before_if.strip().split(maxsplit=2)

    if len(parts) < 3:
        await msg.answer(
            "usage: <code>/alert &lt;name&gt; &lt;seconds&gt; &lt;command&gt; --if &lt;condition&gt;</code>",
            parse_mode="HTML",
        )
        return

    name = parts[0]
    try:
        interval = int(parts[1])
    except ValueError:
        await msg.answer("interval must be a number (seconds)")
        return

    command = parts[2]

    if not _scheduler:
        await msg.answer("scheduler not initialized — check bot logs")
        return

    task_id = await _scheduler.add_monitor(
        description=f"Alert: {name}",
        command=command,
        interval_sec=interval,
        alert_condition=condition,
    )
    from tools.scheduler import _format_interval
    await msg.answer(
        f"🔔 Alert <code>{name}</code> created\n"
        f"  ID: <code>{task_id}</code>\n"
        f"  Check every: {_format_interval(interval)}\n"
        f"  Command: <code>{command}</code>\n"
        f"  Alert when: <code>{condition}</code>\n\n"
        f"cancel with <code>/cancel {task_id}</code>",
        parse_mode="HTML",
    )


# ── /maintenance — full system health check ───────────────────────────────────
@dp.message(Command("maintenance"))
async def cmd_maintenance(msg: Message) -> None:
    if not is_allowed(msg):
        return

    status_msg = await msg.answer("🏥 running full system health check…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from tools.system_maintenance import full_maintenance_check
        result = await full_maintenance_check()
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="maintenance")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(
            f"maintenance check failed: <code>{e}</code>",
            parse_mode="HTML",
        )


# ── Keyboard button shortcuts ─────────────────────────────────────────────────
@dp.message(F.text == "🖥 Do task")
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


@dp.message(F.text == "📸 Screenshot")
async def kbd_screenshot(msg: Message) -> None:
    if is_allowed(msg):
        await cmd_screen(msg)


@dp.message(F.text == "⚡ Shell")
async def kbd_shell_hint(msg: Message) -> None:
    if is_allowed(msg):
        await msg.answer(
            "type: <code>/cmd &lt;command&gt;</code>\ne.g. <code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )


@dp.message(F.text == "⚙️ Status")
async def kbd_status(msg: Message) -> None:
    if is_allowed(msg):
        await cmd_stats(msg)


@dp.message(F.text.in_({"🐛 Debug", "💻 Code"}))
async def kbd_agent_hint(msg: Message) -> None:
    if not is_allowed(msg):
        return
    key = "debug" if "Debug" in msg.text else "coding"
    await msg.answer(
        f"<b>{key}</b> mode — just type your task:",
        parse_mode="HTML",
    )


# ── Callbacks ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("fb:"))
async def cb_feedback(cb: CallbackQuery) -> None:
    action = cb.data.split(":")[1]
    responses = {
        "good":  "👍 nice",
        "retry": "re-send your message to retry",
        "info":  "provider shown in button label",
    }
    await cb.answer(responses.get(action, "ok"))


@dp.callback_query(F.data == "screen:analyze")
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

        # Cleanup
        try:
            Path(path).unlink(missing_ok=True)
            del _last_screenshot[cb.from_user.id]
        except Exception:
            pass
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"analysis failed: <code>{e}</code>", parse_mode="HTML")


@dp.callback_query(F.data == "screen:do")
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


# ── Natural language catch-all ────────────────────────────────────────────────
@dp.message(F.text)
async def handle_nl(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").strip()
    if not task or task.startswith("/"):
        return

    # Detect if this is a computer-use request
    computer_keywords = [
        # English — desktop
        "open", "launch", "click", "type", "press", "drag", "scroll",
        "screenshot", "screen", "what's on", "what is on",
        "check on my computer", "check on the computer", "show me",
        "whatsapp", "browser", "chrome", "firefox", "email", "gmail",
        "supabase", "telegram", "vscode", "folder", "file manager",
        # English — web research & browsing
        "search for", "search the web", "research", "find online",
        "look up", "browse to", "scrape", "go to website",
        "booking", "buy online", "purchase", "order online",
        # Documents & files
        "read pdf", "read excel", "extract table", "ocr", "read docx",
        "organize files", "find files", "baca dokumen",
        # Git & dev
        "git status", "git commit", "git push", "git pull", "git diff",
        "run tests", "pytest", "lint", "format code", "find in code",
        # System
        "disk space", "memory usage", "check services", "maintenance",
        "system cleanup", "gpu health",
        # Indonesian
        "buka", "klik", "ketik", "screenshot", "layar", "komputer",
        "cek langsung", "tolong cek", "lihat di", "buka whatsapp",
        "buka browser", "tampilkan", "show", "periksa",
        "cari di internet", "riset", "cari online",
    ]

    task_lower = task.lower()
    is_computer_task = any(kw in task_lower for kw in computer_keywords)

    if is_computer_task:
        await _run_agent_loop(msg, task)
    else:
        await _execute_chat(msg, task)


# ── Core: agentic loop handler ────────────────────────────────────────────────
async def _run_agent_loop(msg: Message, task: str) -> None:
    """Run the agentic computer-use loop with live progress updates."""
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
            # Store for analyze button
            _last_screenshot[msg.from_user.id] = path
        except Exception as e:
            logger.error("Failed to send screenshot photo: %s", e)

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
        err = str(e)
        hint = ""
        if "rate" in err.lower():
            hint = "\n\nrate limited — try again in a minute"
        elif "key" in err.lower() or "auth" in err.lower():
            hint = "\n\napi key issue — check /keys"
        await status_msg.edit_text(
            f"<code>{err[:500]}</code>{hint}",
            parse_mode="HTML",
        )


# ── Core: single-turn chat handler ────────────────────────────────────────────
async def _execute_chat(
    msg: Message,
    task: str,
    forced_agent: Optional[str] = None,
    show_thinking: bool = False,
) -> None:
    """Single LLM call without computer tool use."""
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
        err = str(e)
        hint = ""
        if "All models exhausted" in err:
            hint = "\n\nall providers failed — check /keys"
        elif "Auth error" in err:
            hint = "\n\nbad api key — check /keys"
        await status_msg.edit_text(
            f"<code>{err[:400]}</code>{hint}",
            parse_mode="HTML",
        )


# ── Startup ───────────────────────────────────────────────────────────────────
async def on_startup() -> None:
    # Initialize persistence and scheduler
    global _scheduler
    try:
        from tools.persistence import init_db
        from tools.scheduler import TaskScheduler
        await init_db()
        _scheduler = TaskScheduler(bot, ALLOWED_USER_ID)
        await _scheduler.start()
        logger.info("Scheduler initialized")
    except Exception as e:
        logger.warning("Scheduler init failed (non-fatal): %s", e)

    await bot.set_my_commands([
        BotCommand(command="do",      description="Autonomous computer control"),
        BotCommand(command="screen",  description="Take desktop screenshot"),
        BotCommand(command="open",    description="Open app or URL"),
        BotCommand(command="click",   description="Click at x,y coordinates"),
        BotCommand(command="type",    description="Type text on keyboard"),
        BotCommand(command="key",     description="Press keyboard shortcut"),
        BotCommand(command="cmd",     description="Run shell command"),
        BotCommand(command="run",     description="LLM chat (no computer)"),
        BotCommand(command="think",   description="QwQ deep reasoning"),
        BotCommand(command="agent",   description="Force specific agent"),
        BotCommand(command="install", description="pip install + restart"),
        BotCommand(command="upgrade", description="git pull + restart"),
        BotCommand(command="models",  description="Agent roster"),
        BotCommand(command="keys",    description="API key status"),
        BotCommand(command="stats",   description="CPU/GPU/RAM"),
        BotCommand(command="git",     description="Git status"),
        BotCommand(command="threads", description="Conversation threads"),
        BotCommand(command="scrape",   description="Scrape a URL (JS-rendered)"),
        BotCommand(command="research", description="Deep multi-page web research"),
        BotCommand(command="swarm",    description="Multi-agent parallel execution"),
        BotCommand(command="email",    description="Email inbox management"),
        BotCommand(command="monitor",  description="Background recurring task"),
        BotCommand(command="schedule", description="One-time scheduled task"),
        BotCommand(command="tasks",    description="List background tasks"),
        BotCommand(command="cancel",      description="Cancel a background task"),
        BotCommand(command="alert",       description="Conditional recurring alert"),
        BotCommand(command="maintenance", description="Full system health check"),
        BotCommand(command="start",       description="Help + status"),
    ])

    key_status = verify_api_keys()
    active = [k for k, v in key_status.items() if v]
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]

    # Detect display at startup
    display = await computer_agent.detect_display()

    logger.info("=" * 55)
    logger.info("Legion v2 starting")
    logger.info("✅ Keys: %s", ", ".join(active) or "NONE")
    logger.info("🖥 Display: %s", display)
    if not any(key_status.get(k) for k in cloud):
        logger.critical("NO CLOUD KEYS — all requests will fail!")
    logger.info("=" * 55)


async def main() -> None:
    dp.startup.register(on_startup)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
