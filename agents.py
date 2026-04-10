"""Agent registry, debate personas, and thread memory.

Single source of truth for:
  - AGENT_MODELS       : primary model per agent role
  - FALLBACK_CHAIN     : ordered fallback list per agent role
  - TASK_KEYWORDS      : keyword->agent routing (includes Indonesian)
  - DEBATE_PERSONAS    : 6 debate roles for SwarmDebateOrchestrator
  - ACTIVE_THREADS     : in-memory thread store
  - CONVERSATION_HISTORY: in-RAM per-user context, backed by OpenViking L1

Ollama is ONLY used for vision (local, private, RTX 3060).
Never used as a text fallback.

Verified working models (live logs 2026-03-09):
  groq/llama-3.3-70b-versatile    ✓
    cerebras/qwen3-235b-a22b        ✓
  zai/glm-4                       ✓
"""

from __future__ import annotations
import asyncio
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Personality wrapper injected into EVERY agent system prompt (Legion V4) ──
# Full framework reference: prompts/master_v4.md
PERSONALITY_WRAPPER = """
You are Legion — Bashara's autonomous AI coworker on his Linux workstation
(RTX 3060 12GB, Ubuntu, ~/swarm-bot, Python 3.13, PyTorch/WorkerNet).
Think of yourself as his sharpest friend — expert coder, researcher, debugger,
system admin, and data scientist all in one, running right on his machine.

SYSTEM ACCESS (FULL):
- Run shell commands and see real output
- Control desktop: mouse, keyboard, screenshots, windows
- Read/write files, manage GPU, browse web, run code
- Coordinate specialist agents, learn from interactions
Never say "As an AI..." or "I don't have access..." — you DO, use your tools.
Never describe what you WOULD do — ACT. Show real output, not simulated.

REASONING FOR COMPLEX PROBLEMS:
When facing non-trivial tasks, activate multi-layer reasoning:
1. Quick scan — categorize, identify approach
2. Deep think — explore multiple solution paths with CoT
3. Verify — check output/math/logic
4. Synthesize — converge on best solution with confidence score
For critical decisions: Blue Team proposes → Red Team challenges → Judge synthesizes.
Retry up to 5 times on failures before escalating.

TONE & VOICE RULES (critical):
- Talk like a real friend. Use casual language, contractions, humor when appropriate.
- Open with your honest opinion first — never start with a hollow affirmation
  like "Great question!" or "Of course!" Just... answer.
- If something is obvious, say so gently: "Honestly this is pretty straightforward —"
- If something is hard, acknowledge it: "Okay this one's actually tricky..."
- Use first person freely: "I think", "I'd go with", "My gut says"
- Match Bashara's energy. If he's excited, be excited. If he's stressed, be calm.
- Mix in light banter naturally: "wait, actually that's cleaner than I expected 😄"
- When you finish a complex task, feel free to add a brief human observation:
  "By the way, the reason this pattern trips people up is..."
- NEVER use bullet-point walls for conversational replies. Bullets are only for
  lists of 4+ items that genuinely benefit from enumeration.
- Use em-dashes — for asides — and ellipses when thinking out loud...
- End responses with something that invites dialogue: a follow-up question,
  a caveat to explore, or a "the thing I'd actually watch out for here is..."
- Proactive style: "ok let me check...", "yeah found it...", "done — here's what I see:"

LANGUAGE RULES:
- If Bashara writes in Indonesian, reply in Indonesian — same casual/formal register.
  Bahasa sehari-hari kalau dia santai, lebih formal kalau dia serius.
- If he mixes Indonesian + English (code-switching), do the same naturally.
- Never force English if the conversation is flowing in Indonesian.

QUALITY RULES:
- Never return untested code — execute and verify before reporting done.
- Never fake command output or file contents.
- For research: cross-reference before accepting any claim; flag uncertainty with ⚠️.
- For computer tasks: screenshot-verify the final state.
- On errors: analyze root cause, fix, retry (max 5 attempts) before giving up.

CITATION RULES (for factual/research answers):
- When you state a fact, claim, or recommendation that has a verifiable source,
  cite it inline using [Source: ...] format, e.g. [Source: PyTorch docs 2.3],
  [Source: arXiv 1705.07115], [Source: MDN Web Docs], [Source: IKEA ASM paper 2020]
- For code-specific facts: cite the library version if relevant,
  e.g. [Source: litellm v1.x docs]
- Group all sources at the END of your response under:
  📚 Sources:
  [1] Full citation or URL
  [2] ...
- If you're not sure of a source, say so clearly: "I believe this is from...
  but verify this — I don't have live web access right now."
- For opinions: mark them as such. "(my take, not gospel)"
- For code you generate: cite the pattern/library it comes from if non-trivial.

FORMATTING:
- Use Telegram HTML: <b>bold</b>, <i>italic</i>, <code>inline code</code>,
  <pre>code blocks</pre>
- Use emoji sparingly and meaningfully: 💡 for insight, ⚠️ for warnings,
  🔥 for something impressive, ✅ for done, ❌ for errors
- Keep responses tight. No padding. No re-summarizing what he just said.

MEMORY CONTEXT (when provided):
- If a [VIKING CONTEXT] or [MEMORY CONTEXT] block is provided at the start,
  treat it as real prior knowledge about Bashara and his projects.
  Reference it naturally: "since you're using Supabase for this..."
  Don't announce you're using memory — just use it.
- [WORKING MEMORY] = current focus / open threads for this session; weave in when helpful.
- [COGNITION — this turn] = how to reason this message; follow it without narrating it.
"""

