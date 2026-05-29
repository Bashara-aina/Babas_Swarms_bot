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
  /resources       → RAM / GPU VRAM / local model policy
  /stats           → CPU/GPU/RAM
  /git             → git status
  /threads         → conversation threads
  /scrape <url>    → scrape a webpage
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable
from contextvars import copy_context
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from uuid import uuid4

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.types import BotCommand, Message
from dotenv import load_dotenv

import agents as agents_registry
import computer_agent
import handlers
import handlers.shared as _shared
from core.daily_harvester.scheduler import DailyHarvesterScheduler
from core.health_check import FEATURE_FLAGS, print_health_report, run_health_check
from core.log_config import set_request_id
from core.observability import init_observability
from core.wiki_scheduler import WikiQualityScheduler
from handlers import register_all_routers
from llm_client import init_humanization_layer, verify_api_keys

# ── Load env FIRST before any module reads os.getenv() ───────────────────────
load_dotenv(Path(__file__).parent / ".env", override=True)

import core.memory.litellm_callbacks  # noqa: F401 — registers litellm.input/success_callback

_REQUIRED_KEYS = ["TELEGRAM_BOT_TOKEN", "ALLOWED_USER_ID"]
_missing = [k for k in _REQUIRED_KEYS if not os.getenv(k)]
if _missing:
    raise RuntimeError(f"Missing required env vars: {_missing}")

# ── Global scheduler handles ─────────────────────────────────────────────────
_harvester_scheduler: DailyHarvesterScheduler | None = None
_wiki_scheduler: WikiQualityScheduler | None = None

# ── Sidecar process handles (restart policy on crash) ───────────────────────
_ruflo_process: subprocess.Popen[bytes] | None = None
_opencode_process: subprocess.Popen[bytes] | None = None

# ── Logging ────────────────────────────────────────────────────────────
_log_dir = Path(__file__).parent / "logs"
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_log_dir / "bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _trim_log_text(value: Any, limit: int = 1200) -> str:
    """Truncate value to limit chars for log safety. Returns string."""
    text = "" if value is None else str(value)
    text = text.replace("\n", "\\n").replace("\r", "")
    return text[:limit] + ("…" if len(text) > limit else "")


class ActivityLogMiddleware(BaseMiddleware):
    """Logs all inbound Telegram messages for observability.

    Generates a short UUID request_id (8 hex chars) and propagates it via contextvars
    so all downstream async calls include it in log entries.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        request_id = uuid4().hex[:8]
        copy_context()
        set_request_id(request_id)
        try:
            user_id = event.from_user.id if event.from_user else None
            username = event.from_user.username if event.from_user else None
            chat_id = event.chat.id if event.chat else None
            text = event.text or event.caption or ""
            logger.info(
                "[IN][request_id=%s][chat=%s][user=%s|@%s] %s",
                request_id,
                chat_id,
                user_id,
                username,
                _trim_log_text(text),
            )
        except Exception as e:
            logger.warning("Inbound activity logging failed: %s", e)
        # Track last user message for curiosity engine
        try:
            if event.from_user and event.from_user.id == ALLOWED_USER_ID:
                _shared._last_user_message_ts = time.time()
        except Exception:
            pass
        try:
            return await handler(event, data)
        finally:
            set_request_id("")  # clear after request


def _install_outbound_logging(bot: Bot) -> None:
    """Wrap core Bot send/edit methods to log all outbound content."""
    original_send_message = bot.send_message
    original_edit_message_text = bot.edit_message_text
    original_send_photo = bot.send_photo

    async def send_message_logged(chat_id: int, text: str, *args: Any, **kwargs: Any):
        logger.info("[OUT][chat=%s][send_message] %s", chat_id, _trim_log_text(text))
        return await original_send_message(chat_id, text, *args, **kwargs)

    async def edit_message_text_logged(
        text: str,
        chat_id: int | None = None,
        message_id: int | None = None,
        inline_message_id: str | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        logger.info(
            "[OUT][chat=%s][edit_message_text] %s",
            chat_id,
            _trim_log_text(text),
        )
        return await original_edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            **kwargs,
        )

    async def send_photo_logged(chat_id: int, photo: Any, *args: Any, **kwargs: Any):
        caption = kwargs.get("caption", "")
        logger.info(
            "[OUT][chat=%s][send_photo] caption=%s",
            chat_id,
            _trim_log_text(caption),
        )
        return await original_send_photo(chat_id, photo, *args, **kwargs)




# ── Graceful Shutdown ─────────────────────────────────────────────────────────
_shutdown_flag = False


def _handle_signal(sig: int, frame) -> None:
    """Handle SIGTERM/SIGINT — set flag for graceful shutdown."""
    global _shutdown_flag
    if _shutdown_flag:
        return
    _shutdown_flag = True
    logger.warning("Received signal %d — graceful shutdown initiated", sig)


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# ── LEGION BOOT Subsystem Health Checks ───────────────────────────────────────


async def _probe_telegram(bot: Bot) -> tuple[bool, str]:
    """Check Telegram API connection by fetching Me."""
    try:
        me = await bot.get_me()
        return True, f"@{me.username}"
    except Exception as e:
        return False, str(e)[:80]


async def _probe_llm() -> tuple[bool, str]:
    """Ping primary LLM with a lightweight call to verify connectivity."""
    try:
        import litellm

        primary = os.getenv("LEGION_LLM_MODEL", "minimax-coding-plan/MiniMax-M2.7")
        if primary.lower().startswith("minimax/"):
            from openai import AsyncOpenAI
            api_key = os.getenv("MINIMAX_API_KEY", "")
            base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
            model_name = primary.replace("minimax/", "").replace("minimax-", "MiniMax-")
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
        else:
            await litellm.acompletion(
                model=primary,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=2,
            )
        return True, primary
    except Exception as e:
        return False, str(e)[:80]


async def _probe_chromadb() -> tuple[bool, str]:
    """Check ChromaDB availability. Warns but doesn't fail."""
    try:
        import chromadb

        client = chromadb.Client()
        client.heartbeat()
        return True, "connected"
    except Exception as e:
        return False, f"unavailable ({e})"


async def _probe_wiki() -> tuple[bool, str]:
    """Check .wiki/ directory is readable and count documents."""
    try:
        wiki_path = Path(".wiki")
        if not wiki_path.exists():
            return False, "not found"
        docs = [d for d in wiki_path.rglob("*.md") if "_quarantine" not in str(d) and "_archive" not in str(d)]
        return True, f"{len(docs)} documents loaded"
    except Exception as e:
        return False, f"error: {e}"


