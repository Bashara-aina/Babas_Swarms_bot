# /home/newadmin/swarm-bot/agents.py
"""Agent router: keyword-based task detection and model registry."""

from __future__ import annotations
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Primary model registry - Best in class as of March 2026
AGENT_MODELS: dict[str, str] = {
    "vision":    "ollama_chat/gemma3:12b",                        # Local - privacy critical
    "coding":    "openrouter/mistralai/devstral-2512:free",      # SWE-bench 72.2%
    "debug":     "zai/glm-4",                                     # GPQA Diamond 85.7%
    "math":      "zai/glm-4",                                     # AIME 2025 95.7%
    "architect": "cerebras/qwen3-235b-a22b",                      # 1,500 tok/s, 131K context
    "mentor":    "gemini/gemini-3.1-pro",                         # 1M context, Gemini Pro sub
    "analyst":   "groq/moonshotai/kimi-k2-instruct",             # 1T MoE, deep reasoning
}

# Fallback models when primary hits rate limit
FALLBACK_MODELS: dict[str, str] = {
    "coding":    "openrouter/qwen/qwen3-coder:free",
    "debug":     "cerebras/qwen3-235b-a22b",
    "math":      "cerebras/qwen3-235b-a22b",
    "architect": "openrouter/openai/gpt-oss-120b:free",
    "mentor":    "gemini/gemma-3-27b-it",
    "analyst":   "openrouter/openai/gpt-oss-120b:free",
}

# Keyword → agent mapping (auto-routing via /run command)
TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot", "image", "photo", "ui", "visual", "ocr", 
        "pixel", "multimodal", "look at", "describe"
    ],
    "coding": [
        "code", "function", "script", "implement", "class", "module", 
        "refactor", "generate", "syntax", "endpoint", "sql", "query",
        "write code", "build", "create file", "add feature", "api"
    ],
    "debug": [
        "debug", "traceback", "exception", "crash", "fix", "bug", 
        "cuda", "pytorch", "torch", "workernet", "nan", "oom", 
        "out of memory", "backward", "loss spike", "error in"
    ],
    "math": [
        "tensor", "matrix", "equation", "derivative", "integral", 
        "gradient descent", "backprop", "linear algebra", "eigenvalue", 
        "softmax", "norm", "convolution", "fourier", "calculate",
        "mathematical", "formula", "proof"
    ],
    "architect": [
        "design", "architecture", "plan", "system", "pipeline", 
        "structure", "strategy", "high level", "document", "thesis",
        "overview", "framework", "organize"
    ],
    "mentor": [
        "explain", "teach me", "i don't understand", "eli5", 
        "what does this mean", "walk me through", "what is", 
        "how does", "why does", "in simple terms", "beginner", 
        "step by step", "like a professor", "break it down"
    ],
    "analyst": [
        "analyze", "plot", "chart", "csv", "dataframe", "log",
        "trend", "statistics", "distribution", "compare results",
        "training run", "metrics", "performance", "insight",
        "nvidia-smi", "visualize", "summarize data"
    ],
    "vision": [
        "screenshot", "image", "photo", "ui", "visual", "ocr",
        "pixel", "multimodal", "look at", "describe", "screen",
        "what's on", "what is on", "desktop", "window", "read screen",
        "find element", "click on", "click the", "what do you see"
    ],
}

# Default fallback agent when no keyword matches
DEFAULT_AGENT = "coding"

# Thread-based conversation memory
ACTIVE_THREADS: dict[str, list[dict]] = {}


def detect_agent(task: str) -> str:
    """Return the best agent key for a given task string.

    Matches by counting keyword hits per agent; highest score wins.
    Falls back to DEFAULT_AGENT when no keywords match.

    Args:
        task: Raw task string from the user.

    Returns:
        Agent key (e.g. "coding", "debug").
    """
    task_lower = task.lower()
    scores: dict[str, int] = {agent: 0 for agent in TASK_KEYWORDS}

    for agent, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            if kw in task_lower:
                scores[agent] += 1

    best_agent = max(scores, key=lambda a: scores[a])
    if scores[best_agent] == 0:
        logger.debug("No keyword match — falling back to %s", DEFAULT_AGENT)
        return DEFAULT_AGENT

    logger.debug("Detected agent '%s' (score=%d)", best_agent, scores[best_agent])
    return best_agent