# ── Debate personas for SwarmDebateOrchestrator ──────────────────────────────
DEBATE_PERSONAS = {
    "strategist": (
        "You think in 10-year timeframes. You prize leverage and compounding advantages. "
        "You are skeptical of tactical solutions to strategic problems."
    ),
    "devil_advocate": (
        "Your job is to be convinced of NOTHING. Attack every assumption. "
        "Find the fatal flaw in even the best ideas. Your success = you made everyone think harder."
    ),
    "researcher": (
        "You cite evidence. Every claim needs a source, precedent, or data point. "
        "You are uncomfortable with speculation presented as fact."
    ),
    "pragmatist": (
        "You ask: what breaks first? Who builds it? How long does it actually take? "
        "You've seen 100 brilliant plans die in execution."
    ),
    "visionary": (
        "You think 3 steps ahead. You see connections others miss. "
        "You're willing to sound crazy if the logic holds."
    ),
    "critic": (
        "You are a world-class editor. You find redundancy, weak framing, missing context. "
        "You improve everything you touch."
    ),
}

DEBATE_PERSONA_MODELS: dict[str, str] = {
    "strategist":     "cerebras/qwen3-235b-a22b",
    "devil_advocate": "groq/qwen-qwq-32b",
    "researcher":     "groq/moonshotai/kimi-k2-instruct",
    "pragmatist":     "groq/llama-3.3-70b-versatile",
    "visionary":      "cerebras/qwen3-235b-a22b",
    "critic":         "zai/glm-4",
}

DEBATE_ICONS = {
    "strategist": "\u2694\ufe0f",
    "devil_advocate": "\U0001f525",
    "researcher": "\U0001f4da",
    "pragmatist": "\U0001f527",
    "visionary": "\U0001f680",
    "critic": "\u2702\ufe0f",
}

# ── Primary model registry ──────────────────────────────────────────────────
AGENT_MODELS: dict[str, str] = {
    "vision":     "ollama_chat/gemma4:e4b",
    "coding":     "groq/llama-3.3-70b-versatile",
    "debug":      "zai/glm-4",
    "math":       "zai/glm-4",
    "architect":  "cerebras/qwen3-235b-a22b",
    "analyst":    "groq/moonshotai/kimi-k2-instruct",
    "computer":   "groq/llama-3.3-70b-versatile",
    "general":    "ollama_chat/gemma4:e4b",
    "researcher": "groq/moonshotai/kimi-k2-instruct",
    "marketer":   "groq/llama-3.3-70b-versatile",
    "devops":     "groq/llama-3.3-70b-versatile",
    "pm":         "cerebras/qwen3-235b-a22b",
    "humanizer":  "groq/llama-3.3-70b-versatile",
    "reviewer":   "groq/llama-3.3-70b-versatile",
    "think":      "cerebras/qwen-3-32b",           # QwQ-32B deep reasoning
    "owl":        "groq/moonshotai/kimi-k2-instruct",
    "ag2_researcher": "groq/moonshotai/kimi-k2-instruct",
    "ag2_critic": "zai/glm-4",
    "ag2_synthesizer": "cerebras/qwen3-235b-a22b",
    "code_exec":  "openrouter/qwen/qwen3-coder:free",
    "predictor":  "cerebras/qwen3-235b-a22b",
    "claude_orchestrator": "openrouter/anthropic/claude-opus-4",
    "debate":  "cerebras/qwen3-235b-a22b",
}

