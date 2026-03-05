# /home/newadmin/swarm-bot/agents.py
"""Agent router: keyword-based task detection and model registry."""

from __future__ import annotations
import logging

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
}

# Default fallback agent when no keyword matches
DEFAULT_AGENT = "coding"


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
