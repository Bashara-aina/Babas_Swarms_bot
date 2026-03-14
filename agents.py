"""Agent registry, debate personas, and thread memory.

Single source of truth for:
  - AGENT_MODELS       : primary model per agent role
  - FALLBACK_CHAIN     : ordered fallback list per agent role
  - TASK_KEYWORDS      : keyword→agent routing (includes Indonesian)
  - DEBATE_PERSONAS    : 6 debate roles for SwarmDebateOrchestrator
  - ACTIVE_THREADS     : in-memory thread store
  - CONVERSATION_HISTORY: persistent per-user conversation context

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

# ── Personality wrapper injected into EVERY agent system prompt ──────────────────
# Goal: sound like a brilliant, warm friend — not a documentation page or a robot
PERSONALITY_WRAPPER = """
You are Legion — Bashara's personal AI, running right here on her Linux machine.
Think of yourself as her smartest friend who also happens to be an expert in
whatever she needs: code, research, design, life advice, math, or just vibing.

TONE & VOICE RULES (critical):
- Talk like a real friend. Use casual language, contractions, even humor when appropriate.
- Open with your honest opinion first — never start with a hollow affirmation
  like "Great question!" or "Of course!" Just... answer.
- If something is obvious, say so gently: "Honestly this is pretty straightforward —"
- If something is hard, acknowledge it: "Okay this one's actually tricky..."
- Use first person freely: "I think", "I'd go with", "My gut says"
- Match Bashara's energy. If she's excited, be excited. If she's stressed, be calm.
- Mix in light banter naturally: "wait, actually that's cleaner than I expected 😄"
- When you finish a complex task, feel free to add a brief human observation:
  "By the way, the reason this pattern trips people up is..."
- NEVER use bullet-point walls for conversational replies. Bullets are only for
  lists of 4+ items that genuinely benefit from enumeration.
- Use em-dashes — for asides — and ellipses when thinking out loud...
- End responses with something that invites dialogue: a follow-up question,
  a caveat to explore, or a "the thing I'd actually watch out for here is..."

LANGUAGE RULES:
- If Bashara writes in Indonesian, reply in Indonesian — same casual/formal register.
  Bahasa sehari-hari kalau dia santai, lebih formal kalau dia serius.
- If she mixes Indonesian + English (code-switching), do the same naturally.
- Never force English if the conversation is flowing in Indonesian.

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
- Keep responses tight. No padding. No re-summarizing what she just said.

MEMORY CONTEXT (when provided):
- If a [MEMORY CONTEXT] block is provided at the start of the message,
  treat it as real prior knowledge about Bashara and her projects.
  Reference it naturally: "since you're using Supabase for this..."
  Don't announce you're using memory — just use it.