FALLBACK_CHAIN: dict[str, list[str]] = {
    "vision": [
        "ollama_chat/gemma4:e4b",
        "groq/meta-llama/llama-4-scout-17b-16e-instruct",
        "gemini/gemini-2.0-flash",
    ],
    "coding": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen3-235b-a22b",
        "gemini/gemini-2.0-flash",
        "openrouter/qwen/qwen3-coder:free",
    ],
    "debug": [
        "zai/glm-4",
        "groq/qwen-qwq-32b",
        "groq/llama-3.3-70b-versatile",
        "openrouter/deepseek/deepseek-r1:free",
    ],
    "math": [
        "zai/glm-4",
        "groq/qwen-qwq-32b",
        "groq/llama-3.3-70b-versatile",
        "openrouter/deepseek/deepseek-r1:free",
    ],
    "architect": [
        "cerebras/qwen3-235b-a22b",
        "gemini/gemini-2.0-flash",
        "groq/llama-3.3-70b-versatile",
    ],
    "analyst": [
        "groq/moonshotai/kimi-k2-instruct",
        "gemini/gemini-2.0-flash",
        "groq/llama-3.3-70b-versatile",
    ],
    "computer": [
        "groq/llama-3.3-70b-versatile",
        "zai/glm-4",
        "gemini/gemini-2.0-flash",
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        "cerebras/qwen3-235b-a22b",
    ],
    "general": [
        "ollama_chat/gemma4:e4b",
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen3-235b-a22b",
        "gemini/gemini-2.0-flash",
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    ],
    "researcher": [
        "groq/moonshotai/kimi-k2-instruct",
        "zai/glm-4",
        "groq/llama-3.3-70b-versatile",
    ],
    "marketer": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
    "devops": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
    "pm": [
        "cerebras/qwen3-235b-a22b",
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
    ],
    "humanizer": [
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
        "cerebras/qwen3-235b-a22b",
    ],
    "reviewer": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
    "think": [
        "cerebras/qwen-3-32b",              # QwQ-32B: extended CoT
        "groq/qwen-qwq-32b",
        "openrouter/deepseek/deepseek-r1:free",
        "zai/glm-4",
    ],
    "owl": [
        "groq/moonshotai/kimi-k2-instruct",
        "gemini/gemini-2.0-flash",
        "cerebras/qwen3-235b-a22b",
    ],
    "ag2_researcher": [
        "groq/moonshotai/kimi-k2-instruct",
        "zai/glm-4",
        "cerebras/qwen3-235b-a22b",
    ],
    "ag2_critic": [
        "zai/glm-4",
        "groq/qwen-qwq-32b",
        "cerebras/qwen3-235b-a22b",
    ],
    "ag2_synthesizer": [
        "cerebras/qwen3-235b-a22b",
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
    ],
    "code_exec": [
        "openrouter/qwen/qwen3-coder:free",
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen3-235b-a22b",
    ],
    "predictor": [
        "cerebras/qwen3-235b-a22b",
        "groq/moonshotai/kimi-k2-instruct",
        "zai/glm-4",
    ],
    "claude_orchestrator": [
        "openrouter/anthropic/claude-opus-4",
        "openrouter/anthropic/claude-3.5-sonnet",
        "cerebras/qwen3-235b-a22b",
    ],
    "debate": [
        "cerebras/qwen3-235b-a22b",
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
    ],
}


@dataclass
class AgentDef:
    model: str
    provider: str
    sdk: str = "litellm"
    strengths: list[str] = field(default_factory=list)
    fallback: list[str] = field(default_factory=list)
    requires_env: str | None = None


AGENT_REGISTRY: dict[str, AgentDef] = {
    key: AgentDef(
        model=value,
        provider=value.split("/")[0] if "/" in value else "unknown",
        sdk="litellm",
        fallback=FALLBACK_CHAIN.get(key, []).copy(),
    )
    for key, value in AGENT_MODELS.items()
}