async def _probe_data_writable() -> tuple[bool, str]:
    """Check data/ directory is writable."""
    try:
        data_path = Path("data")
        data_path.mkdir(exist_ok=True)
        test_file = data_path / ".health_check_write_test"
        test_file.write_text("ok")
        test_file.unlink()
        return True, "writable"
    except Exception as e:
        return False, f"not writable ({e})"


async def _probe_voicevox() -> tuple[bool, str]:
    """Check VoiceVox engine availability. Warns but doesn't fail."""
    try:
        from bridges.voicevox_bridge import VoiceVoxBridge

        bridge = VoiceVoxBridge()
        available = await bridge._check_voicevox()
        if available:
            return True, "running"
        return False, "not running (voice mode disabled)"
    except Exception:
        return False, "not installed (voice mode disabled)"


async def _probe_duckduckgo() -> tuple[bool, str]:
    """Test DuckDuckGo search returns actual content."""
    try:
        from ddgs import DDGS

        result = await asyncio.wait_for(
            asyncio.to_thread(lambda: list(DDGS().text("test", max_results=1))),
            timeout=10.0,
        )
        return (True, "OK") if result else (False, "empty response")
    except ImportError:
        return False, "duckduckgo-search not installed"
    except Exception as e:
        return False, f"error: {e}"


async def run_legion_boot_health(bot: Bot) -> dict[str, dict[str, str]]:
    """Run full startup health check across all subsystems."""
    results: dict[str, dict[str, str]] = {}

    telegram_ok, telegram_detail = await _probe_telegram(bot)
    llm_ok, llm_detail = await _probe_llm()
    chroma_ok, chroma_detail = await _probe_chromadb()
    wiki_ok, wiki_detail = await _probe_wiki()
    data_ok, data_detail = await _probe_data_writable()
    voicevox_ok, voicevox_detail = await _probe_voicevox()
    ddg_ok, ddg_detail = await _probe_duckduckgo()

    results["telegram"] = {"ok": telegram_ok, "detail": telegram_detail}
    results["llm"] = {"ok": llm_ok, "detail": llm_detail}
    results["chromadb"] = {"ok": chroma_ok, "detail": chroma_detail}
    results["wiki"] = {"ok": wiki_ok, "detail": wiki_detail}
    results["data"] = {"ok": data_ok, "detail": data_detail}
    results["voicevox"] = {"ok": voicevox_ok, "detail": voicevox_detail}
    results["duckduckgo"] = {"ok": ddg_ok, "detail": ddg_detail}

    return results


