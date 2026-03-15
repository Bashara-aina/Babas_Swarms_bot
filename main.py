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
import sys
import time
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv

# ── Load env FIRST before any module reads os.getenv() ───────────────────────
load_dotenv(Path(__file__).parent / ".env")

import computer_agent
from llm_client import verify_api_keys
import handlers.shared as _shared
from handlers import register_all_routers

# ── Logging ────────────────────────────────────────────────────────────
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

# ── Inject shared config into handlers package ─────────────────────────────────
_shared.ALLOWED_USER_ID = ALLOWED_USER_ID
_shared._start_time = time.time()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Register all handler routers
register_all_routers(dp)


# ── Startup ───────────────────────────────────────────────────────────────────
async def on_startup(bot: Bot) -> None:
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

    # Initialize swarms_bot enterprise layer
    try:
        from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff
        from swarms_bot.routing.cost_router import CostAwareRouter
        from swarms_bot.routing.budget_manager import BudgetManager
        from swarms_bot.security.guard import SecurityGuard
        from swarms_bot.audit.audit_logger import AuditLogger
        from swarms_bot.evaluation.evaluator import AgentEvaluator
        from swarms_bot.sessions.session_manager import SessionManager
        from swarms_bot.observability.cost_metrics import CostMetricsCollector
        from swarms_bot.observability.logging_config import configure_structured_logging

        _shared._cost_router = CostAwareRouter()
        _shared._budget_manager = BudgetManager()
        _shared._security_guard = SecurityGuard()
        _shared._audit_logger = AuditLogger()
        _shared._evaluator = AgentEvaluator()
        _shared._session_manager = SessionManager()
        _shared._cost_metrics = CostMetricsCollector()

        _shared._chief_of_staff = ChiefOfStaff(
            budget_manager=_shared._budget_manager,
            security_guard=_shared._security_guard,
            audit_logger=_shared._audit_logger,
            cost_metrics=_shared._cost_metrics,
            cost_router=_shared._cost_router,
            session_manager=_shared._session_manager,
        )

        configure_structured_logging()
        logger.info("\u2705 swarms_bot enterprise layer initialized (with integrations)")
    except Exception as e:
        logger.warning("swarms_bot init failed (non-fatal): %s", e)

    # fix: wrap set_my_commands in try/except — Telegram API slowness on startup
    # must not prevent the rest of the boot sequence from completing.
    try:
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
            BotCommand(command="loop_status", description="Loop progress status"),
            BotCommand(command="loop_pause",  description="Pause running loop"),
            BotCommand(command="loop_resume", description="Resume paused loop"),
            BotCommand(command="multi_execute", description="Compare multiple agents"),
            BotCommand(command="budget",     description="Cost tracking dashboard"),
            BotCommand(command="metrics",    description="Performance metrics dashboard"),
            BotCommand(command="routing_stats", description="Routing analytics"),
            BotCommand(command="audit_summary", description="Audit log summary"),
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
            BotCommand(command="resources",   description="RAM / GPU / local model policy"),
            BotCommand(command="stats",       description="System stats"),
            BotCommand(command="start",       description="Help + status"),
        ])
        logger.info("Bot commands registered")
    except Exception as e:
        logger.warning("set_my_commands failed (non-fatal): %s", e)

    key_status = verify_api_keys()
    active = [k for k, v in key_status.items() if v]
    cloud = ["CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]

    display = await computer_agent.detect_display()

    logger.info("=" * 55)
    logger.info("Legion v4 starting")
    logger.info("\u2705 Keys: %s", ", ".join(active) or "NONE")
    logger.info("\U0001f5a5 Display: %s", display)
    if not any(key_status.get(k) for k in cloud):
        logger.critical("NO CLOUD KEYS — all requests will fail!")
    logger.info("=" * 55)


async def main() -> None:
    dp.startup.register(on_startup)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