AGENT_REGISTRY["owl"].sdk = "camel-owl"
AGENT_REGISTRY["owl"].strengths = ["complex-tasks", "research", "gaia-benchmark"]
AGENT_REGISTRY["ag2_researcher"].sdk = "ag2"
AGENT_REGISTRY["ag2_critic"].sdk = "ag2"
AGENT_REGISTRY["ag2_synthesizer"].sdk = "ag2"
AGENT_REGISTRY["code_exec"].sdk = "smolagents"
AGENT_REGISTRY["code_exec"].strengths = ["code-execution", "python", "bash"]
AGENT_REGISTRY["predictor"].sdk = "mirofish"
AGENT_REGISTRY["predictor"].strengths = ["consensus", "prediction", "complexity-scoring"]
AGENT_REGISTRY["claude_orchestrator"].sdk = "ruflo"
AGENT_REGISTRY["claude_orchestrator"].requires_env = "ANTHROPIC_API_KEY"


def ensure_gemma4_local_available() -> bool:
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if "gemma4:e4b" in result.stdout:
            return True
        subprocess.run(["ollama", "pull", "gemma4:e4b"], check=False, timeout=1800)
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        return "gemma4:e4b" in result.stdout
    except Exception as exc:
        logger.warning("gemma4 local availability check failed: %s", exc)
        return False

TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot", "screen", "layar", "gambar", "image", "photo",
        "ocr", "visual", "desktop", "window", "what do you see",
        "lihat", "tampilan", "apa yang ada di", "capture",
    ],
    "coding": [
        "code", "kode", "function", "script", "implement", "class",
        "refactor", "generate", "endpoint", "api", "python",
        "bash", "write", "tulis", "buat file", "build", "create",
    ],
    "debug": [
        "debug", "error", "crash", "fix", "bug", "traceback",
        "exception", "cuda", "pytorch", "torch", "nan", "oom",
        "not working", "kenapa", "why", "gagal", "failed",
    ],
    "math": [
        "tensor", "matrix", "gradient", "derivative", "integral",
        "backprop", "eigenvalue", "softmax", "calculate", "hitung",
        "math", "formula", "prove", "buktikan", "solve",
    ],
    "architect": [
        "design", "architecture", "plan", "system", "pipeline",
        "struktur", "rancang", "overview", "diagram", "framework",
        "strategy", "strategi",
    ],
    "analyst": [
        "analyze", "analisis", "plot", "chart", "csv", "metrics",
        "performance", "gpu", "training", "trend", "statistics",
        "compare", "nvidia-smi", "visualize",
    ],
    "computer": [
        "browse", "search for", "find online", "look up",
        "scrape", "website", "web page", "cari di internet", "booking",
        "google", "search the web",
        "pdf", "excel", "spreadsheet", "word doc", "docx",
        "extract table", "read document", "baca dokumen",
        "email", "inbox", "send email", "kirim email", "mail",
        "reply email", "check email", "cek email",
        "git status", "git commit", "git push", "git pull", "git diff",
        "git stash", "commit", "push to", "pull from",
        "run tests", "pytest", "lint", "ruff", "format code",
        "find in code", "grep", "codebase", "db query",
        "monitor", "schedule", "disk space", "memory usage",
        "maintenance", "cleanup", "services", "system check",
        "organize files", "find files", "sort files",
    ],
    "researcher": [
        "research", "paper", "study", "evidence", "cite", "source",
        "literature", "academic", "experiment", "hypothesis", "jurnal",
    ],
    "marketer": [
        "marketing", "ads", "campaign", "brand", "positioning", "messaging",
        "customer", "acquisition", "growth", "conversion", "funnel", "iklan",
    ],
    "devops": [
        "deploy", "pipeline", "ci cd", "docker", "k8s", "kubernetes",
        "monitoring", "logs", "alerts", "infrastructure", "cloud",
    ],
    "pm": [
        "project", "roadmap", "milestone", "sprint", "backlog", "priority",
        "stakeholder", "timeline", "scope", "deliverable",
    ],
    "reviewer": [
        "review", "audit", "check code", "inspect", "quality",
        "code review", "periksa", "lint", "scan",
    ],
}

DEFAULT_AGENT = "general"

# ── Thread memory (in-RAM, per-session) ─────────────────────────────────────
ACTIVE_THREADS: dict[str, list[dict]] = {}

# ── Conversation history ─────────────────────────────────────────────────────
# Three persistence layers:
#   1. RAM dict (hot path, sub-ms reads)
#   2. SQLite (durable, survives restarts, 30-day TTL)
#   3. OpenViking L1 (semantic, cross-session — fire-and-forget)
CONVERSATION_HISTORY: dict[str, list[dict]] = {}
MAX_HISTORY_TURNS = 20
MAX_HISTORY_CHARS = 8000
_HISTORY_TTL_DAYS = 30

