"""Agent router — cloud-first, Ollama only where it specialises.

Ollama is ONLY used for vision/screenshot analysis (gemma3:12b, local + private).
It is NEVER a fallback for text agents.

Verified working models (from live logs 2026-03-09):
  groq/llama-3.3-70b-versatile                   ✓
  groq/meta-llama/llama-4-scout-17b-16e-instruct ✓
  cerebras/qwen-3-235b-a22b                       ✓ (was wrong: qwen-3-235b)
  zai/glm-4                                       ✓ (via openai-compat endpoint)
"""

from __future__ import annotations
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Primary models ──────────────────────────────────────────────────────────
# Ollama ONLY for vision — its specialisation is local screenshot analysis.
AGENT_MODELS: dict[str, str] = {
    "vision":    "ollama_chat/gemma3:12b",              # local, private, RTX 3060
    "coding":    "groq/llama-3.3-70b-versatile",        # fast + reliable ✓
    "debug":     "zai/glm-4",                           # GPQA Diamond 85.7%
    "math":      "zai/glm-4",                           # AIME 2025 95.7%
    "architect": "cerebras/qwen-3-235b-a22b",           # 1500 tok/s, 131K ctx
    "analyst":   "groq/moonshotai/kimi-k2-instruct",    # 1T MoE, deep reasoning
    "computer":  "groq/llama-3.3-70b-versatile",        # agentic tool-calling loop
    "general":   "groq/llama-3.3-70b-versatile",        # reliable default ✓
}

# ── Fallback chains (NO Ollama outside vision) ──────────────────────────────
FALLBACK_CHAIN: dict[str, list[str]] = {
    "vision": [
        "ollama_chat/gemma3:12b",                          # local first (private)
        "groq/meta-llama/llama-4-scout-17b-16e-instruct",  # cloud fallback
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
}

# ── Keyword routing ─────────────────────────────────────────────────────────
TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot", "screen", "layar", "gambar", "image", "photo",
        "ocr", "visual", "desktop", "window", "what do you see",
        "lihat", "tampilan", "apa yang ada di", "capture",
    ],
    "coding": [
        "code", "kode", "function", "script", "implement", "class",
        "refactor", "generate", "sql", "endpoint", "api", "python",
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
        # Web browsing & research
        "browse", "search for", "research", "find online", "look up",
        "scrape", "website", "web page", "cari di internet", "booking",
        "google", "search the web",
        # Documents
        "pdf", "excel", "spreadsheet", "ocr", "word doc", "docx",
        "extract table", "read document", "baca dokumen",
        # Email
        "email", "inbox", "send email", "kirim email", "mail",
        "reply email", "check email", "cek email",
        # Git
        "git status", "git commit", "git push", "git pull", "git diff",
        "git stash", "commit", "push to", "pull from",
        # Dev tools
        "run tests", "pytest", "lint", "ruff", "format code",
        "find in code", "grep", "codebase", "db query", "sql",
        # System / scheduling
        "monitor", "schedule", "disk space", "memory usage",
        "maintenance", "cleanup", "services", "system check",
        # File management
        "organize files", "find files", "sort files",
    ],
}

DEFAULT_AGENT = "general"
ACTIVE_THREADS: dict[str, list[dict]] = {}


def detect_agent(task: str) -> str:
    task_lower = task.lower()
    scores: dict[str, int] = {agent: 0 for agent in TASK_KEYWORDS}
    for agent, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            if kw in task_lower:
                scores[agent] += 1
    best = max(scores, key=lambda a: scores[a])
    if scores[best] == 0:
        return DEFAULT_AGENT
    return best


def get_model(agent_key: str, use_fallback: bool = False) -> str | None:
    return AGENT_MODELS.get(agent_key)


def get_fallback_chain(agent_key: str) -> list[str]:
    return FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])


def list_agents() -> str:
    icons = {
        "vision": "👁️", "coding": "💻", "debug": "🐛",
        "math": "📐", "architect": "🏗️", "analyst": "📊",
        "computer": "🖥️", "general": "🧠",
    }
    lines = ["<b>🤖 Legion Agent Roster</b>\n"]
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
    return list(AGENT_MODELS.keys())


def add_to_thread(thread_id: str, agent: str, task: str, result: str) -> None:
    if thread_id not in ACTIVE_THREADS:
        ACTIVE_THREADS[thread_id] = []
    ACTIVE_THREADS[thread_id].append({
        "agent": agent, "task": task,
        "result": result[:500], "timestamp": time.time(),
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
        lines.append(f"[{t}] {turn['agent'].upper()}: {turn['task'][:80]}…")
        lines.append(f"↳ {turn['result'][:120]}…\n")
    return "\n".join(lines)


def list_threads() -> str:
    if not ACTIVE_THREADS:
        return "No active threads yet. Start one with <code>/thread &lt;name&gt;</code>."
    lines = ["<b>📌 Threads</b>\n"]
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
        return True
    return False
