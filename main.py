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
import html as html_mod
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
            # HTML parse failed — escape entities and retry, then plain text fallback
            try:
                safe = html_mod.escape(chunk)
                await msg.answer(safe, parse_mode="HTML", reply_markup=markup)
            except Exception:
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
        f"yo Bas — Legion v4 up — {h}h {m}m | {active}/6 keys\n\n"
        "<b>computer control</b>\n"
        "  <code>/do</code> <code>/screen</code> <code>/open</code> <code>/click</code> <code>/type</code> <code>/key</code> <code>/cmd</code>\n\n"
        "<b>AI agents</b>\n"
        "  <code>/run</code>  <code>/think</code>  <code>/swarm</code>  <code>/agent</code>\n\n"
        "<b>research</b>\n"
        "  <code>/paper</code>  <code>/ask_paper</code>  <code>/workernet_papers</code>\n"
        "  <code>/scrape</code>  <code>/research</code>\n\n"
        "<b>second brain</b>\n"
        "  <code>/remember</code>  <code>/recall</code>  <code>/memories</code>  <code>/briefing</code>\n\n"
        "<b>dev tools</b>\n"
        "  <code>/scaffold</code>  <code>/build</code>  <code>/gpu</code>  <code>/vuln_scan</code>\n\n"
        "<b>tasks</b>\n"
        "  <code>/task_from</code>  <code>/tasks_due</code>  <code>/task_done</code>\n\n"
        "<b>content</b>\n"
        "  <code>/post</code>  <code>/brand_check</code>  <code>/delegate</code>\n\n"
        "<b>system</b>\n"
        "  <code>/stats</code>  <code>/git</code>  <code>/models</code>  <code>/keys</code>  <code>/maintenance</code>\n\n"
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