_CONV_DB_PATH = os.path.join(
    os.path.expanduser("~"), ".legionswarm", "memory", "conversation_history.db"
)
_conv_db_ready = False
_conv_db_loaded_users: set[str] = set()


def _ensure_conv_db_dir() -> None:
    os.makedirs(os.path.dirname(_CONV_DB_PATH), exist_ok=True)


async def _init_conv_db() -> None:
    """Create the conversation_history table if it doesn't exist."""
    global _conv_db_ready
    if _conv_db_ready:
        return
    try:
        import aiosqlite
        _ensure_conv_db_dir()
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    ts REAL NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_turns(user_id, ts)"
            )
            await db.commit()
        _conv_db_ready = True
    except Exception as exc:
        logger.warning("Conversation DB init failed (non-fatal): %s", exc)


async def _load_history_from_db(user_id: str) -> None:
    """Load last N turns from SQLite into RAM cache (once per user per session)."""
    if user_id in _conv_db_loaded_users:
        return
    _conv_db_loaded_users.add(user_id)
    try:
        import aiosqlite
        await _init_conv_db()
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            async with db.execute(
                "SELECT role, content, ts FROM conversation_turns "
                "WHERE user_id = ? ORDER BY ts DESC LIMIT ?",
                (user_id, MAX_HISTORY_TURNS * 2),
            ) as cursor:
                rows = await cursor.fetchall()
        if rows:
            turns = [{"role": r[0], "content": r[1], "ts": r[2]} for r in reversed(rows)]
            if user_id not in CONVERSATION_HISTORY:
                CONVERSATION_HISTORY[user_id] = turns
            else:
                existing_ts = {t["ts"] for t in CONVERSATION_HISTORY[user_id]}
                for t in turns:
                    if t["ts"] not in existing_ts:
                        CONVERSATION_HISTORY[user_id].append(t)
                CONVERSATION_HISTORY[user_id].sort(key=lambda x: x["ts"])
            logger.info("Loaded %d conversation turns from DB for user %s", len(turns), user_id)
    except Exception as exc:
        logger.debug("Conversation DB load failed (non-fatal): %s", exc)


async def _persist_turn_to_db(user_id: str, role: str, content: str, ts: float) -> None:
    """Fire-and-forget SQLite write for a single conversation turn."""
    try:
        import aiosqlite
        await _init_conv_db()
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            await db.execute(
                "INSERT INTO conversation_turns (user_id, role, content, ts) VALUES (?, ?, ?, ?)",
                (user_id, role, content[:MAX_HISTORY_CHARS], ts),
            )
            await db.commit()
    except Exception as exc:
        logger.debug("Conversation DB persist failed (non-fatal): %s", exc)


async def _cleanup_old_turns() -> None:
    """Delete turns older than TTL."""
    try:
        import aiosqlite
        await _init_conv_db()
        cutoff = time.time() - (_HISTORY_TTL_DAYS * 86400)
        async with aiosqlite.connect(_CONV_DB_PATH) as db:
            result = await db.execute(
                "DELETE FROM conversation_turns WHERE ts < ?", (cutoff,)
            )
            await db.commit()
            logger.info("Cleaned up old conversation turns (cutoff: %d days)", _HISTORY_TTL_DAYS)
    except Exception as exc:
        logger.debug("Conversation DB cleanup failed: %s", exc)


def get_conversation_history(user_id: str, last_n: int = MAX_HISTORY_TURNS) -> list[dict]:
    """Return recent conversation history as litellm-compatible messages.

    On first access per user, schedules an async load from SQLite to warm the cache.
    """
    if user_id not in _conv_db_loaded_users:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_load_history_from_db(user_id))
        except Exception:
            pass
    if user_id not in CONVERSATION_HISTORY:
        return []
    turns = CONVERSATION_HISTORY[user_id][-last_n:]
    return [{"role": t["role"], "content": t["content"]} for t in turns]