def print_legion_boot_report(results: dict[str, dict[str, str]]) -> None:
    """Print the LEGION BOOT startup report in the specified format."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n🚀 LEGION BOOT — {ts}")

    checks = [
        ("telegram", "Telegram", None),
        ("llm", "LLM", None),
        ("chromadb", "ChromaDB", "unavailable (memory degraded)"),
        ("wiki", "Wiki", None),
        ("data", "Data", None),
        ("voicevox", "VoiceVox", "not running (voice mode disabled)"),
        ("duckduckgo", "Search", None),
    ]

    degraded: list[str] = []
    for key, label, degrade_msg in checks:
        entry = results.get(key, {"ok": False, "detail": "unknown"})
        ok = entry["ok"]
        detail = entry["detail"]

        icon = "✅" if ok else "⚠️"

        if key == "chromadb" and not ok:
            print(f"{icon} {label}: {degrade_msg}")
            degraded.append("memory")
        elif key == "voicevox" and not ok:
            print(f"{icon} {label}: {degrade_msg}")
            degraded.append("voice")
        elif (key == "llm" and ok) or (key == "wiki" and ok):
            print(f"{icon} {label}: {detail}")
        else:
            print(f"{icon} {label}: {detail}")

    degraded_str = ", ".join(degraded) if degraded else "none"
    print(f"Legion ready. Degraded mode: {degraded_str}.")


# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
_uid_raw = (os.getenv("ALLOWED_USER_ID") or os.getenv("BASHARA_TELEGRAM_ID") or "0").strip()
ALLOWED_USER_ID = int(_uid_raw.split(",")[0] if _uid_raw else "0")

if not BOT_TOKEN:
    logger.critical("TELEGRAM_BOT_TOKEN not set in .env")
    sys.exit(1)
if not ALLOWED_USER_ID:
    logger.critical("ALLOWED_USER_ID or BASHARA_TELEGRAM_ID must be set in .env")
    sys.exit(1)

# ── Inject shared config into handlers package ─────────────────────────────────
_shared.ALLOWED_USER_ID = ALLOWED_USER_ID
_shared._start_time = time.time()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(ActivityLogMiddleware())
logger.info("Activity inbound logging middleware installed")

# Register all handler routers
register_all_routers(dp)


# ── Startup ───────────────────────────────────────────────────────────────────
def _ruflo_health_probe_sync(url: str = "http://127.0.0.1:7834/health") -> bool:
    req = urlrequest.Request(url=url, method="GET")
    with urlrequest.urlopen(req, timeout=2) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status == 200 and '"ok":true' in body.replace(" ", "")


def _opencode_health_probe_sync(url: str = "http://127.0.0.1:4096/health") -> bool:
    req = urlrequest.Request(url=url, method="GET")
    with urlrequest.urlopen(req, timeout=2) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status == 200 and '"ok":true' in body.replace(" ", "")


async def _wait_for_ruflo_health(attempts: int = 8, delay_seconds: float = 0.5) -> bool:
    for _ in range(attempts):
        try:
            healthy = await asyncio.to_thread(_ruflo_health_probe_sync)
            if healthy:
                return True
        except (urlerror.URLError, TimeoutError, ValueError, OSError):
            pass
        await asyncio.sleep(delay_seconds)
    return False


async def _ruflo_restart_monitor(check_interval: float = 30.0) -> None:
    """Background loop: restarts ruflo sidecar if it crashes.

    Uses the global _ruflo_process handle to detect death,
    then re-spawns it and verifies health.
    """
    global _ruflo_process
    import itertools
    for attempt in itertools.count():
        await asyncio.sleep(check_interval)
        proc = _ruflo_process
        if proc is None:
            continue
        if proc.poll() is not None:  # process has exited
            logger.warning("ruflo sidecar died (pid=%d, exit=%d) — restarting in %ds",
                           proc.pid, proc.returncode, check_interval)
            try:
                new_proc = subprocess.Popen(
                    ["node", "tools/ruflo/server.js"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                _ruflo_process = new_proc
                logger.info("ruflo sidecar restarted (new pid=%d)", new_proc.pid)
                if await _wait_for_ruflo_health():
                    logger.info("ruflo sidecar healthy after restart")
                else:
                    logger.warning("ruflo sidecar unhealthy after restart (non-fatal)")
            except Exception as e:
                logger.error("ruflo sidecar restart failed: %s", e)


async def _wait_for_opencode_health(attempts: int = 8, delay_seconds: float = 0.5) -> bool:
    for _ in range(attempts):
        try:
            healthy = await asyncio.to_thread(_opencode_health_probe_sync)
            if healthy:
                return True
        except (urlerror.URLError, TimeoutError, ValueError, OSError):
            pass
        await asyncio.sleep(delay_seconds)
    return False


async def _bootstrap_supabase_skill() -> None:
    """Generate skills/rumahlabuh-manager.md from live Supabase schema.

    Runs on startup if the skill file is missing or older than 7 days.
    Wrapped in try/except — never blocks bot boot.
    """
    skill_path = Path("skills/rumahlabuh-manager.md")
    max_age_seconds = 7 * 24 * 3600  # regenerate weekly

    if skill_path.exists():
        age = time.time() - skill_path.stat().st_mtime
        if age < max_age_seconds:
            logger.info("Supabase skill file is fresh (age=%.0fh) — skipping bootstrap", age / 3600)
            return
        logger.info("Supabase skill file is stale (age=%.0fh) — regenerating", age / 3600)
    else:
        logger.info("Supabase skill file missing — bootstrapping from live schema")

    try:
        from tools.supabase_client import get_client, is_configured

        if not is_configured():
            logger.info("Supabase not configured — skipping skill bootstrap")
            return
        db = get_client()
        path = await db.generate_skill_file(str(skill_path))
        logger.info("✅ Supabase skill file generated: %s", path)
    except Exception as exc:
        logger.warning("Supabase skill bootstrap failed (non-fatal): %s", exc)


async def _run_group_a_startup(bot: Bot) -> None:
    """Run all independent startup tasks in parallel via asyncio.gather."""

    async def _start_observability() -> None:
        try:
            init_observability()
        except Exception as e:
            logger.warning("Observability init failed (non-fatal): %s", e)

    async def _start_humanization() -> None:
        try:
            layer = init_humanization_layer()
            mem = layer.get("memory")
            emo = layer.get("emotion")
            logger.info("[Legion v6] Memory: %s", await mem.get_memory_stats() if mem else {})
            logger.info(
                "[Legion v6] Emotion: %s",
                getattr(getattr(emo, "state", None), "dominant_emotion", "loaded"),
            )
            logger.info("[Legion v6] Humanization layer active.")
        except Exception as e:
            logger.warning("Humanization init failed (non-fatal): %s", e)

    async def _start_registry() -> None:
        try:
            from core.agent_registry import load_registry

            load_registry()
            logger.info("Agent registry loaded from YAML (76 agents)")
        except Exception as e:
            logger.warning("Agent registry YAML load failed (non-fatal): %s", e)

    async def _start_personality() -> None:
        try:
            from tools.letta_personality import init_personality_state

            state = init_personality_state()
            logger.info("Personality state loaded: %s", state.get("dominant_emotion", "neutral"))
        except Exception as e:
            logger.warning("Personality init failed (non-fatal): %s", e)

    async def _start_memoryos() -> None:
        try:
            from tools.memoryos_client import get_memoryos

            mos = get_memoryos("bashara")
            if mos:
                logger.info("✅ MemoryOS initialized (hierarchical memory tiers)")
        except Exception as e:
            logger.warning("MemoryOS init failed (non-fatal): %s", e)

    async def _start_n8n() -> None:
        try:
            from tools.n8n_bridge import start_n8n_webhook_listener

            start_n8n_webhook_listener()
            logger.info("n8n webhook listener scheduled")
        except Exception as e:
            logger.warning("n8n init failed (non-fatal): %s", e)

    async def _start_monitors() -> None:
        try:
            from tools.proactive_monitors import start_monitors

            for task in await start_monitors(bot, ALLOWED_USER_ID):
                _ = task
            interval = int(os.getenv("PROACTIVE_MIN_INTERVAL_SEC", "1800"))
            logger.info("Proactive monitors scheduled (min_interval=%ds, env: PROACTIVE_MIN_INTERVAL_SEC)", interval)
        except Exception as e:
            logger.warning("Proactive monitors init failed (non-fatal): %s", e)

    async def _start_proactive_scheduler() -> None:
        try:
            from core.proactive.scheduler import get_scheduler

            async def _proactive_notify(text: str) -> None:
                await bot.send_message(ALLOWED_USER_ID, text[:4000], parse_mode="HTML")

            get_scheduler(str(ALLOWED_USER_ID), _proactive_notify, ALLOWED_USER_ID).start()
            logger.info("ProactiveScheduler started (schedule + business + GitHub checks)")
        except Exception as e:
            logger.warning("ProactiveScheduler init failed (non-fatal): %s", e)

    async def _start_curiosity_engine() -> None:
        try:
            from core.proactive.curiosity_engine import run_curiosity_loop

            async def _curiosity_notify(text: str) -> None:
                await bot.send_message(ALLOWED_USER_ID, text[:4000])

            def _get_last_user_ts() -> float:
                try:
                    import handlers.shared as _sh

                    return _sh._last_user_message_ts
                except Exception:
                    return 0.0

            task = asyncio.create_task(run_curiosity_loop(_curiosity_notify, _get_last_user_ts))
            task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
            logger.info("Curiosity engine started")
        except Exception as e:
            logger.warning("Curiosity engine init failed (non-fatal): %s", e)

    async def _start_voice_prewarm() -> None:
        try:
            from tools.voice_engine import prewarm

            await prewarm()
            logger.info("Voice engine pre-warmed")
        except Exception as e:
            logger.warning("Voice prewarm failed (non-fatal): %s", e)

    async def _start_gemma4_prep() -> None:
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("agents_root", Path(__file__).parent / "agents.py")
            if spec and spec.loader:
                agents_root = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agents_root)
                agents_root.ensure_gemma4_local_available()
        except Exception as e:
            logger.warning("gemma4 local prep failed (non-fatal): %s", e)

    async def _start_daily_harvester() -> None:
        global _harvester_scheduler
        try:

            async def _harvest_notify(text: str) -> None:
                await bot.send_message(ALLOWED_USER_ID, text[:4000])

            _harvester_scheduler = DailyHarvesterScheduler(_harvest_notify, ALLOWED_USER_ID)
            _harvester_scheduler.start()
            logger.info("DailyHarvesterScheduler started")
        except Exception as e:
            logger.warning("DailyHarvesterScheduler init failed (non-fatal): %s", e)

    async def _start_wiki_quality_scheduler() -> None:
        global _wiki_scheduler
        try:

            async def _wiki_notify(text: str) -> None:
                await bot.send_message(ALLOWED_USER_ID, text[:4000])

            _wiki_scheduler = WikiQualityScheduler(_wiki_notify, ALLOWED_USER_ID)
            _wiki_scheduler.start()
            logger.info("WikiQualityScheduler started")
        except Exception as e:
            logger.warning("WikiQualityScheduler init failed (non-fatal): %s", e)

    async def _register_lifecycle_hooks() -> None:
        try:
            from core.builtin_hooks import register_builtin_hooks

            register_builtin_hooks()
            logger.info("Lifecycle hooks registered")
            # Emit session_start so symphony, cc_session_start, and other hooks fire
            try:
                from core.hooks import get_hooks
                hooks = get_hooks()
                await hooks.emit("session_start", {"source": "legion_startup"})
            except Exception:
                pass
        except Exception as e:
            logger.warning("Hook init failed (non-fatal): %s", e)

        # Start observation queue (fire-and-forget non-blocking capture)
        try:
            from core.memory.observation_capture import register_observation_hooks
            from core.memory.observation_queue import get_observation_queue

            register_observation_hooks()
            get_observation_queue().start()
            logger.info("Observation capture system started")
        except Exception as e:
            logger.warning("Observation queue init failed (non-fatal): %s", e)

    # Run all Group A tasks in parallel with a 30s timeout
    await asyncio.wait_for(
        asyncio.gather(
            _start_observability(),
            _start_humanization(),
            _start_registry(),
            _start_personality(),
            _start_memoryos(),
            _start_n8n(),
            _start_monitors(),
            _start_proactive_scheduler(),
            _start_curiosity_engine(),
            _start_voice_prewarm(),
            _start_gemma4_prep(),
            _start_daily_harvester(),
            _start_wiki_quality_scheduler(),
            _register_lifecycle_hooks(),
            return_exceptions=True,
        ),
        timeout=30.0,
    )


async def on_startup(bot: Bot) -> None:
    """Initializes bot, registers routers, starts background daemons.

    Called by aiogram when the bot starts. Sets up:
    - Skills registry
    - Schedulers (daily briefing, nightly capability, memory consolidation, GitHub intel)
    - Heartbeat daemon
    - Persistence and memory DBs
    - Session transcript store
    - swarms_bot enterprise layer (via core/swarm.py)
    - Webhook server (core/webhooks/)
    - MCP manager (core/mcp/)
    - Sidecar processes (ruflo, opencode)
    All initializations are wrapped in try/except — failures are non-fatal.
    """
    # Store bot reference in shared state for cross-module access
    _shared._bot = bot

    # Import and initialize skills registry
    try:
        from core.skills import get_skill_registry

        _ = get_skill_registry()  # triggers module-level registration
        skill_count = len(get_skill_registry().list_all())
        logger.info("Skills registry initialized (%d skills)", skill_count)

        # Initialize timer skill with bot reference for notifications
        try:
            from core.skills.timer import set_bot as timer_set_bot

            timer_set_bot(bot)
            logger.info("Timer skill bot reference set")
        except Exception as e:
            logger.warning("Timer bot init failed (non-fatal): %s", e)
    except Exception as e:
        logger.warning("Skills registry init failed (non-fatal): %s", e)

    # Group A: Run all independent tasks in parallel
    await _run_group_a_startup(bot)

    # Heartbeat daemon (proactive health monitoring during active hours)
    try:
        from core.heartbeat.daemon import _heartbeat

        asyncio.create_task(_heartbeat.start(bot, ALLOWED_USER_ID)).add_done_callback(
            lambda t: logger.error("Heartbeat daemon crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Heartbeat daemon started (interval=%ds)", _heartbeat.interval // 60)
    except Exception as e:
        logger.warning("Heartbeat daemon init failed (non-fatal): %s", e)

    # Group B: Run sequentially after parallel tasks complete
    # Initialize persistence and scheduler
    try:
        from tools.persistence import init_db
        from tools.scheduler import TaskScheduler

        await init_db()
        _shared._scheduler = TaskScheduler(bot, ALLOWED_USER_ID)
        await _shared._scheduler.start()
        logger.info("Scheduler initialized")
    except Exception as e:
        logger.warning("Scheduler init failed (non-fatal): %s", e)

    # Initialize Legiona autonomous maintenance scheduler (weekly evolve, friday eval, monthly dedup)
    try:
        from lib.legiona.scheduler import start_scheduler as start_legiona_scheduler
        _shared._legiona_scheduler = start_legiona_scheduler(bot)
        logger.info("Legiona scheduler initialized")
    except Exception as e:
        logger.warning("Legiona scheduler init failed (non-fatal): %s", e)

    # Initialize memory DB
    try:
        from tools.memory import init_memory_db

        await init_memory_db()
        logger.info("Memory DB initialized")
    except Exception as e:
        logger.warning("Memory init failed (non-fatal): %s", e)

    # Initialize persistent conversation history DB + cleanup old turns
    try:
        from core.conversation_interface import _cleanup_old_turns, _init_conv_db

        await _init_conv_db()
        asyncio.create_task(_cleanup_old_turns()).add_done_callback(
            lambda t: logger.error("Cleanup old turns crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Conversation history DB initialized (SQLite-backed)")
    except Exception as e:
        logger.warning("Conversation history DB init failed (non-fatal): %s", e)

    # Initialize session transcript store (U1 — SQLite-backed, separate from conversation history)
    try:
        from core.session.transcript import get_transcript_store

        store = get_transcript_store()
        await store.init()
        logger.info("Session transcript store initialized")
    except Exception as e:
        logger.warning("Session transcript store init failed (non-fatal): %s", e)

    # Group C: Fire-and-forget tasks (already using create_task — no changes needed)
    # Bootstrap Supabase skill file from live schema (non-blocking)
    asyncio.create_task(_bootstrap_supabase_skill()).add_done_callback(
        lambda t: logger.error("Bootstrap supabase skill crashed: %s", t.exception()) if t.exception() else None
    )

    # Schedule daily briefing at 7:30 AM via tools/briefing.py
    # NOTE: ProactiveScheduler in core/proactive/scheduler.py ALSO fires a briefing at DAILY_BRIEFING_HOUR (default 8AM).
    # This creates duplicate briefings. For now, let ProactiveScheduler handle it (8AM) and disable this one.
    # Planned: consolidate into a single briefing mechanism (see ADR-006)
    FEATURE_BRIEFING_CONSOLIDATION_ENABLED = False  # Planned: v2.0
    if not FEATURE_BRIEFING_CONSOLIDATION_ENABLED:
        logger.info("Briefing consolidation is planned for v2.0 — not yet available.")
    # try:
    #     from tools.briefing import schedule_daily_briefing
    #
    #     asyncio.create_task(schedule_daily_briefing(bot, ALLOWED_USER_ID, hour=7, minute=30))
    #     logger.info("Daily briefing scheduled for 07:30")
    # except Exception as e:
    #     logger.warning("Briefing schedule failed (non-fatal): %s", e)

    # Schedule nightly capability regression at 03:40 AM
    try:
        from tools.capability_nightly import schedule_nightly_capability_report

        asyncio.create_task(
            schedule_nightly_capability_report(bot, ALLOWED_USER_ID, hour=3, minute=40)
        ).add_done_callback(
            lambda t: logger.error("Nightly capability report crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Nightly capability regression scheduled for 03:40")
    except Exception as e:
        logger.warning("Nightly capability schedule failed (non-fatal): %s", e)

    # Schedule nightly memory consolidation at 02:00 AM
    try:

        async def _run_memory_consolidation_nightly() -> None:
            import calendar

            while True:
                now = datetime.now()
                target = now.replace(hour=2, minute=0, second=0, microsecond=0)
                if now >= target:
                    target = target + timedelta(days=1)
                sleep_seconds = (target - now).total_seconds()
                if sleep_seconds <= 0:
                    sleep_seconds = 86400  # Fallback: 24h
                await asyncio.sleep(sleep_seconds)
                try:
                    from core.memory.consolidator import run_nightly

                    result = await run_nightly()
                    logger.info("Memory consolidation done: %s", result)
                except Exception as _ce:
                    logger.warning("Memory consolidation failed: %s", _ce)
                await asyncio.sleep(60)

        asyncio.create_task(_run_memory_consolidation_nightly()).add_done_callback(
            lambda t: logger.error("Memory consolidation nightly crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Nightly memory consolidation scheduled for 02:00")
    except Exception as e:
        logger.warning("Memory consolidation schedule failed (non-fatal): %s", e)

    # Schedule weekly memory consistency validation at 03:00 AM (Monday)
    try:

        async def _run_memory_consistency_weekly() -> None:
            while True:
                now = datetime.now().astimezone()
                target = now.replace(hour=3, minute=0, second=0, microsecond=0)
                days_ahead = (0 - target.weekday()) % 7  # Monday
                target = target + timedelta(days=days_ahead)
                if target <= now:
                    target = target + timedelta(days=7)

                await asyncio.sleep((target - now).total_seconds())
                try:
                    from core.memory.memory_manager import get_memory

                    report = await get_memory().validate_consistency(user_id=str(ALLOWED_USER_ID))
                    logger.info("Weekly memory consistency check: %s", report)

                    if report.get("status") == "drift_detected":
                        await bot.send_message(
                            ALLOWED_USER_ID,
                            "<b>⚠️ Memory Consistency Alert</b>\n"
                            f"Average drift: <code>{float(report.get('average_drift', 0.0)):.4f}</code>\n"
                            f"Max drift: <code>{float(report.get('max_drift', 0.0)):.4f}</code>\n"
                            f"Threshold: <code>{float(report.get('threshold', 0.15)):.4f}</code>\n"
                            f"Samples: <code>{int(report.get('sample_size', 0))}</code>",
                            parse_mode="HTML",
                        )
                except Exception as check_exc:
                    logger.warning("Memory consistency validation failed: %s", check_exc)

                await asyncio.sleep(60)

        asyncio.create_task(_run_memory_consistency_weekly()).add_done_callback(
            lambda t: logger.error("Memory consistency weekly crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Weekly memory consistency validation scheduled for Monday 03:00")
    except Exception as e:
        logger.warning("Memory consistency schedule failed (non-fatal): %s", e)

    # Schedule daily GitHub trending intelligence at 09:00 AM
    try:

        async def _run_github_intel_daily() -> None:
            import calendar

            while True:
                now = datetime.now()
                target = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if now >= target:
                    target = target.replace(day=target.day + 1)
                try:
                    days_in_month = calendar.monthrange(target.year, target.month)[1]
                    if target.day > days_in_month:
                        target = target.replace(
                            month=target.month + 1 if target.month < 12 else 1,
                            day=1,
                            year=target.year + (1 if target.month == 12 else 0),
                        )
                except Exception:
                    pass
                await asyncio.sleep((target - now).total_seconds())
                try:
                    from tools.github_intel import GitHubIntelEngine

                    engine = GitHubIntelEngine()

                    async def _notify(text: str) -> None:
                        await bot.send_message(ALLOWED_USER_ID, text[:4000], parse_mode="HTML")

                    repos = await engine.fetch_trending(language="python")
                    await engine.evaluate_all(repos)
                    await engine.run_daily_scan(_notify)
                except Exception as _ge:
                    logger.warning("GitHub intel daily scan failed: %s", _ge)
                await asyncio.sleep(60)

        asyncio.create_task(_run_github_intel_daily()).add_done_callback(
            lambda t: logger.error("GitHub intel daily crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Daily GitHub intel scheduled for 09:00")
    except Exception as e:
        logger.warning("GitHub intel schedule failed (non-fatal): %s", e)

    # Proactive initiator (fire-and-forget)
    try:
        from tools.proactive_initiator import start_proactive_initiator

        asyncio.create_task(start_proactive_initiator(bot, ALLOWED_USER_ID)).add_done_callback(
            lambda t: logger.error("Proactive initiator crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Proactive initiator started (Legion talks first)")
    except Exception as e:
        logger.warning("Proactive initiator init failed (non-fatal): %s", e)

    # Proactive engine (monitoring loop)
    try:
        from core.proactive_engine import register_sender, run_proactive_loop

        async def _legion_proactive_send(text: str) -> None:
            await bot.send_message(chat_id=int(os.getenv("ALLOWED_USER_ID")), text=text, parse_mode="HTML")

        register_sender(_legion_proactive_send)
        asyncio.create_task(run_proactive_loop()).add_done_callback(
            lambda t: logger.error("Proactive engine loop crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Proactive engine started (site/GPU/thesis monitoring)")
    except Exception as e:
        logger.warning("Proactive engine init failed (non-fatal): %s", e)

    # Screenpipe (fire-and-forget, conditional)
    try:
        if os.getenv("SCREENPIPE_ENABLED", "").strip().lower() in ("1", "true", "yes", "on"):
            if os.getenv("SCREENPIPE_PROACTIVE_ENABLED", "1").strip().lower() not in (
                "0",
                "false",
                "no",
                "off",
            ):
                from bridges.screenpipe_bridge import ScreenpipeBridge

                _sp_bridge = ScreenpipeBridge(bot, ALLOWED_USER_ID)
                asyncio.create_task(_sp_bridge.monitor_loop()).add_done_callback(
                    lambda t: (
                        logger.error("Screenpipe monitor loop crashed: %s", t.exception()) if t.exception() else None
                    )
                )
                logger.info("Screenpipe proactive monitor started")
    except Exception as e:
        logger.warning("Screenpipe bridge init failed (non-fatal): %s", e)

    # ruflo sidecar (synchronous launch + async health check)
    global _ruflo_process
    if os.getenv("MINIMAX_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        try:
            proc = subprocess.Popen(
                ["node", "tools/ruflo/server.js"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _ruflo_process = proc
            logger.info("ruflo sidecar launched (pid=%d)", proc.pid)
        except Exception as e:
            logger.warning("ruflo sidecar launch failed (non-fatal): %s", e)

        try:
            if await _wait_for_ruflo_health():
                logger.info("ruflo sidecar healthy on startup")
            else:
                logger.warning("ruflo sidecar health probe failed on startup (non-fatal)")
        except Exception as e:
            logger.warning("ruflo sidecar health probe errored (non-fatal): %s", e)

        # Ruflo Autonomy Layer boot (silent, < 7s) — runs in background after ruflo is healthy
        async def _boot_autonomy_layer() -> None:
            try:
                from core.autonomy import get_autonomy_engine
                engine = get_autonomy_engine()
                result = await engine.boot()
                if result.healthy:
                    logger.info(
                        "Autonomy Layer booted: workers=%d, hooks=%d",
                        result.workers_dispatched,
                        result.hooks_registered,
                    )
                else:
                    logger.warning("Autonomy Layer degraded: %s", result.error_message)
            except Exception as e:
                logger.warning("Autonomy Layer boot failed (non-fatal): %s", e)

        asyncio.create_task(_boot_autonomy_layer()).add_done_callback(
            lambda t: logger.error("Autonomy Layer boot crashed: %s", t.exception())
            if not t.cancelled() and t.exception() else None
        )

        # Restart policy: monitor ruflo and restart if it dies
        task = asyncio.create_task(_ruflo_restart_monitor())
        task.add_done_callback(
            lambda t: logger.error("Ruflo restart monitor died: %s", t.exception())
            if not t.cancelled() and t.exception() else None
        )

    # opencode sidecar (synchronous launch + async health check)
    global _opencode_process
    try:
        proc = subprocess.Popen(
            ["opencode", "serve", "--port", "4096"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={
                **os.environ,
                "LITELLM_BASE_URL": "http://localhost:4000",
            },
        )
        _opencode_process = proc
        logger.info("opencode sidecar launched (pid=%d)", proc.pid)
    except Exception as e:
        logger.warning("opencode sidecar launch failed (non-fatal): %s", e)

    try:
        if await _wait_for_opencode_health():
            logger.info("opencode sidecar healthy on startup")
        else:
            logger.warning("opencode sidecar health probe failed on startup (non-fatal)")
    except Exception as e:
        logger.warning("opencode sidecar health probe errored (non-fatal): %s", e)

    # Initialize swarms_bot enterprise layer
    try:
        from core.swarm import init_swarm_layer

        init_swarm_layer()
    except Exception as e:
        logger.warning("swarms_bot init failed (non-fatal): %s", e)

    # HTTP health endpoint for uptime monitors (GET /health → 200 {"status": "ok"})
    try:
        from core.health import start_health_server

        asyncio.create_task(start_health_server(port=8080)).add_done_callback(
            lambda t: logger.error("Health server crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Health endpoint scheduled on port 8080")
    except Exception as e:
        logger.warning("Health server init failed (non-fatal): %s", e)

    # Webhook server (GitHub, system alerts, etc.)
    try:
        from core.webhooks import WEBHOOK_SERVER
        from core.webhooks.handlers import github, system

        WEBHOOK_SERVER.register("github", github.handle_github_pr_merged)
        WEBHOOK_SERVER.register("system", system.handle_system_alert)
        asyncio.create_task(WEBHOOK_SERVER.start()).add_done_callback(
            lambda t: logger.error("Webhook server crashed: %s", t.exception()) if t.exception() else None
        )
        logger.info("Webhook server started on port %d", WEBHOOK_SERVER.port)
    except Exception as e:
        logger.warning("Webhook server init failed (non-fatal): %s", e)

    # MCP servers (Brave, GitHub, Filesystem, Obsidian, Supabase, Browser)
    try:
        from core.mcp import MCP_MANAGER

        await MCP_MANAGER.start_all()
        logger.info("MCP manager started")
    except Exception as e:
        logger.warning("MCP manager init failed (non-fatal): %s", e)

    # Optional: keep GitNexus graph index fresh for Claude/OpenCode/Legion prompt context
    if os.getenv("LEGION_GITNEXUS_AUTO_ANALYZE", "0").strip().lower() in ("1", "true", "yes", "on"):
        try:
            from core.gitnexus_bridge import run_gitnexus_analyze

            asyncio.create_task(run_gitnexus_analyze(with_skills=True)).add_done_callback(
                lambda t: logger.warning("GitNexus auto-analyze failed: %s", t.exception()) if t.exception() else None
            )
            logger.info("GitNexus auto-analyze scheduled")
        except Exception as e:
            logger.warning("GitNexus auto-analyze init failed (non-fatal): %s", e)

    # fix: wrap set_my_commands in try/except — Telegram API slowness on startup
    # must not prevent the rest of the boot sequence from completing.
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="do", description="Autonomous computer control (tool-calling)"),
                BotCommand(command="autopilot", description="Vision-action loop — desktop automation"),
                BotCommand(command="confirm", description="Confirm dangerous action in autopilot"),
                BotCommand(command="screen", description="Take desktop screenshot"),
                BotCommand(command="run", description="LLM chat (no computer)"),
                BotCommand(command="swarm", description="Multi-agent team execution"),
                BotCommand(command="owl", description="OWL specialist complex-task agent"),
                BotCommand(command="predict", description="Swarm consensus prediction"),
                BotCommand(command="code_exec", description="Write + execute code safely"),
                BotCommand(command="ag2", description="AG2 multi-agent research conversation"),
                BotCommand(command="swarm_viz", description="Visualize agents/thoughts/communications"),
                BotCommand(command="think", description="QwQ deep reasoning"),
                BotCommand(command="cmd", description="Run shell command"),
                BotCommand(command="code", description="Plan a coding task with Plandex"),
                BotCommand(command="apply", description="Apply pending Plandex plan"),
                BotCommand(command="abort", description="Abort pending Plandex plan"),
                BotCommand(command="diff", description="Review pending Plandex diff"),
                BotCommand(command="fix", description="Run SWE-agent on GitHub issue"),
                BotCommand(command="fix_dry", description="SWE-agent dry-run (no PR)"),
                # Research
                BotCommand(command="paper", description="Search arXiv papers"),
                BotCommand(command="ask_paper", description="Ask about a paper"),
                # DEPRECATED: workernet_papers — removed from menu (handler still works for backward compat)
                BotCommand(command="research", description="Deep web research"),
                BotCommand(command="jarvis", description="Context bundle + plan (no auto-send)"),
                BotCommand(command="scrape", description="Scrape a URL"),
                # Memory
                BotCommand(command="memory", description="Humanized memory stats"),
                BotCommand(command="remember", description="Save a note to memory"),
                BotCommand(command="recall", description="Search memory"),
                BotCommand(command="forget", description="Remove core memory key"),
                BotCommand(command="emotion", description="Legion emotional state"),
                BotCommand(command="voice_toggle", description="Toggle voice replies"),
                BotCommand(command="oi", description="Force Open Interpreter computer control"),
                BotCommand(command="om_stats", description="OpenMemory sector statistics"),
                BotCommand(command="n8n", description="n8n automation status"),
                BotCommand(command="debate", description="Debate a topic with Legion"),
                BotCommand(command="opinion", description="Get Legion's honest opinion"),
                BotCommand(command="opinions", description="Legion current opinions"),
                BotCommand(command="profile", description="Persistent user profile"),
                BotCommand(command="teach", description="Teach/correct Legion profile"),
                BotCommand(command="memories", description="Show recent memories"),
                BotCommand(command="briefing", description="Morning briefing"),
                BotCommand(command="harvest_review", description="Review pending harvest candidates"),
                BotCommand(command="harvest_stats", description="Harvest quality statistics"),
                BotCommand(command="monitor", description="System health + alert thresholds"),
                # Business
                BotCommand(command="biz", description="Business metrics dashboard"),
                BotCommand(command="self_review", description="Legion self-improvement review"),
                # Dev
                BotCommand(command="scaffold", description="Create project scaffold"),
                BotCommand(command="build", description="Parallel fullstack build"),
                BotCommand(command="gpu", description="GPU health status"),
                BotCommand(command="vuln_scan", description="Vulnerability scan"),
                BotCommand(command="opencode", description="Route task to opencode CLI"),
                BotCommand(command="codex", description="Route task to Claude Code"),
                # Tasks
                BotCommand(command="task_from", description="Extract tasks from text"),
                BotCommand(command="tasks_due", description="Show pending tasks"),
                # Content
                BotCommand(command="post", description="Draft social media post"),
                BotCommand(command="threads_mode", description="Toggle Threads campaign mode"),
                BotCommand(command="brand_check", description="Monitor brand mentions"),
                # Code Quality
                BotCommand(command="review", description="AI code review"),
                BotCommand(command="security_review", description="Security audit"),
                # Orchestration
                BotCommand(command="orchestrate", description="Decompose + execute complex task"),
                BotCommand(command="multi_plan", description="Compare 3 agent approaches"),
                BotCommand(command="plan", description="ECC-style implementation planning"),
                BotCommand(command="quality_gate", description="Generate + verify grounded answer"),
                BotCommand(command="verify", description="Alias for quality gate"),
                BotCommand(command="eval", description="Evaluate/verify an answer or plan"),
                BotCommand(command="model_route", description="Show routed agent/model chain"),
                BotCommand(command="harness_audit", description="Harness readiness audit"),
                BotCommand(command="code_review", description="ECC-style code review"),
                BotCommand(command="python_review", description="Python-focused code review"),
                BotCommand(command="refactor_clean", description="Format + cleanup review"),
                BotCommand(command="test_coverage", description="Run pytest coverage"),
                BotCommand(command="tdd", description="Generate TDD plan"),
                BotCommand(command="prompt_optimize", description="Optimize a prompt"),
                BotCommand(command="build_fix", description="Analyze build failures"),
                BotCommand(command="go_build", description="Run go build ./..."),
                BotCommand(command="go_test", description="Run go test ./..."),
                BotCommand(command="go_review", description="Review Go code"),
                BotCommand(command="kotlin_build", description="Run Kotlin/Gradle build"),
                BotCommand(command="kotlin_test", description="Run Kotlin/Gradle tests"),
                BotCommand(command="kotlin_review", description="Review Kotlin code"),
                BotCommand(command="gradle_build", description="Run Gradle build"),
                BotCommand(command="pm2", description="Check PM2 status"),
                BotCommand(command="promote", description="Generate promotion notes"),
                BotCommand(command="evolve", description="Create evolution roadmap"),
                BotCommand(command="aside", description="Create concise side note"),
                BotCommand(command="loop", description="Autonomous goal execution loop"),
                BotCommand(command="loop_stop", description="Stop running loop"),
                BotCommand(command="loop_status", description="Loop progress status"),
                BotCommand(command="loop_pause", description="Pause running loop"),
                BotCommand(command="loop_resume", description="Resume paused loop"),
                BotCommand(command="multi_execute", description="Alias multi-agent compare"),
                BotCommand(command="budget", description="Cost tracking dashboard"),
                BotCommand(command="soul", description="Show current SOUL.md"),
                BotCommand(command="capabilities", description="Honest capability status"),
                BotCommand(command="self_report", description="24h activity summary"),
                BotCommand(command="metrics", description="Performance metrics dashboard"),
                BotCommand(command="routing_stats", description="Routing analytics"),
                BotCommand(command="audit_summary", description="Audit log summary"),
                # Sessions & Learning
                BotCommand(command="save", description="Save session state"),
                BotCommand(command="resume", description="Resume saved session"),
                BotCommand(command="checkpoint", description="Save named checkpoint"),
                BotCommand(command="sessions", description="List saved sessions"),
                BotCommand(command="learn", description="Teach a pattern"),
                BotCommand(command="learn_eval", description="Evaluate learned instincts"),
                BotCommand(command="instincts", description="Show learned patterns"),
                BotCommand(command="instinct_status", description="Instincts by category"),
                BotCommand(command="skill_create", description="Create a new skill file"),
                BotCommand(command="update_docs", description="Generate docs update draft"),
                BotCommand(command="update_codemaps", description="Regenerate codemap doc"),
                BotCommand(command="projects", description="List workspace projects/files"),
                BotCommand(command="setup_pm", description="Package manager/setup guide"),
                BotCommand(command="claw", description="Delegate to OpenClaw"),
                BotCommand(command="audit", description="Activity audit trail"),
                # Wiki
                BotCommand(command="wiki_audit", description="Wiki quality status + quarantine"),
                BotCommand(command="wiki_scan", description="Run full wiki deep evaluation"),
                BotCommand(command="wiki_stats", description="Wiki quality by directory"),
                BotCommand(command="wiki_flush", description="Delete quarantined wiki files"),
                BotCommand(command="wiki_restore", description="Restore quarantined files"),
                # System
                BotCommand(command="models", description="Agent roster"),
                BotCommand(command="keys", description="API key status"),
                BotCommand(command="resources", description="RAM / GPU / local model policy"),
                BotCommand(command="stats", description="System stats"),
                BotCommand(command="visualize", description="Visual dashboard + architecture"),
                BotCommand(command="capability_stats", description="Capability quality leaderboard"),
                BotCommand(command="benchmark", description="Run capability benchmark suite"),
                BotCommand(command="redteam", description="Run red-team capability suite"),
                BotCommand(command="start", description="Help + status"),
            ]
        )
        logger.info("Bot commands registered")
    except Exception as e:
        logger.warning("set_my_commands failed (non-fatal): %s", e)

    key_status = verify_api_keys()
    active = [k for k, v in key_status.items() if v]
    cloud = ["MINIMAX_API_KEY", "OLLAMA_API_KEY"]

    display = await computer_agent.detect_display()

    logger.info("=" * 55)
    logger.info("Legion v4 starting")
    logger.info("\u2705 Keys: %s", ", ".join(active) or "NONE")
    logger.info("\U0001f5a5 Display: %s", display)
    if not any(key_status.get(k) for k in cloud):
        logger.critical("NO CLOUD KEYS — all requests will fail!")
    logger.info("=" * 55)


async def on_shutdown(dispatcher: Dispatcher) -> None:
    """Graceful shutdown: stop accepting new messages, finish in-flight, flush, close."""
    global _shutdown_flag
    _shutdown_flag = True
    logger.info("Legion shutting down gracefully — %d tasks running", len(asyncio.all_tasks()))

    # 1. Stop accepting new messages (flag set)
    logger.info("Shutdown step 1/5: new message acceptance disabled")

    # 2. Finish processing in-flight (wait up to 10s)
    logger.info("Shutdown step 2/5: waiting for in-flight tasks (max 10s)")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        for task in tasks:
            task.cancel()
        await asyncio.wait(tasks, timeout=10.0)

    # 3. Flush memory writes
    logger.info("Shutdown step 3/5: flushing memory writes")
    try:
        from tools.persistence import get_engine

        engine = get_engine()
        if engine:
            engine.flush()
    except Exception:
        pass

    # 4. Close DB connections
    logger.info("Shutdown step 4/6: closing DB connections")
    try:
        if _harvester_scheduler:
            await _harvester_scheduler.stop()
    except Exception:
        pass
    try:
        if getattr(_shared, "_legiona_scheduler", None):
            _shared._legiona_scheduler.shutdown(wait=False)
    except Exception:
        pass
    try:
        from core.mcp import MCP_MANAGER

        await MCP_MANAGER.stop_all()
    except Exception:
        pass
    try:
        from tools.memory import close_memory_db

        close_memory_db()
    except Exception:
        pass
    try:
        from tools.agentops_client import end_session

        end_session()
    except Exception:
        pass
    try:
        from core.memory.memory_manager import get_memory

        mem = get_memory()
        mem.close()
    except Exception:
        pass

    # Emit session_end so registered hooks (e.g. opencode_session_end_hook) fire automatically
    try:
        from core.hooks import get_hooks
        hooks = get_hooks()
        await hooks.emit("session_end", {"source": "legion_shutdown"})
    except Exception:
        pass

    # 5a. Autonomy Layer teardown (Part X — silent session save + memory flush)
    logger.info("Shutdown step 5a/7: Autonomy Layer session teardown")
    try:
        from core.autonomy import get_autonomy_engine
        engine = get_autonomy_engine()
        if engine.is_healthy or engine.task_count > 0:
            await engine.shutdown()
    except Exception:
        pass

    # 5b. Flush and stop observation queue
    logger.info("Shutdown step 5b/7: stopping observation queue")
    try:
        from core.memory.observation_queue import get_observation_queue
        queue = get_observation_queue()
        await queue.stop()
    except Exception:
        pass

    # 6. Log shutdown
    logger.info("Shutdown step 6/7: shutdown complete")
    logger.info("Legion shutdown complete — exiting cleanly")


async def main() -> None:
    # LEGION BOOT — full subsystem health check
    boot_health = await run_legion_boot_health(bot)
    print_legion_boot_report(boot_health)

    # Legacy health check (feature flags)
    health = run_health_check()
    print_health_report(health)
    _shared.FEATURE_FLAGS = FEATURE_FLAGS

    # Environment validation
    _required = ["TELEGRAM_BOT_TOKEN"]
    _missing_req = [k for k in _required if not os.getenv(k)]
    _optional_warn = []
    for _opt in ["SUPABASE_URL", "CHROMADB_HOST", "ADMIN_USER_IDS"]:
        if not os.getenv(_opt):
            _optional_warn.append(_opt)

    if _missing_req:
        logger.critical("Missing required env vars: %s — exiting.", _missing_req)
        sys.exit(1)
    if _optional_warn:
        logger.warning("Missing optional env vars (functionality may be limited): %s", _optional_warn)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
