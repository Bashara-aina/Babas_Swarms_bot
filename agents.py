"""Agent registry, debate personas, and thread memory.

Single source of truth for:
  - AGENT_MODELS       : primary model per agent role
  - FALLBACK_CHAIN     : ordered fallback list per agent role
  - TASK_KEYWORDS      : keyword→agent routing (includes Indonesian)
  - DEBATE_PERSONAS    : 6 debate roles for SwarmDebateOrchestrator
  - ACTIVE_THREADS     : in-memory thread store

Ollama is ONLY used for vision (local, private, RTX 3060).
Never used as a text fallback.

Verified working models (live logs 2026-03-09):
  groq/llama-3.3-70b-versatile                   ✓
  groq/meta-llama/llama-4-scout-17b-16e-instruct ✓
  cerebras/qwen-3-235b-a22b                       ✓
  zai/glm-4                                       ✓
"""

from __future__ import annotations
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Personality wrapper injected into EVERY agent system prompt ──────────────
PERSONALITY_WRAPPER = """
You are a brilliant, opinionated expert. You think out loud, use vivid examples,
and speak like a sharp colleague over coffee — not a documentation page. Rules:
- Use em-dashes, ellipses, contractions naturally
- Open with your honest take, not a summary
- Use analogies when explaining complex ideas
- Disagree with conventional wisdom when you have good reason
- Never use bullet-point walls for conversational answers
- End with a question or a "the real insight here is..." observation
- Match the user's language: if they write in Indonesian, respond in Indonesian
  with the same casual/formal register
- Use Telegram markdown: **bold** for emphasis, `code` for technical terms,
  and 💡 🔥 ⚡ sparingly for genuine highlights
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

# Persona → preferred model (different reasoning styles need different models)
DEBATE_PERSONA_MODELS: dict[str, str] = {
    "strategist":     "cerebras/qwen-3-235b-a22b",           # fast, large context
    "devil_advocate": "groq/qwen-qwq-32b",                   # adversarial reasoning
    "researcher":     "groq/moonshotai/kimi-k2-instruct",    # deep research
    "pragmatist":     "groq/llama-3.3-70b-versatile",        # practical, fast
    "visionary":      "cerebras/qwen-3-235b-a22b",           # creative, fast
    "critic":         "zai/glm-4",                           # precise, analytical
}

DEBATE_ICONS = {
    "strategist": "⚔️",
    "devil_advocate": "🔥",
    "researcher": "📚",
    "pragmatist": "🔧",
    "visionary": "🚀",
    "critic": "✂️",
}

# ── Primary model registry ──────────────────────────────────────────────────
# SINGLE source of truth — router.py imports from here.
AGENT_MODELS: dict[str, str] = {
    "vision":     "ollama_chat/gemma3:12b",              # local, private, RTX 3060
    "coding":     "groq/llama-3.3-70b-versatile",        # fast + reliable
    "debug":      "zai/glm-4",                           # GPQA Diamond 85.7%
    "math":       "zai/glm-4",                           # AIME 2025 95.7%
    "architect":  "cerebras/qwen-3-235b-a22b",           # 1500 tok/s, 131K ctx
    "analyst":    "groq/moonshotai/kimi-k2-instruct",    # 1T MoE, deep reasoning
    "computer":   "groq/llama-3.3-70b-versatile",        # agentic tool-calling loop
    "general":    "groq/llama-3.3-70b-versatile",        # reliable default
    "researcher": "groq/moonshotai/kimi-k2-instruct",    # academic research
    "marketer":   "groq/llama-3.3-70b-versatile",        # content + social
    "devops":     "groq/llama-3.3-70b-versatile",        # infra + deployment
    "pm":         "cerebras/qwen-3-235b-a22b",           # project management
    "humanizer":  "groq/llama-3.3-70b-versatile",        # humanising AI text
    "reviewer":   "groq/llama-3.3-70b-versatile",        # AI code review
}

# ── Fallback chains (NO Ollama outside vision) ──────────────────────────────
FALLBACK_CHAIN: dict[str, list[str]] = {
    "vision": [
        "ollama_chat/gemma3:12b",
        "groq/meta-llama/llama-4-scout-17b-16e-instruct",
        "gemini/gemini-2.0-flash",
    ],
    "coding": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen-3-235b-a22b",
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
        "cerebras/qwen-3-235b-a22b",
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
        "cerebras/qwen-3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
    "general": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen-3-235b-a22b",
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
        "cerebras/qwen-3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
    "devops": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen-3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
    "pm": [
        "cerebras/qwen-3-235b-a22b",
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
    ],
    "humanizer": [
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
        "cerebras/qwen-3-235b-a22b",
    ],
    "reviewer": [
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen-3-235b-a22b",
        "gemini/gemini-2.0-flash",
    ],
}

# ── Keyword → agent routing ─────────────────────────────────────────────────
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

# ── Thread memory ───────────────────────────────────────────────────────────
ACTIVE_THREADS: dict[str, list[dict]] = {}


def detect_agent(task: str) -> str:
    task_lower = task.lower()
    scores: dict[str, int] = {agent: 0 for agent in TASK_KEYWORDS}
    for agent, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            if kw in task_lower:
                scores[agent] += 1
    best_agent = max(scores, key=lambda a: scores[a])
    if scores[best_agent] == 0:
        logger.debug("No keyword match — using %s", DEFAULT_AGENT)
        return DEFAULT_AGENT
    logger.debug("Detected agent '%s' (score=%d)", best_agent, scores[best_agent])
    return best_agent


def get_model(agent_key: str, use_fallback: bool = False) -> str | None:
    """Return primary or first-fallback model for an agent key."""
    if use_fallback:
        chain = FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])
        logger.debug("Fallback model for '%s': %s", agent_key, chain[0])
        return chain[0]
    return AGENT_MODELS.get(agent_key)


def get_fallback_chain(agent_key: str) -> list[str]:
    """Return full fallback chain for waterfall retry logic."""
    return FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])


def build_system_prompt(role_prompt: str) -> str:
    """Prepend the personality wrapper to any agent system prompt."""
    return PERSONALITY_WRAPPER.strip() + "\n\n" + role_prompt


def list_agents() -> str:
    lines = ["<b>🤖 Active Agents</b>\n"]
    icons = {
        "vision": "👁️", "coding": "💻", "debug": "🐛",
        "math": "📐", "architect": "🏗️", "analyst": "📊",
        "computer": "🖥️", "general": "🧠", "researcher": "🔬",
        "marketer": "📢", "devops": "🔧", "pm": "📋",
        "humanizer": "✨",
    }
    for key, model in AGENT_MODELS.items():
        icon = icons.get(key, "🤖")
        if model.startswith("ollama_chat/"):
            provider = "OLLAMA"
            model_name = model.replace("ollama_chat/", "") + " (local 🔒)"
        else:
            parts = model.split("/")
            provider = parts[0].upper()
            model_name = "/".join(parts[1:])
        lines.append(f"  {icon} <b>{key}</b> → <code>{provider}</code> <i>{model_name}</i>")
    lines.append("\n  🔒 <i>vision = local Ollama, stays on your machine</i>")
    return "\n".join(lines)


def list_all_departments() -> list[str]:
    """Return all agent role names."""
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
    logger.info("Added to thread '%s': %s agent", thread_id, agent)


def get_thread_context(thread_id: str, last_n: int = 3) -> str:
    if thread_id not in ACTIVE_THREADS or not ACTIVE_THREADS[thread_id]:
        return ""
    recent = ACTIVE_THREADS[thread_id][-last_n:]
    lines = ["<i>Previous in this thread:</i>\n"]
    for turn in recent:
        t = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        lines.append(f"[{t}] {turn['agent'].upper()}: {turn['task'][:80]}…")
        lines.append(f"↳ {turn['result'][:120]}…\n")
    return "\n".join(lines)


def list_threads() -> str:
    if not ACTIVE_THREADS:
        return "<b>No active threads</b>\n\nUse <code>/thread &lt;name&gt;</code> to start one."
    lines = ["<b>📌 Active Threads</b>\n"]
    for tid, turns in ACTIVE_THREADS.items():
        last = turns[-1]
        t = datetime.fromtimestamp(last["timestamp"]).strftime("%m/%d %H:%M")
        lines.append(f"  📌 <b>{tid}</b> — {len(turns)} turns (last: {t})")
    return "\n".join(lines)


def list_threads_raw() -> list[str]:
    return list(ACTIVE_THREADS.keys())


def clear_thread(thread_id: str) -> bool:
    if thread_id in ACTIVE_THREADS:
        del ACTIVE_THREADS[thread_id]
        logger.info("Cleared thread '%s'", thread_id)
        return True
    return False