# ── /swarm — multi-agent team execution (v4) ──────────────────────────────────
@dp.message(Command("swarm"))
async def cmd_swarm(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/swarm").strip()
    if not task:
        await msg.answer(
            "usage: <code>/swarm &lt;complex task&gt;</code>\n\n"
            "decomposes task and runs specialist agents in parallel:\n"
            "strategist, developer, researcher, marketer, analyst, devops, pm\n\n"
            "examples:\n"
            "<code>/swarm analyze IKEA ASM codebase and suggest 3 improvements</code>\n"
            "<code>/swarm build a landing page with API and tests</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("strategist decomposing task...")
    typing_task = asyncio.create_task(_keep_typing(msg))

    async def on_progress(step_text: str) -> None:
        try:
            await status_msg.edit_text(step_text, parse_mode="HTML")
        except Exception:
            pass

    try:
        from tools.orchestrator import decompose_task, execute_parallel, synthesize_results
        subtasks = await decompose_task(task)
        agent_list = "\n".join(f"  [{s['agent']}] {s['task'][:60]}..." for s in subtasks)
        await status_msg.edit_text(
            f"running {len(subtasks)} agents:\n{agent_list}",
            parse_mode="HTML",
        )

        results = await execute_parallel(subtasks, progress_cb=on_progress)
        final = await synthesize_results(task, results, subtasks)

        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, final, model_used="swarm/multi-agent")
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


# ── /paper — arXiv paper search ────────────────────────────────────────────────
@dp.message(Command("paper"))
async def cmd_paper(msg: Message) -> None:
    if not is_allowed(msg):
        return
    query = (msg.text or "").removeprefix("/paper").strip()
    if not query:
        await msg.answer(
            "usage: <code>/paper &lt;query&gt;</code>\n\n"
            "searches arXiv and returns top 3 results.\n\n"
            "examples:\n"
            "<code>/paper Kendall multi-task learning uncertainty</code>\n"
            "<code>/paper FiLM visual reasoning conditioning</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer(f"searching arXiv: {query[:50]}...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.arxiv import search_arxiv
        papers = await search_arxiv(query, max_results=3)
        typing_task.cancel()
        await status_msg.delete()
        if not papers:
            await msg.answer("No papers found.")
            return
        for p in papers:
            text = (
                f"<b>{p['title'][:200]}</b>\n"
                f"<i>{p['authors']}</i> | {p['published']}\n\n"
                f"{p['abstract'][:400]}...\n\n"
                f"ID: <code>{p['arxiv_id']}</code>\n"
                f"PDF: {p['pdf_url']}"
            )
            try:
                await msg.answer(text, parse_mode="HTML")
            except Exception:
                await msg.answer(text)
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"arXiv error: <code>{e}</code>", parse_mode="HTML")


# ── /ask-paper — question about a specific paper ──────────────────────────────
@dp.message(Command("ask_paper"))
async def cmd_ask_paper(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/ask_paper").strip()
    if not text:
        await msg.answer(
            "usage: <code>/ask_paper &lt;arxiv_id&gt; &lt;question&gt;</code>\n\n"
            "example:\n"
            "<code>/ask_paper 1705.07115 is clamping log_var justified?</code>",
            parse_mode="HTML",
        )
        return
    parts = text.split(maxsplit=1)
    arxiv_id = parts[0]
    question = parts[1] if len(parts) > 1 else "Summarize the key contributions."
    status_msg = await msg.answer(f"downloading {arxiv_id}...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.arxiv import download_paper, extract_paper_text, analyze_paper
        pdf_path = await download_paper(arxiv_id)
        await status_msg.edit_text("extracting text...")
        paper_text = extract_paper_text(pdf_path)
        await status_msg.edit_text("analyzing...")
        analysis = await analyze_paper(paper_text, question)
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, analysis, model_used="debug/paper-analysis")
        # Auto-save to memory
        try:
            from tools.memory import auto_save_research
            await auto_save_research(analysis, arxiv_id)
        except Exception:
            pass
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"paper error: <code>{e}</code>", parse_mode="HTML")


# ── /workernet-papers — analyze all 6 WorkerNet papers ────────────────────────
@dp.message(Command("workernet_papers"))
async def cmd_workernet_papers(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("fetching 6 WorkerNet papers...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.arxiv import (
            WORKERNET_PAPERS, download_paper, extract_paper_text, analyze_paper,
        )
        for name, info in WORKERNET_PAPERS.items():
            try:
                await status_msg.edit_text(f"processing: {name}...")
                pdf_path = await download_paper(info["arxiv_id"])
                paper_text = extract_paper_text(pdf_path)
                question = f"How does this paper relate to implementing: {', '.join(info['implements'])}? Key equation: {info['key_equation']}"
                analysis = await analyze_paper(paper_text, question)
                header = (
                    f"<b>{name}</b> (arXiv:{info['arxiv_id']})\n"
                    f"Implements: <code>{', '.join(info['implements'])}</code>\n"
                    f"Key eq: <code>{info['key_equation']}</code>\n\n"
                )
                await send_chunked(msg, header + analysis, model_used="debug")
                # Auto-save
                try:
                    from tools.memory import auto_save_research
                    await auto_save_research(header + analysis, info["arxiv_id"])
                except Exception:
                    pass
            except Exception as e:
                await msg.answer(f"{name}: error — {e}")
        typing_task.cancel()
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /briefing — morning briefing ──────────────────────────────────────────────
@dp.message(Command("briefing"))
async def cmd_briefing(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("assembling briefing...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.briefing import generate_briefing
        briefing = await generate_briefing()
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, briefing, model_used="briefing")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"briefing error: <code>{e}</code>", parse_mode="HTML")


# ── /remember, /recall, /memories, /brain-export — second brain ───────────────
@dp.message(Command("remember"))
async def cmd_remember(msg: Message) -> None:
    if not is_allowed(msg):
        return
    note = (msg.text or "").removeprefix("/remember").strip()
    if not note:
        await msg.answer("usage: <code>/remember &lt;note&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.memory import add_memory
        note_id = await add_memory(note, source="telegram")
        await msg.answer(f"saved (id: {note_id})")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


@dp.message(Command("recall"))
async def cmd_recall(msg: Message) -> None:
    if not is_allowed(msg):
        return
    query = (msg.text or "").removeprefix("/recall").strip()
    if not query:
        await msg.answer("usage: <code>/recall &lt;query&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.memory import search_memory
        results = await search_memory(query, top_k=5)
        if not results:
            await msg.answer("no matching memories found.")
            return
        lines = ["<b>Matching memories:</b>\n"]
        for r in results:
            import time as _time
            ts = _time.strftime("%m/%d", _time.localtime(r["created_at"]))
            tags = f" [{r['tags']}]" if r.get("tags") else ""
            lines.append(f"  #{r['id']} ({ts}{tags}) rel:{r['relevance']}")
            lines.append(f"  {r['text'][:150]}...\n")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


@dp.message(Command("memories"))
async def cmd_memories(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.memory import get_recent_memories
        import time as _time
        notes = await get_recent_memories(limit=10)
        if not notes:
            await msg.answer("no memories saved yet. Use <code>/remember &lt;note&gt;</code>", parse_mode="HTML")
            return
        lines = ["<b>Recent memories:</b>\n"]
        for n in notes:
            ts = _time.strftime("%m/%d %H:%M", _time.localtime(n["created_at"]))
            tags = f" [{n['tags']}]" if n.get("tags") else ""
            lines.append(f"  #{n['id']} ({ts}{tags}) [{n['source']}]")
            lines.append(f"  {n['text'][:120]}...\n")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


@dp.message(Command("brain_export"))
async def cmd_brain_export(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("exporting to Obsidian vault...")
    try:
        from tools.memory import export_to_obsidian
        vault_path = str(Path.home() / "brain")
        result = await export_to_obsidian(vault_path)
        await status_msg.edit_text(result)
    except Exception as e:
        await status_msg.edit_text(f"export error: <code>{e}</code>", parse_mode="HTML")


# ── /scaffold, /build — project scaffolding ───────────────────────────────────
@dp.message(Command("scaffold"))
async def cmd_scaffold(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/scaffold").strip()
    if not text:
        await msg.answer(
            "usage: <code>/scaffold &lt;framework&gt; &lt;description&gt;</code>\n\n"
            "frameworks: nextjs, fastapi, laravel\n\n"
            "examples:\n"
            "<code>/scaffold nextjs personal portfolio with blog</code>\n"
            "<code>/scaffold fastapi todo API with JWT auth</code>",
            parse_mode="HTML",
        )
        return
    parts = text.split(maxsplit=1)
    framework = parts[0].lower()
    desc = parts[1] if len(parts) > 1 else framework

    # Extract features from description
    features = []
    desc_lower = desc.lower()
    if "auth" in desc_lower:
        features.append("auth")
    if "supabase" in desc_lower:
        features.append("supabase")
    if "database" in desc_lower or "db" in desc_lower:
        features.append("database")

    # Generate project name from description
    project_name = desc.split()[:3]
    project_name = "-".join(w.lower() for w in project_name if w.isalnum())[:30] or framework

    status_msg = await msg.answer(f"scaffolding {framework} project: {project_name}...")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from tools.scaffolder import scaffold_nextjs, scaffold_fastapi, scaffold_laravel
        if framework in ("nextjs", "next"):
            result = await scaffold_nextjs(project_name, features)
        elif framework in ("fastapi", "fast"):
            result = await scaffold_fastapi(project_name, features)
        elif framework == "laravel":
            result = await scaffold_laravel(project_name, features)
        else:
            typing_task.cancel()
            await status_msg.edit_text(f"unknown framework: {framework}\nSupported: nextjs, fastapi, laravel")
            return
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used=f"scaffold/{framework}")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"scaffold error: <code>{e}</code>", parse_mode="HTML")


@dp.message(Command("build"))
async def cmd_build(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/build").strip()
    if not task:
        await msg.answer(
            "usage: <code>/build &lt;task&gt;</code>\n\n"
            "runs frontend + backend agents in parallel.\n\n"
            "example:\n<code>/build e-commerce product page with cart API</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("frontend + backend agents running in parallel...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.scaffolder import parallel_fullstack
        result = await parallel_fullstack(task)
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="build/parallel")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"build error: <code>{e}</code>", parse_mode="HTML")


# ── /task-from, /tasks-due, /task-done — project management ──────────────────
@dp.message(Command("task_from"))
async def cmd_task_from(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/task_from").strip()
    if not text:
        await msg.answer(
            "usage: <code>/task_from &lt;text or transcript&gt;</code>\n\n"
            "extracts structured tasks from any text.\n\n"
            "example:\n"
            "<code>/task_from discussed: add auth by friday, deploy monday, john handles DB</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("extracting tasks...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.project_manager import transcript_to_tasks, save_tasks_local
        tasks = await transcript_to_tasks(text)
        await save_tasks_local(tasks, "telegram")
        typing_task.cancel()
        await status_msg.delete()
        lines = [f"<b>Extracted {len(tasks)} tasks:</b>\n"]
        priority_icons = {"high": "!!", "mid": "!", "low": ""}
        for t in tasks:
            icon = priority_icons.get(t.get("priority", "mid"), "")
            lines.append(f"  {icon} {t['task'][:80]}")
            lines.append(f"    owner: {t.get('owner', '?')} | deadline: {t.get('deadline', 'TBD')}\n")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


@dp.message(Command("tasks_due"))
async def cmd_tasks_due(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.project_manager import check_deadlines
        result = await check_deadlines()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


@dp.message(Command("task_done"))
async def cmd_task_done(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task_id_str = (msg.text or "").removeprefix("/task_done").strip()
    if not task_id_str:
        await msg.answer("usage: <code>/task_done &lt;id&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.project_manager import complete_task
        result = await complete_task(int(task_id_str))
        await msg.answer(result)
    except Exception as e:
        await msg.answer(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /gpu — enhanced GPU status ────────────────────────────────────────────────
@dp.message(Command("gpu"))
async def cmd_gpu(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.devops import check_gpu_health
        result = await check_gpu_health()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"GPU error: <code>{e}</code>", parse_mode="HTML")


# ── /vuln-scan — vulnerability scan ──────────────────────────────────────────
@dp.message(Command("vuln_scan"))
async def cmd_vuln_scan(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("scanning dependencies...")
    try:
        from tools.devops import check_vulnerabilities
        result = await check_vulnerabilities()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="devops/vuln-scan")
    except Exception as e:
        await status_msg.edit_text(f"scan error: <code>{e}</code>", parse_mode="HTML")


# ── /watch-training — training log monitor ────────────────────────────────────
@dp.message(Command("watch_training"))
async def cmd_watch_training(msg: Message) -> None:
    if not is_allowed(msg):
        return
    import os as _os
    log_path = _os.getenv("WORKERNET_LOG_PATH", "")
    if not log_path:
        await msg.answer(
            "WORKERNET_LOG_PATH not set in .env\n"
            "Set it to your training log path.",
        )
        return

    if not _scheduler:
        await msg.answer("scheduler not initialized")
        return

    task_id = await _scheduler.add_monitor(
        description="WorkerNet training watcher",
        command=f"tail -5 '{log_path}'",
        interval_sec=60,
        alert_condition="'nan' in result.lower() or 'inf' in result.lower() or 'best' in result.lower()",
    )
    await msg.answer(
        f"training watcher started: <code>{task_id}</code>\n"
        f"monitoring: {log_path}\n"
        f"alerts on: NaN, Inf, new best model\n\n"
        f"cancel: <code>/cancel {task_id}</code>",
        parse_mode="HTML",
    )


# ── /post — social media drafting ─────────────────────────────────────────────
@dp.message(Command("post"))
async def cmd_post(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/post").strip()
    if not text:
        await msg.answer(
            "usage: <code>/post &lt;platform&gt; &lt;topic&gt;</code>\n\n"
            "platforms: linkedin, tweet, thread\n\n"
            "example:\n<code>/post linkedin my WorkerNet model achieves 60% accuracy on IKEA ASM</code>",
            parse_mode="HTML",
        )
        return
    parts = text.split(maxsplit=1)
    platform = parts[0].lower()
    topic = parts[1] if len(parts) > 1 else text
    status_msg = await msg.answer(f"drafting {platform} post...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.content import draft_linkedin_post, draft_tweet
        if platform == "linkedin":
            result = await draft_linkedin_post(topic)
        elif platform == "tweet":
            result = await draft_tweet(topic, thread=False)
        elif platform == "thread":
            result = await draft_tweet(topic, thread=True)
        else:
            typing_task.cancel()
            await status_msg.edit_text("platforms: linkedin, tweet, thread")
            return
        typing_task.cancel()
        await status_msg.delete()
        await msg.answer(f"<b>{platform.upper()} draft:</b>\n\n{result}", parse_mode="HTML")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /brand-check — brand monitoring ───────────────────────────────────────────
@dp.message(Command("brand_check"))
async def cmd_brand_check(msg: Message) -> None:
    if not is_allowed(msg):
        return
    keyword = (msg.text or "").removeprefix("/brand_check").strip()
    if not keyword:
        await msg.answer("usage: <code>/brand_check &lt;keyword&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer(f"searching for: {keyword}...")
    typing_task = asyncio.create_task(_keep_typing(msg))
    try:
        from tools.content import monitor_brand
        result = await monitor_brand([keyword])
        typing_task.cancel()
        await status_msg.delete()
        await msg.answer(result, parse_mode="HTML")
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(f"error: <code>{e}</code>", parse_mode="HTML")


# ── /delegate — OpenClaw delegation ───────────────────────────────────────────
@dp.message(Command("delegate"))
async def cmd_delegate(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/delegate").strip()
    if not task:
        await msg.answer(
            "usage: <code>/delegate &lt;task&gt;</code>\n\n"
            "sends task to OpenClaw (smart home, Obsidian, Spotify, etc.)",
            parse_mode="HTML",
        )
        return
    try:
        from tools.openclaw_bridge import delegate_to_openclaw
        result = await delegate_to_openclaw(task)
        await send_chunked(msg, result, model_used="openclaw")
    except Exception as e:
        await msg.answer(f"delegate error: <code>{e}</code>", parse_mode="HTML")


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

    task_lower = task.lower()

    # Check OpenClaw delegation first
    try:
        from tools.openclaw_bridge import should_delegate_to_openclaw, is_openclaw_running, delegate_to_openclaw
        if should_delegate_to_openclaw(task):
            if await is_openclaw_running():
                result = await delegate_to_openclaw(task)
                await send_chunked(msg, result, model_used="openclaw")
                return
    except Exception:
        pass

    # ── Smart routing: question → chat, action → computer ──────────────

    # Detect questions (knowledge queries → chat mode, no tools)
    question_starters = [
        "apa ", "berapa", "bagaimana", "kenapa", "mengapa", "siapa",
        "dimana", "kapan", "gimana", "apakah", "bisakah",
        "what ", "how ", "why ", "when ", "where ", "which ",
        "who ", "is it", "are there", "does ", "do you", "can you",
        "could you", "would you", "should ",
        "ada berapa", "apa saja", "apa itu", "ada apa",
    ]
    is_question = (
        task_lower.rstrip().endswith("?")
        or any(task_lower.startswith(q) for q in question_starters)
    )

    # Strong computer keywords — always require computer access
    strong_computer = [
        "screenshot", "take screenshot",
        "click on", "click at", "klik pada",
        "drag", "scroll down", "scroll up",
        # App launching (specific apps)
        "open whatsapp", "buka whatsapp", "open chrome", "buka chrome",
        "open browser", "buka browser", "open firefox", "buka firefox",
        "open vscode", "buka vscode", "open terminal", "buka terminal",
        "open supabase", "open gmail", "open spotify", "open telegram",
        "launch ", "jalankan ",
        # Web browsing actions
        "search for", "search the web", "cari di internet",
        "browse to", "go to website", "scrape",
        # File/system actions
        "read pdf", "read excel", "extract table",
        "organize files", "baca dokumen",
        "git commit", "git push", "git pull",
        "run tests", "pytest", "format code",
        "disk space", "check services", "system cleanup",
    ]

    # Soft keywords — trigger computer only if NOT a question
    soft_computer = [
        "open", "buka", "show me", "check on",
        "cek langsung", "tolong cek", "lihat di",
        "tampilkan", "periksa", "cari online",
        "monitor", "research", "klik", "ketik",
    ]

    has_strong = any(kw in task_lower for kw in strong_computer)
    has_soft = any(kw in task_lower for kw in soft_computer)

    if has_strong:
        await _run_agent_loop(msg, task)
    elif is_question:
        await _execute_chat(msg, task)
    elif has_soft:
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


# ── Session management ────────────────────────────────────────────────────────

@dp.message(Command("save"))
async def cmd_save(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/save").strip()
    if not name:
        await msg.answer("usage: <code>/save &lt;session_name&gt;</code>", parse_mode="HTML")
        return
    try:
        import json as _json, uuid
        from agents import ACTIVE_THREADS
        from tools.persistence import save_session
        # Find the most recent active thread
        thread_id = f"tg_{msg.chat.id}"
        context = ACTIVE_THREADS.get(thread_id, [])
        session_id = uuid.uuid4().hex[:12]
        await save_session(
            session_id=session_id,
            name=name,
            thread_id=thread_id,
            agent_key="general",
            context_json=_json.dumps(context, default=str),
        )
        await msg.answer(
            f"✅ Session <b>{html_mod.escape(name)}</b> saved ({len(context)} messages)\n"
            f"ID: <code>{session_id}</code>\nResume with: <code>/resume {html_mod.escape(name)}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


@dp.message(Command("resume"))
async def cmd_resume(msg: Message) -> None:
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/resume").strip()
    if not name:
        await msg.answer("usage: <code>/resume &lt;session_name&gt;</code>", parse_mode="HTML")
        return
    try:
        import json as _json
        from agents import ACTIVE_THREADS
        from tools.persistence import resume_session
        session = await resume_session(name)
        if not session:
            await msg.answer(f"session <b>{html_mod.escape(name)}</b> not found.", parse_mode="HTML")
            return
        # Restore thread context
        thread_id = session["thread_id"]
        context = _json.loads(session["context_json"] or "[]")
        ACTIVE_THREADS[thread_id] = context
        await msg.answer(
            f"✅ Resumed <b>{html_mod.escape(session['name'])}</b> "
            f"({len(context)} messages restored)\n"
            f"Thread: <code>{thread_id}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


@dp.message(Command("sessions"))
async def cmd_sessions(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.persistence import list_sessions
        sessions = await list_sessions(limit=20)
        if not sessions:
            await msg.answer("No saved sessions.")
            return
        import datetime
        lines = ["<b>Saved Sessions</b>\n"]
        for s in sessions:
            dt = datetime.datetime.fromtimestamp(s["last_active"]).strftime("%m-%d %H:%M")
            lines.append(
                f"  <code>{s['session_id']}</code> <b>{html_mod.escape(s['name'])}</b> "
                f"({s['status']}) — {dt}"
            )
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── Audit ─────────────────────────────────────────────────────────────────────

@dp.message(Command("audit"))
async def cmd_audit(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/audit").strip()
    hours = int(arg) if arg.isdigit() else 24
    try:
        from tools.persistence import get_audit_summary
        summary = await get_audit_summary(hours=hours)
        if not summary["breakdown"]:
            await msg.answer(f"No activity in the last {hours}h.")
            return
        lines = [f"<b>Audit — last {hours}h</b>\n"]
        total_tin = total_tout = total_err = 0
        for row in summary["breakdown"]:
            tin = row["tin"] or 0
            tout = row["tout"] or 0
            total_tin += tin
            total_tout += tout
            total_err += row["errors"] or 0
            lines.append(
                f"  <code>{row['action']:12}</code> ×{row['cnt']} "
                f"({tin + tout} tok, {row['errors'] or 0} err)"
            )
        lines.append(f"\nTotal: {total_tin + total_tout} tokens, {total_err} errors")
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── Instincts / Learn ─────────────────────────────────────────────────────────

@dp.message(Command("learn"))
async def cmd_learn(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text = (msg.text or "").removeprefix("/learn").strip()
    if not text:
        await msg.answer(
            "usage: <code>/learn &lt;pattern or preference&gt;</code>\n"
            "Example: /learn Always use type hints in Python",
            parse_mode="HTML",
        )
        return
    # Detect category from keywords
    t = text.lower()
    if any(k in t for k in ("style", "format", "naming", "convention")):
        category = "style"
    elif any(k in t for k in ("prefer", "always", "never", "default")):
        category = "preference"
    elif any(k in t for k in ("fix", "correct", "actually", "instead")):
        category = "correction"
    else:
        category = "pattern"
    try:
        from tools.persistence import add_instinct
        iid = await add_instinct(category, text, source="manual")
        await msg.answer(
            f"✅ Learned [{category}] (id: {iid})\n<i>{html_mod.escape(text[:200])}</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


@dp.message(Command("instincts"))
async def cmd_instincts(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from tools.persistence import get_instincts
        items = await get_instincts(limit=30)
        if not items:
            await msg.answer("No instincts yet. Use /learn to add some.")
            return
        lines = ["<b>Instincts</b>\n"]
        for i in items:
            lines.append(
                f"  <code>#{i['id']}</code> [{i['category']}] "
                f"{html_mod.escape(i['content'][:80])} "
                f"(used {i['uses']}×)"
            )
        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


@dp.message(Command("forget"))
async def cmd_forget(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/forget").strip()
    if not arg.isdigit():
        await msg.answer("usage: <code>/forget &lt;instinct_id&gt;</code>", parse_mode="HTML")
        return
    try:
        from tools.persistence import delete_instinct
        ok = await delete_instinct(int(arg))
        if ok:
            await msg.answer(f"✅ Instinct #{arg} deleted.")
        else:
            await msg.answer(f"Instinct #{arg} not found.")
    except Exception as e:
        await msg.answer(f"error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── Code Review ───────────────────────────────────────────────────────────────

@dp.message(Command("review"))
async def cmd_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/review").strip()
    if not arg:
        await msg.answer(
            "usage: <code>/review &lt;file_path&gt;</code>\n"
            "or reply to a code message with /review",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer("🔍 reviewing…")
    try:
        from tools.code_reviewer import review_file, review_code
        from pathlib import Path
        if Path(arg).exists():
            result = await review_file(arg)
        else:
            # Treat as inline code
            result = await review_code(arg, language="python")
        await status_msg.edit_text(result[:4000], parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"review error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


@dp.message(Command("security_review"))
async def cmd_security_review(msg: Message) -> None:
    if not is_allowed(msg):
        return
    arg = (msg.text or "").removeprefix("/security_review").strip()
    if not arg:
        await msg.answer("usage: <code>/security_review &lt;file_path&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer("🛡 security review…")
    try:
        from tools.code_reviewer import review_file
        result = await review_file(arg, review_type="security")
        await status_msg.edit_text(result[:4000], parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"review error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── Multi-Plan ────────────────────────────────────────────────────────────────

@dp.message(Command("multi_plan"))
async def cmd_multi_plan(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/multi_plan").strip()
    if not task:
        await msg.answer("usage: <code>/multi_plan &lt;task&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer("🧠 generating 3 approaches…")
    try:
        from llm_client import chat
        agents = ["architect", "coding", "analyst"]
        results = await asyncio.gather(
            *(chat(task, agent_key=a) for a in agents),
            return_exceptions=True,
        )
        lines = ["<b>Multi-Plan Comparison</b>\n"]
        for agent, res in zip(agents, results):
            if isinstance(res, Exception):
                lines.append(f"\n<b>⚠️ {agent}</b>: error — {html_mod.escape(str(res)[:200])}\n")
            else:
                text, model = res
                lines.append(f"\n<b>📋 {agent}</b> ({model}):\n{text[:1000]}\n")
        full = "\n".join(lines)
        # Chunk if needed
        if len(full) <= 4000:
            await status_msg.edit_text(full, parse_mode="HTML")
        else:
            await status_msg.edit_text(full[:4000], parse_mode="HTML")
            for i in range(4000, len(full), 4000):
                await msg.answer(full[i:i + 4000], parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── Orchestrate ───────────────────────────────────────────────────────────────

@dp.message(Command("orchestrate"))
async def cmd_orchestrate(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/orchestrate").strip()
    if not task:
        await msg.answer("usage: <code>/orchestrate &lt;complex task&gt;</code>", parse_mode="HTML")
        return
    status_msg = await msg.answer("🎯 decomposing task…")
    try:
        from tools.orchestrate_engine import orchestrate_task
        result = await orchestrate_task(task, progress_cb=lambda s: status_msg.edit_text(f"⏳ {s}"))
        if len(result) <= 4000:
            await status_msg.edit_text(result, parse_mode="HTML")
        else:
            await status_msg.edit_text(result[:4000], parse_mode="HTML")
            for i in range(4000, len(result), 4000):
                await msg.answer(result[i:i + 4000], parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── Autonomous Loop ──────────────────────────────────────────────────────

@dp.message(Command("loop"))
async def cmd_loop(msg: Message) -> None:
    """Autonomous plan-execute loop with safety bounds."""
    if not is_allowed(msg):
        return
    goal = (msg.text or "").removeprefix("/loop").strip()
    if not goal:
        await msg.answer(
            "<b>usage:</b> <code>/loop &lt;goal&gt;</code>\n\n"
            "Runs an autonomous plan→execute loop until the goal is done.\n"
            "Safety bounds: 25 iterations, $0.50 cost ceiling, 30min timeout.\n"
            "Stop anytime with /loop_stop",
            parse_mode="HTML",
        )
        return

    from tools.autonomous_loop import get_active_loop, run_autonomous_loop, LoopConfig

    # Check if a loop is already running
    if get_active_loop(msg.from_user.id):
        await msg.answer(
            "A loop is already running. Use /loop_stop to cancel it first.",
        )
        return

    thread_id = _user_thread.get(msg.from_user.id)

    await msg.answer(
        f"<b>🔄 Loop started</b>\n"
        f"Goal: <code>{html_mod.escape(goal[:200])}</code>\n\n"
        f"Bounds: 25 iters | $0.50 cost cap | 30min timeout\n"
        f"Progress updates every 5 iterations.\n"
        f"Stop anytime: /loop_stop",
        parse_mode="HTML",
    )

    async def notify(text: str) -> None:
        try:
            await bot.send_message(msg.chat.id, text, parse_mode="HTML")
        except Exception:
            try:
                await bot.send_message(msg.chat.id, html_mod.escape(text), parse_mode="HTML")
            except Exception:
                await bot.send_message(msg.chat.id, text[:4000])

    # Run in background — don't block the command handler
    asyncio.create_task(
        run_autonomous_loop(
            user_id=msg.from_user.id,
            goal=goal,
            notify_cb=notify,
            config=LoopConfig(),
            thread_id=thread_id,
        )
    )


@dp.message(Command("loop_stop"))
async def cmd_loop_stop(msg: Message) -> None:
    """Kill switch for the autonomous loop."""
    if not is_allowed(msg):
        return
    from tools.autonomous_loop import stop_loop
    if stop_loop(msg.from_user.id):
        await msg.answer("Loop stop signal sent. It will halt after the current step.")
    else:
        await msg.answer("No active loop running.")


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

    # Register lifecycle hooks
    try:
        from core.builtin_hooks import register_builtin_hooks
        register_builtin_hooks()
        logger.info("Lifecycle hooks registered")
    except Exception as e:
        logger.warning("Hook init failed (non-fatal): %s", e)

    # Initialize memory DB
    try:
        from tools.memory import init_memory_db
        await init_memory_db()
        logger.info("Memory DB initialized")
    except Exception as e:
        logger.warning("Memory init failed (non-fatal): %s", e)

    # Schedule daily briefing at 7:30 AM
    try:
        from tools.briefing import schedule_daily_briefing
        asyncio.create_task(schedule_daily_briefing(bot, ALLOWED_USER_ID, hour=7, minute=30))
        logger.info("Daily briefing scheduled for 07:30")
    except Exception as e:
        logger.warning("Briefing schedule failed (non-fatal): %s", e)

    await bot.set_my_commands([
        BotCommand(command="do",          description="Autonomous computer control"),
        BotCommand(command="screen",      description="Take desktop screenshot"),
        BotCommand(command="run",         description="LLM chat (no computer)"),
        BotCommand(command="swarm",       description="Multi-agent team execution"),
        BotCommand(command="think",       description="QwQ deep reasoning"),
        BotCommand(command="cmd",         description="Run shell command"),
        # Research
        BotCommand(command="paper",       description="Search arXiv papers"),
        BotCommand(command="ask_paper",   description="Ask about a paper"),
        BotCommand(command="workernet_papers", description="Analyze WorkerNet papers"),
        BotCommand(command="research",    description="Deep web research"),
        BotCommand(command="scrape",      description="Scrape a URL"),
        # Memory
        BotCommand(command="remember",    description="Save a note to memory"),
        BotCommand(command="recall",      description="Search memory"),
        BotCommand(command="memories",    description="Show recent memories"),
        BotCommand(command="briefing",    description="Morning briefing"),
        # Dev
        BotCommand(command="scaffold",    description="Create project scaffold"),
        BotCommand(command="build",       description="Parallel fullstack build"),
        BotCommand(command="gpu",         description="GPU health status"),
        BotCommand(command="vuln_scan",   description="Vulnerability scan"),
        # Tasks
        BotCommand(command="task_from",   description="Extract tasks from text"),
        BotCommand(command="tasks_due",   description="Show pending tasks"),
        # Content
        BotCommand(command="post",        description="Draft social media post"),
        BotCommand(command="brand_check", description="Monitor brand mentions"),
        # Code Quality
        BotCommand(command="review",      description="AI code review"),
        BotCommand(command="security_review", description="Security audit"),
        # Orchestration
        BotCommand(command="orchestrate", description="Decompose + execute complex task"),
        BotCommand(command="multi_plan",  description="Compare 3 agent approaches"),
        BotCommand(command="loop",        description="Autonomous goal execution loop"),
        BotCommand(command="loop_stop",   description="Stop running loop"),
        # Sessions & Learning
        BotCommand(command="save",        description="Save session state"),
        BotCommand(command="resume",      description="Resume saved session"),
        BotCommand(command="sessions",    description="List saved sessions"),
        BotCommand(command="learn",       description="Teach a pattern"),
        BotCommand(command="instincts",   description="Show learned patterns"),
        BotCommand(command="audit",       description="Activity audit trail"),
        # System
        BotCommand(command="models",      description="Agent roster"),
        BotCommand(command="keys",        description="API key status"),
        BotCommand(command="stats",       description="System stats"),
        BotCommand(command="start",       description="Help + status"),
    ])

    key_status = verify_api_keys()
    active = [k for k, v in key_status.items() if v]
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]

    # Detect display at startup
    display = await computer_agent.detect_display()

    logger.info("=" * 55)
    logger.info("Legion v4 starting")
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