def get_model(agent_key: str, use_fallback: bool = False) -> str | None:
    """Return the model string for an agent key.
    
    Args:
        agent_key: One of the keys in AGENT_MODELS.
        use_fallback: If True, return fallback model instead of primary.

    Returns:
        Full model string (e.g. "zai/glm-4") or None.
    """
    registry = FALLBACK_MODELS if use_fallback else AGENT_MODELS
    return registry.get(agent_key)


def list_agents() -> str:
    """Return a human-readable table of all agents and their models.

    Returns:
        Formatted string suitable for Telegram HTML message.
    """
    lines = ["<b>LegionSwarm 10/10 — Active Agents</b>\n"]
    for key, model in AGENT_MODELS.items():
        lines.append(f"  <b>{key}</b> → <code>{model}</code>")
    return "\n".join(lines)


# ── Thread Management ────────────────────────────────────────────────────────

def add_to_thread(thread_id: str, agent: str, task: str, result: str) -> None:
    """Store a conversation turn in thread history.
    
    Args:
        thread_id: Unique thread identifier (e.g. "workernet_training")
        agent: Agent key that processed this turn
        task: User's original task
        result: Agent's response
    """
    if thread_id not in ACTIVE_THREADS:
        ACTIVE_THREADS[thread_id] = []
    
    ACTIVE_THREADS[thread_id].append({
        "agent": agent,
        "task": task,
        "result": result[:500],  # Store first 500 chars to avoid memory bloat
        "timestamp": time.time()
    })
    
    # Keep only last 10 turns per thread
    if len(ACTIVE_THREADS[thread_id]) > 10:
        ACTIVE_THREADS[thread_id] = ACTIVE_THREADS[thread_id][-10:]
    
    logger.info("Added to thread '%s': %s agent", thread_id, agent)


def get_thread_context(thread_id: str, last_n: int = 3) -> str:
    """Get recent conversation context from a thread.
    
    Args:
        thread_id: Thread to retrieve context from
        last_n: Number of recent turns to include (default 3)
    
    Returns:
        Formatted conversation history or empty string if thread doesn't exist
    """
    if thread_id not in ACTIVE_THREADS or not ACTIVE_THREADS[thread_id]:
        return ""
    
    recent = ACTIVE_THREADS[thread_id][-last_n:]
    context_lines = ["Previous conversation in this thread:\n"]
    
    for turn in recent:
        time_str = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        context_lines.append(
            f"[{time_str}] {turn['agent'].upper()}: {turn['task'][:100]}..."
        )
        context_lines.append(f"Response: {turn['result']}\n")
    
    return "\n".join(context_lines)


def list_threads() -> str:
    """List all active threads with turn counts.
    
    Returns:
        Formatted list of threads for Telegram
    """
    if not ACTIVE_THREADS:
        return "<b>No active threads</b>\n\nUse <code>/thread &lt;name&gt;</code> to start one."
    
    lines = ["<b>Active Threads</b>\n"]
    for thread_id, turns in ACTIVE_THREADS.items():
        last_turn = turns[-1]
        time_str = datetime.fromtimestamp(last_turn["timestamp"]).strftime("%m/%d %H:%M")
        lines.append(
            f"📌 <b>{thread_id}</b> — {len(turns)} turns (last: {time_str})"
        )
    
    return "\n".join(lines)


def clear_thread(thread_id: str) -> bool:
    """Delete a thread's history.
    
    Args:
        thread_id: Thread to clear
    
    Returns:
        True if thread existed and was cleared, False otherwise
    """
    if thread_id in ACTIVE_THREADS:
        del ACTIVE_THREADS[thread_id]
        logger.info("Cleared thread '%s'", thread_id)
        return True
    return False