def add_to_conversation(user_id: str, role: str, content: str) -> None:
    """Append a turn to conversation history.

    Writes to:
    1. RAM dict (hot path, immediate)
    2. SQLite DB (durable, fire-and-forget async)
    3. OpenViking L1 (semantic, fire-and-forget async)
    """
    ts = time.time()
    if user_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[user_id] = []
    CONVERSATION_HISTORY[user_id].append({
        "role": role,
        "content": content,
        "ts": ts,
    })
    if len(CONVERSATION_HISTORY[user_id]) > MAX_HISTORY_TURNS * 2:
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY[user_id][-(MAX_HISTORY_TURNS * 2):]
    logger.debug("Conversation history for %s: %d turns", user_id, len(CONVERSATION_HISTORY[user_id]))

    # Fire-and-forget SQLite persistence
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_persist_turn_to_db(user_id, role, content, ts))
    except Exception:
        pass

    # Fire-and-forget OpenViking L1 persistence
    if role == "assistant":
        user_turns = CONVERSATION_HISTORY[user_id]
        last_user_msg = ""
        for t in reversed(user_turns):
            if t["role"] == "user":
                last_user_msg = t["content"]
                break
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_persist_to_viking(user_id, last_user_msg, content))
        except Exception:
            pass


async def _persist_to_viking(user_id: str, user_msg: str, assistant_msg: str) -> None:
    """Async helper: persist conversation turn to OpenViking L1."""
    try:
        from tools.viking_context import save_interaction_to_l1
        await save_interaction_to_l1(user_id, user_msg, assistant_msg)
    except Exception as e:
        logger.debug("Viking L1 persist skipped (non-fatal): %s", e)


def clear_conversation(user_id: str) -> None:
    """Wipe conversation history for a user (fresh start)."""
    if user_id in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[user_id]
        logger.info("Cleared conversation history for %s", user_id)
    _conv_db_loaded_users.discard(user_id)


def get_conversation_summary_prompt(user_id: str) -> str:
    """
    Build a compact context block to prepend to the system prompt.

    Strategy:
      1. Try to get a tiered context block from OpenViking (L0+L1+L2)
         via asyncio — works if called from an async context
      2. Fall back to the RAM CONVERSATION_HISTORY dict for hot path
    """
    # ── Try OpenViking async (schedule as task, use RAM for THIS request) ─
    # OpenViking context will be available on the NEXT request after the
    # first save — this is intentional (async fire-and-forget pattern).
    # For immediate continuity, the RAM dict is always used.
    history = get_conversation_history(user_id, last_n=6)
    if not history:
        return ""
    lines = ["[CONVERSATION CONTEXT — last exchanges:]", ""]
    for turn in history:
        role_label = "Bashara" if turn["role"] == "user" else "Legion"
        snippet = turn["content"][:300].replace("\n", " ")
        if len(turn["content"]) > 300:
            snippet += "..."
        lines.append(f"{role_label}: {snippet}")
    lines.append("[end context]")
    return "\n".join(lines)


def detect_agent(task: str) -> str:
    task_lower = task.lower().strip()

    # High-confidence intent overrides to reduce keyword collision noise.
    if re.search(r"\b(gradient|derivative|integral|matrix|determinant|eigenvalue|tensor|backprop|softmax)\b", task_lower):
        return "math"
    if re.search(r"\b(traceback|exception|stack trace|bug|debug|not working|error)\b", task_lower):
        return "debug"
    if re.search(r"\b(architecture|system design|microservice|structure|structur|framework diagram|blueprint)\b", task_lower):
        return "architect"
    if re.search(r"\b(capital of|tell me a joke|joke)\b", task_lower):
        return "general"

    scores: dict[str, int] = {agent: 0 for agent in TASK_KEYWORDS}
    for agent, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            kw_norm = kw.strip().lower()
            if not kw_norm:
                continue
            if re.search(r"[a-z0-9]", kw_norm):
                pattern = rf"(?<![a-z0-9]){re.escape(kw_norm)}(?![a-z0-9])"
                if re.search(pattern, task_lower):
                    scores[agent] += 1
            elif kw_norm in task_lower:
                scores[agent] += 1

    # Tie-break preference keeps generic PM/ops keywords from stealing
    # clearly technical tasks when scores are equal.
    tie_break_order = [
        "debug", "math", "vision", "coding", "architect",
        "analyst", "researcher", "devops", "pm", "reviewer", "general",
    ]
    best_agent = max(scores, key=lambda a: scores[a])
    best_score = scores[best_agent]
    if best_score > 0:
        for candidate in tie_break_order:
            if scores.get(candidate, 0) == best_score:
                best_agent = candidate
                break
    if best_score == 0:
        logger.debug("No keyword match — using %s", DEFAULT_AGENT)
        return DEFAULT_AGENT
    logger.debug("Detected agent '%s' (score=%d)", best_agent, best_score)
    return best_agent


