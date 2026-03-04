# /home/newadmin/swarm-bot/agents.py
"""Agent router: keyword-based task detection and model registry."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Full model registry — keys match /agent <name> command
AGENT_MODELS: dict[str, str] = {
    "vision": "ollama_chat/gemma3:12b",
    "coding": "ollama_chat/qwen3.5:35b",
    "debug": "ollama_chat/exaone-deep:32b",
    "math": "ollama_chat/phi4",
    "architect": "ollama_chat/llama3.3:70b",
}

# Keyword → agent mapping (auto-routing via /run command)
# IMPORTANT: Always show the full dict when editing this.
TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot",
        "image",
        "photo",
        "ui",
        "visual",
        "look at",
        "describe",
        "ocr",
        "pixel",
        "multimodal",
    ],
    "coding": [
        "code",
        "function",
        "script",
        "write",
        "implement",
        "class",
        "module",
        "refactor",
        "generate",
        "syntax",
        "api",
        "endpoint",
        "database",
        "sql",
        "query",
    ],
    "debug": [
        "debug",
        "error",
        "traceback",
        "exception",
        "crash",
        "fix",
        "bug",
        "cuda",
        "pytorch",
        "torch",
        "workernet",
        "nan",
        "oom",
        "out of memory",
        "gradient",
        "backward",
        "loss",
    ],
    "math": [
        "math",
        "tensor",
        "matrix",
        "equation",
        "derivative",
        "integral",
        "gradient descent",
        "backprop",
        "linear algebra",
        "eigenvalue",
        "softmax",
        "norm",
        "convolution",
        "fourier",
    ],
    "architect": [
        "design",
        "architecture",
        "plan",
        "system",
        "pipeline",
        "overview",
        "summarize",
        "explain",
        "high level",
        "strategy",
        "structure",
        "long",
        "document",
        "thesis",
        "research",
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


def get_model(agent_key: str) -> str | None:
    """Return the Ollama model string for an agent key, or None if unknown.

    Args:
        agent_key: One of the keys in AGENT_MODELS.

    Returns:
        Full model string (e.g. "ollama_chat/phi4") or None.
    """
    return AGENT_MODELS.get(agent_key)


def list_agents() -> str:
    """Return a human-readable table of all agents and their models.

    Returns:
        Formatted string suitable for Telegram HTML message.
    """
    lines = ["<b>Active Agent Roster</b>\n"]
    for key, model in AGENT_MODELS.items():
        lines.append(f"  <b>{key}</b> → <code>{model}</code>")
    return "\n".join(lines)
