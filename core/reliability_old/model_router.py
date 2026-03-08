# /home/newadmin/swarm-bot/reliability/model_router.py
"""Dynamic model routing by task complexity and cost tier.

Tiers:
- lightweight: Free ultra-fast models (Cerebras, Groq) — simple queries
- midweight: Standard models — average tasks
- heavyweight: Best-in-class models — complex multi-step tasks

Expected savings: 60-80% cost reduction by routing simple tasks to free fast models.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Model tiers — ordered by capability within each tier
TIERS: dict[str, dict] = {
    "lightweight": {
        "models": [
            "cerebras/qwen3-235b-a22b",       # Free, 1500 tok/s
            "groq/moonshotai/kimi-k2-instruct", # Free, fast
        ],
        "description": "Simple queries, fact retrieval, formatting",
        "max_task_len": 150,
    },
    "midweight": {
        "models": [
            "zai/glm-4",                        # Free, strong reasoning
            "openrouter/qwen/qwen3-coder:free", # Free coding
        ],
        "description": "Standard coding, debugging, math, explanation",
        "max_task_len": 600,
    },
    "heavyweight": {
        "models": [
            "openrouter/qwen/qwen3-coder:free",          # QwQ-Coder free tier
            "gemini/gemini-3.1-pro",                     # 1M context
            "cerebras/qwen3-235b-a22b",                  # Fast fallback
        ],
        "description": "Complex reasoning, multi-step, long-form",
        "max_task_len": None,  # No limit
    },
}

# Technical terms that indicate higher complexity
TECHNICAL_TERMS = [
    "pytorch", "cuda", "gradient", "backprop", "transformer", "attention",
    "eigenvalue", "tensor", "convolution", "dockerfile", "kubernetes",
    "async", "decorator", "metaclass", "coroutine", "distributed",
    "architecture", "algorithm", "optimization", "regularization",
]

# Multi-step indicators
MULTI_STEP_KWS = [
    "first", "then", "after that", "finally", "step by step",
    "and then", "also additionally", "commit", "restart", "deploy",
]


def classify_complexity(task: str) -> str:
    """Determine task complexity tier based on heuristics.

    Args:
        task: Raw task string from user.

    Returns:
        Tier name: 'lightweight' | 'midweight' | 'heavyweight'.
    """
    t = task.lower()
    length = len(task)

    # Count signals
    technical_count = sum(1 for term in TECHNICAL_TERMS if term in t)
    multi_step_count = sum(1 for kw in MULTI_STEP_KWS if kw in t)
    code_blocks = task.count("```")
    has_traceback = "traceback" in t or "error:" in t or "exception" in t

    # Heavyweight signals
    if (
        length > 500
        or multi_step_count >= 2
        or code_blocks >= 2
        or (technical_count >= 3 and has_traceback)
        or "architecture" in t
        or "design" in t and length > 200
    ):
        return "heavyweight"

    # Lightweight signals
    if (
        length < 80
        and technical_count == 0
        and multi_step_count == 0
        and not code_blocks
    ):
        return "lightweight"

    return "midweight"


def select_model(agent_key: str, task: str, force_tier: Optional[str] = None) -> str:
    """Select optimal model for the given agent and task.

    Primary agent model is used for heavyweight tier.
    Cheaper models replace primary for simpler tasks.

    Args:
        agent_key: Agent key (e.g. 'coding').
        task: Task string for complexity classification.
        force_tier: Override complexity detection with specific tier.

    Returns:
        Model string to use (e.g. 'cerebras/qwen3-235b-a22b').
    """
    import agents as ag

    tier = force_tier or classify_complexity(task)
    primary = ag.get_model(agent_key) or ""

    logger.info("Model routing: agent=%s tier=%s task_len=%d", agent_key, tier, len(task))

    # Vision agent always uses local model (privacy)
    if agent_key == "vision" or "ollama_chat/" in primary:
        return primary

    # For heavyweight tasks, use the configured primary model
    if tier == "heavyweight":
        return primary

    # For midweight/lightweight, try cheaper tier first
    tier_models = TIERS.get(tier, {}).get("models", [])
    if tier_models:
        selected = tier_models[0]
        logger.info("Routing to %s tier model: %s", tier, selected)
        return selected

    return primary


def routing_explanation(agent_key: str, task: str) -> str:
    """Return human-readable routing decision explanation.

    Args:
        agent_key: Agent key.
        task: Task string.

    Returns:
        Formatted explanation string.
    """
    tier = classify_complexity(task)
    model = select_model(agent_key, task)

    tier_info = TIERS.get(tier, {})
    return (
        f"Task complexity: <b>{tier}</b>\n"
        f"Routing to: <code>{model}</code>\n"
        f"Reason: {tier_info.get('description', '')}"
    )
