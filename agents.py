"""Agent router: cloud-only model registry with smart keyword routing.

Priority fallback chain (all free tiers):
  1. Cerebras  — fastest inference (~1,500 tok/s)
  2. Groq      — fast (~241 tok/s)
  3. Gemini    — large context (1M tokens)
  4. OpenRouter — model variety fallback
  NO Ollama fallback — cloud APIs only.
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

DEBATE_ICONS = {
    "strategist": "⚔️",
    "devil_advocate": "🔥",
    "researcher": "📚",
    "pragmatist": "🔧",
    "visionary": "🚀",
    "critic": "✂️",
}

# ── Primary model registry ──────────────────────────────────────────────────
AGENT_MODELS: dict[str, str] = {
    "vision":     "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "coding":     "cerebras/qwen-3-235b",
    "debug":      "groq/qwen-qwq-32b",
    "math":       "cerebras/qwen-3-235b",
    "architect":  "gemini/gemini-2.0-flash",
    "analyst":    "groq/moonshotai/kimi-k2-instruct",
    "general":    "cerebras/qwen-3-235b",
    "research":   "gemini/gemini-2.0-flash",
    "humanizer":  "groq/llama-3.3-70b-versatile",
}

# ── Fallback chain per agent ────────────────────────────────────────────────
FALLBACK_MODELS: dict[str, str] = {
    "vision":     "gemini/gemini-2.0-flash",
    "coding":     "openrouter/qwen/qwen3-coder:free",
    "debug":      "groq/llama-3.3-70b-versatile",
    "math":       "groq/qwen-qwq-32b",
    "architect":  "cerebras/qwen-3-235b",
    "analyst":    "gemini/gemini-2.0-flash",
    "general":    "groq/llama-3.3-70b-versatile",
    "research":   "cerebras/qwen-3-235b",
    "humanizer":  "gemini/gemini-2.0-flash",
}

FALLBACK_CHAIN: dict[str, list[str]] = {
    "vision": [
        "groq/meta-llama/llama-4-scout-17b-16e-instruct",
        "gemini/gemini-2.0-flash",
        "openrouter/google/gemini-2.0-flash-exp:free",
    ],
    "coding": [
        "cerebras/qwen-3-235b",
        "groq/qwen-qwq-32b",
        "openrouter/qwen/qwen3-coder:free",
        "openrouter/openai/gpt-4o-mini:free",
    ],
    "debug": [
        "groq/qwen-qwq-32b",
        "groq/llama-3.3-70b-versatile",
        "cerebras/qwen-3-235b",
        "openrouter/deepseek/deepseek-r1:free",
    ],
    "math": [
        "cerebras/qwen-3-235b",
        "groq/qwen-qwq-32b",
        "openrouter/deepseek/deepseek-r1:free",
    ],
    "architect": [
        "gemini/gemini-2.0-flash",
        "cerebras/qwen-3-235b",
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    ],
    "analyst": [
        "groq/moonshotai/kimi-k2-instruct",
        "gemini/gemini-2.0-flash",
        "cerebras/qwen-3-235b",
    ],
    "general": [
        "cerebras/qwen-3-235b",
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        "openrouter/google/gemini-flash-1.5:free",
    ],
    "research": [
        "gemini/gemini-2.0-flash",
        "cerebras/qwen-3-235b",
        "groq/llama-3.3-70b-versatile",
        "openrouter/google/gemini-flash-1.5:free",
    ],
    "humanizer": [
        "groq/llama-3.3-70b-versatile",
        "gemini/gemini-2.0-flash",
        "cerebras/qwen-3-235b",
    ],
}

# ── Keyword → agent routing ─────────────────────────────────────────────────
TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot", "image", "photo", "ui", "visual", "ocr",
        "screen", "what's on", "desktop", "window", "look at",
        "describe", "read screen", "see", "what do you see",
    ],
    "coding": [
        "code", "function", "script", "implement", "class", "module",
        "refactor", "generate", "syntax", "endpoint", "sql", "query",
        "write code", "build", "create file", "add feature", "api",
        "python", "bash", "shell", "command",
    ],
    "debug": [
        "debug", "traceback", "exception", "crash", "fix", "bug",
        "cuda", "pytorch", "torch", "nan", "oom", "out of memory",
        "backward", "loss spike", "error", "why is", "not working",
    ],
    "math": [
        "tensor", "matrix", "equation", "derivative", "integral",
        "gradient", "backprop", "linear algebra", "eigenvalue",
        "softmax", "norm", "convolution", "calculate", "math",
        "formula", "proof", "solve",
    ],
    "architect": [
        "design", "architecture", "plan", "system", "pipeline",
        "structure", "strategy", "high level", "document", "thesis",
        "overview", "framework", "organize", "diagram",
    ],
    "analyst": [
        "analyze", "plot", "chart", "csv", "dataframe", "log",
        "trend", "statistics", "distribution", "compare",
        "metrics", "performance", "insight", "nvidia-smi",
        "visualize", "summarize data", "gpu", "training",
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
    if use_fallback:
        return FALLBACK_MODELS.get(agent_key)
    return AGENT_MODELS.get(agent_key)


def get_fallback_chain(agent_key: str) -> list[str]:
    return FALLBACK_CHAIN.get(agent_key, FALLBACK_CHAIN["general"])


def build_system_prompt(role_prompt: str) -> str:
    """Prepend the personality wrapper to any agent system prompt."""
    return PERSONALITY_WRAPPER.strip() + "\n\n" + role_prompt


def list_agents() -> str:
    lines = ["<b>🤖 Active Agents — Cloud Only</b>\n"]
    icons = {
        "vision": "👁️", "coding": "💻", "debug": "🐛",
        "math": "📐", "architect": "🏗️", "analyst": "📊",
        "general": "🧠", "research": "🔍", "humanizer": "✨",
    }
    for key, model in AGENT_MODELS.items():
        icon = icons.get(key, "🤖")
        provider = model.split("/")[0].upper()
        model_name = "/".join(model.split("/")[1:])
        lines.append(f"  {icon} <b>{key}</b> → <code>{provider}</code> <i>{model_name}</i>")
    return "\n".join(lines)


def list_all_departments() -> list[str]:
    """Compatibility shim for old code that calls agents.list_all_departments()."""
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
    lines = ["Previous conversation in this thread:\n"]
    for turn in recent:
        t = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        lines.append(f"[{t}] {turn['agent'].upper()}: {turn['task'][:100]}...")
        lines.append(f"Response: {turn['result']}\n")
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
