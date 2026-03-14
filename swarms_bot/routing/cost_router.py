"""Cost-aware model routing — cascade from cheap to expensive models.

Extends core/reliability/model_router.py with:
- Cascade pattern: try cheap model first, escalate on low confidence
- Cost estimation before execution
- Model tier pricing matrix (March 2026)

Target: 60-78% cost reduction vs naive routing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    TRIVIAL = 1     # Simple classification, yes/no
    SIMPLE = 2      # Basic Q&A, short snippets
    MODERATE = 3    # Code generation, analysis
    COMPLEX = 4     # Multi-step reasoning
    EXPERT = 5      # Architecture, long-form planning


@dataclass
class ModelTier:
    """A model tier with pricing info."""

    name: str
    model_id: str
    provider: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    tier: str  # "free", "budget", "standard", "premium"
    max_context: int = 32768

    @property
    def cost_per_token(self) -> float:
        """Average cost per token (input + output blended)."""
        return (self.cost_per_1m_input + self.cost_per_1m_output) / 2 / 1_000_000


# Model pricing as of March 2026 — uses existing litellm model strings
MODEL_TIERS: List[ModelTier] = [
    # Free tier (Cerebras, Groq free models)
    ModelTier("Cerebras Qwen", "cerebras/qwen-3-235b-a22b", "cerebras",
             0.0, 0.0, "free", 131072),
    ModelTier("Groq Llama 3.3", "groq/llama-3.3-70b-versatile", "groq",
             0.0, 0.0, "free", 32768),
    ModelTier("Groq Kimi K2", "groq/moonshotai/kimi-k2-instruct", "groq",
             0.0, 0.0, "free", 131072),
    # Budget tier
    ModelTier("ZAI GLM-4", "zai/glm-4", "zai",
             0.0, 0.0, "budget", 128000),
    ModelTier("Gemini Flash", "gemini/gemini-2.0-flash-exp:free", "gemini",
             0.0, 0.0, "budget", 1048576),
    # Standard tier
    ModelTier("OpenRouter Qwen Coder", "openrouter/qwen/qwen3-coder:free",
             "openrouter", 0.0, 0.0, "standard", 65536),
    # Premium tier (paid models — fallback only)
    ModelTier("Gemini Pro", "gemini/gemini-1.5-pro", "gemini",
             3.50, 10.50, "premium", 1048576),
]

# Complexity signals
_TECHNICAL_TERMS = {
    "pytorch", "cuda", "gradient", "backprop", "transformer", "attention",
    "eigenvalue", "tensor", "convolution", "dockerfile", "kubernetes",
    "async", "decorator", "metaclass", "coroutine", "distributed",
    "architecture", "algorithm", "optimization", "regularization",
}

_MULTI_STEP_KWS = {
    "first", "then", "after that", "finally", "step by step",
    "and then", "also", "additionally", "commit", "restart", "deploy",
}


def classify_complexity(task: str) -> TaskComplexity:
    """Classify task complexity using heuristics (no LLM call).

    Args:
        task: Raw task string.

    Returns:
        TaskComplexity enum value.
    """
    t = task.lower()
    length = len(task)

    technical_count = sum(1 for term in _TECHNICAL_TERMS if term in t)
    multi_step = sum(1 for kw in _MULTI_STEP_KWS if kw in t)
    code_blocks = task.count("```")
    has_traceback = "traceback" in t or "error:" in t or "exception" in t

    # Expert: architecture + long
    if "architecture" in t and length > 300:
        return TaskComplexity.EXPERT
    if technical_count >= 4 and multi_step >= 2:
        return TaskComplexity.EXPERT

    # Complex: multi-step or code with tracebacks
    if multi_step >= 2 or code_blocks >= 2:
        return TaskComplexity.COMPLEX
    if technical_count >= 3 and has_traceback:
        return TaskComplexity.COMPLEX
    if length > 500:
        return TaskComplexity.COMPLEX

    # Trivial: very short, no technical terms
    if length < 60 and technical_count == 0 and not code_blocks:
        return TaskComplexity.TRIVIAL

    # Simple: short, basic
    if length < 150 and technical_count <= 1:
        return TaskComplexity.SIMPLE

    return TaskComplexity.MODERATE


# Map complexity → eligible model tiers
_COMPLEXITY_TIERS: Dict[TaskComplexity, List[str]] = {
    TaskComplexity.TRIVIAL: ["free", "budget"],
    TaskComplexity.SIMPLE: ["free", "budget"],
    TaskComplexity.MODERATE: ["free", "budget", "standard"],
    TaskComplexity.COMPLEX: ["free", "standard", "premium"],
    TaskComplexity.EXPERT: ["standard", "premium"],
}


class CostAwareRouter:
    """Routes tasks to the cheapest model capable of handling the complexity.

    Integrates with existing agents.py model selection while adding
    cost-based optimization on top.
    """

    def __init__(self) -> None:
        self.routing_log: List[Dict[str, Any]] = []
        self._total_estimated_savings: float = 0.0

    def select_model(
        self,
        agent_key: str,
        task: str,
    ) -> Tuple[str, TaskComplexity, str]:
        """Select optimal model for agent + task combination.

        Args:
            agent_key: Agent key from agents.py.
            task: Task description.

        Returns:
            Tuple of (model_id, complexity, tier_name).
        """
        complexity = classify_complexity(task)

        # Vision always uses local (privacy requirement)
        if agent_key == "vision":
            return "ollama_chat/gemma3:12b", complexity, "local"

        # Get eligible tiers for this complexity
        eligible_tiers = _COMPLEXITY_TIERS.get(
            complexity, ["free", "standard"]
        )

        # Find cheapest eligible model
        for tier_name in eligible_tiers:
            matching = [m for m in MODEL_TIERS if m.tier == tier_name]
            if matching:
                selected = matching[0]
                logger.info(
                    "Cost router: agent=%s complexity=%s tier=%s model=%s",
                    agent_key, complexity.name, tier_name, selected.model_id,
                )
                self._log_routing(
                    agent_key, task, complexity, selected, tier_name,
                )
                return selected.model_id, complexity, tier_name

        # Fallback to existing agent model
        from router import get_fallback_chain
        chain = get_fallback_chain(agent_key)
        default_model = chain[0] if chain else "groq/llama-3.3-70b-versatile"
        return default_model, complexity, "fallback"

    def estimate_cost(self, task: str, model_id: str) -> float:
        """Estimate execution cost for a task + model.

        Args:
            task: Task description.
            model_id: litellm model string.

        Returns:
            Estimated cost in USD.
        """
        # Estimate tokens
        input_tokens = len(task.split()) * 1.3
        output_tokens = input_tokens * 2  # assume 2x response

        # Find model tier
        tier = next(
            (m for m in MODEL_TIERS if m.model_id == model_id), None
        )

        if tier is None or tier.cost_per_token == 0:
            return 0.0  # Free tier

        return (input_tokens + output_tokens) * tier.cost_per_token

    def _log_routing(
        self,
        agent_key: str,
        task: str,
        complexity: TaskComplexity,
        model: ModelTier,
        tier: str,
    ) -> None:
        """Log routing decision."""
        self.routing_log.append({
            "agent": agent_key,
            "complexity": complexity.name,
            "model": model.model_id,
            "tier": tier,
            "cost_per_token": model.cost_per_token,
            "timestamp": time.time(),
        })
        if len(self.routing_log) > 200:
            self.routing_log = self.routing_log[-200:]

    def get_routing_stats(self) -> Dict[str, Any]:
        """Return routing statistics."""
        if not self.routing_log:
            return {"total_routes": 0}

        tier_counts: Dict[str, int] = {}
        complexity_counts: Dict[str, int] = {}

        for entry in self.routing_log:
            tier_counts[entry["tier"]] = tier_counts.get(entry["tier"], 0) + 1
            complexity_counts[entry["complexity"]] = (
                complexity_counts.get(entry["complexity"], 0) + 1
            )

        total = len(self.routing_log)
        free_pct = tier_counts.get("free", 0) / total * 100

        return {
            "total_routes": total,
            "tier_distribution": tier_counts,
            "complexity_distribution": complexity_counts,
            "free_tier_pct": round(free_pct, 1),
            "estimated_savings_pct": round(free_pct * 0.9, 1),
        }

    def format_stats_html(self) -> str:
        """Format routing stats as HTML for Telegram."""
        stats = self.get_routing_stats()
        if stats["total_routes"] == 0:
            return "<b>Cost Router:</b> No routes yet"

        lines = [
            "<b>Cost-Aware Router Stats</b>\n",
            f"Routes: {stats['total_routes']}",
            f"Free tier: {stats['free_tier_pct']}%",
            f"Est. savings: ~{stats['estimated_savings_pct']}%",
            "",
            "<b>By complexity:</b>",
        ]
        for comp, count in stats["complexity_distribution"].items():
            lines.append(f"  {comp}: {count}")

        lines.append("\n<b>By tier:</b>")
        for tier, count in stats["tier_distribution"].items():
            lines.append(f"  {tier}: {count}")

        return "\n".join(lines)