"""

# ── Debate personas for SwarmDebateOrchestrator ──────────────────────────────────
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
# FIX #17: Added fallback-aware note — if persona model fails, FALLBACK_CHAIN[role] is used
DEBATE_PERSONA_MODELS: dict[str, str] = {
    "strategist":     "cerebras/qwen-3-235b-a22b",           # fast, large context
    "devil_advocate": "groq/qwen-qwq-32b",                   # adversarial reasoning
    "researcher":     "groq/moonshotai/kimi-k2-instruct",    # deep research
    "pragmatist":     "groq/llama-3.3-70b-versatile",        # practical, fast
    "visionary":      "cerebras/qwen-3-235b-a22b",           # creative, fast
    "critic":         "zai/glm-4",                           # precise, analytical
}

DEBATE_PERSONA_FALLBACKS: dict[str, list[str]] = {
    "strategist":     ["cerebras/qwen-3-235b-a22b", "groq/llama-3.3-70b-versatile", "gemini/gemini-2.0-flash"],
    "devil_advocate": ["groq/qwen-qwq-32b", "groq/llama-3.3-70b-versatile", "gemini/gemini-2.0-flash"],
    "researcher":     ["groq/moonshotai/kimi-k2-instruct", "zai/glm-4", "groq/llama-3.3-70b-versatile"],
    "pragmatist":     ["groq/llama-3.3-70b-versatile", "cerebras/qwen-3-235b-a22b", "gemini/gemini-2.0-flash"],
    "visionary":      ["cerebras/qwen-3-235b-a22b", "groq/llama-3.3-70b-versatile", "gemini/gemini-2.0-flash"],
    "critic":         ["zai/glm-4", "groq/llama-3.3-70b-versatile", "gemini/gemini-2.0-flash"],
}

DEBATE_ICONS = {
    "strategist": "⚔️",
    "devil_advocate": "🔥",
    "researcher": "📚",
    "pragmatist": "🔧",
    "visionary": "🚀",
    "critic": "✂️",
}

# ── Primary model registry ────────────────────────────────────────────────────────────
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

# ── Fallback chains (NO Ollama outside vision) ──────────────────────────────────
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

# ── Keyword → agent routing ───────────────────────────────────────────────────────────────
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

# ── Thread memory (in-RAM, per-session) ─────────────────────────────────────────────
ACTIVE_THREADS: dict[str, list[dict]] = {}

# ── Conversation history (persistent per user_id, for long-context) ────────────────
# Format: {user_id: [{"role": "user"|"assistant", "content": str, "ts": float}]}
CONVERSATION_HISTORY: dict[str, list[dict]] = {}
MAX_HISTORY_TURNS = 20   # keep last 20 exchanges in RAM
MAX_HISTORY_CHARS = 8000  # cap injected history at ~8K chars to stay within context


def get_conversation_history(user_id: str, last_n: int = MAX_HISTORY_TURNS) -> list[dict]:
    """Return recent conversation history as litellm-compatible messages."""
    if user_id not in CONVERSATION_HISTORY:
        return []
    turns = CONVERSATION_HISTORY[user_id][-last_n:]
    return [{"role": t["role"], "content": t["content"]} for t in turns]


def add_to_conversation(user_id: str, role: str, content: str) -> None:
    """Append a turn to conversation history. Trims to MAX_HISTORY_TURNS pairs."""
    if user_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[user_id] = []
    CONVERSATION_HISTORY[user_id].append({
        "role": role,
        "content": content,
        "ts": time.time(),
    })
    # FIX #12: Keep last MAX_HISTORY_TURNS * 2 entries (each "turn" = 1 user + 1 assistant message)
    if len(CONVERSATION_HISTORY[user_id]) > MAX_HISTORY_TURNS * 2:
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY[user_id][-(MAX_HISTORY_TURNS * 2):]
    logger.debug("Conversation history for %s: %d entries", user_id, len(CONVERSATION_HISTORY[user_id]))


def clear_conversation(user_id: str) -> None:
    """Wipe conversation history for a user (fresh start)."""
    if user_id in CONVERSATION_HISTORY:
        del CONVERSATION_HISTORY[user_id]
        logger.info("Cleared conversation history for %s", user_id)


def get_conversation_summary_prompt(user_id: str) -> str:
    """
    Build a compact context block to prepend to the system prompt,
    summarizing the last few exchanges so the LLM has continuity.
    """
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


def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
    """
    Prepend the personality wrapper + optional conversation context
    to any agent system prompt.
    """
    parts = [PERSONALITY_WRAPPER.strip()]
    if user_id:
        ctx = get_conversation_summary_prompt(user_id)
        if ctx:
            parts.append(ctx)
    parts.append(role_prompt)
    return "\n\n".join(parts)


def list_agents() -> str:
    lines = ["<b>🤖 Active Agents</b>\n"]
    # FIX #4: Added 'reviewer' icon so all AGENT_MODELS keys have a matching icon
    icons = {
        "vision": "👁️", "coding": "💻", "debug": "🐛",
        "math": "📐", "architect": "🏗️", "analyst": "📊",
        "computer": "🖥️", "general": "🧠", "researcher": "🔬",
        "marketer": "📢", "devops": "🔧", "pm": "📋",
        "humanizer": "✨", "reviewer": "🔍",
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


# ── Thread memory (in-RAM, used by /thread command) ────────────────────────────
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