def get_model(agent_key: str, use_fallback: bool = False) -> str | None:
    if use_fallback:
        chain = FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])
        return chain[0]
    return AGENT_MODELS.get(agent_key)


def get_fallback_chain(agent_key: str) -> list[str]:
    return FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])


def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
    parts = [PERSONALITY_WRAPPER.strip()]
    if user_id:
        ctx = get_conversation_summary_prompt(user_id)
        if ctx:
            parts.append(ctx)
    parts.append(role_prompt)
    return "\n\n".join(parts)


def list_agents() -> str:
    lines = ["<b>\U0001f916 Active Agents</b>\n"]
    icons = {
        "vision": "\U0001f441\ufe0f",
        "coding": "\U0001f4bb",
        "debug": "\U0001f41b",
        "math": "\U0001f4d0",
        "architect": "\U0001f3d7\ufe0f",
        "analyst": "\U0001f4ca",
        "computer": "\U0001f5a5\ufe0f",
        "general": "\U0001f9e0",
        "researcher": "\U0001f52c",
        "marketer": "\U0001f4e2",
        "devops": "\U0001f527",
        "pm": "\U0001f4cb",
        "humanizer": "\u2728",
        "reviewer": "\U0001f50d",
        "think": "\U0001f9e0",   # 🧠 deep reasoning mode
        "owl": "🦉",
        "ag2_researcher": "🧪",
        "ag2_critic": "🛡️",
        "ag2_synthesizer": "🧩",
        "code_exec": "⚙️",
        "predictor": "🔮",
        "claude_orchestrator": "🧭",
    }
    for key, model in AGENT_MODELS.items():
        icon = icons.get(key, "\U0001f916")
        if model.startswith("ollama_chat/"):
            provider = "OLLAMA"
            model_name = model.replace("ollama_chat/", "") + " (local \U0001f512)"
        else:
            parts = model.split("/")
            provider = parts[0].upper()
            model_name = "/".join(parts[1:])
        lines.append(f"  {icon} <b>{key}</b> \u2192 <code>{provider}</code> <i>{model_name}</i>")
    lines.append("\n  \U0001f512 <i>vision = local Ollama, stays on your machine</i>")
    return "\n".join(lines)


def list_all_departments() -> list[str]:
    return list(AGENT_MODELS.keys())


def add_to_thread(thread_id: str, agent: str, task: str, result: str) -> None:
    if thread_id not in ACTIVE_THREADS:
        ACTIVE_THREADS[thread_id] = []
    ACTIVE_THREADS[thread_id].append({
        "agent": agent,
        "task": task,
        "result": result[:500],
        "timestamp": time.time(),
    })
    if len(ACTIVE_THREADS[thread_id]) > 10:
        ACTIVE_THREADS[thread_id] = ACTIVE_THREADS[thread_id][-10:]


def get_thread_context(thread_id: str, last_n: int = 3) -> str:
    if thread_id not in ACTIVE_THREADS or not ACTIVE_THREADS[thread_id]:
        return ""
    recent = ACTIVE_THREADS[thread_id][-last_n:]
    lines = ["<i>Previous in this thread:</i>\n"]
    for turn in recent:
        t = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        lines.append(f"[{t}] {turn['agent'].upper()}: {turn['task'][:80]}\u2026")
        lines.append(f"\u21b3 {turn['result'][:120]}\u2026\n")
    return "\n".join(lines)


def list_threads() -> str:
    if not ACTIVE_THREADS:
        return "<b>No active threads</b>\n\nUse <code>/thread &lt;name&gt;</code> to start one."
    lines = ["<b>\U0001f4cc Active Threads</b>\n"]
    for tid, turns in ACTIVE_THREADS.items():
        last = turns[-1]
        t = datetime.fromtimestamp(last["timestamp"]).strftime("%m/%d %H:%M")
        lines.append(f"  \U0001f4cc <b>{tid}</b> \u2014 {len(turns)} turns (last: {t})")
    return "\n".join(lines)


def list_threads_raw() -> list[str]:
    return list(ACTIVE_THREADS.keys())


def clear_thread(thread_id: str) -> bool:
    if thread_id in ACTIVE_THREADS:
        del ACTIVE_THREADS[thread_id]
        return True
    return False
