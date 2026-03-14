"""Per-task model router — assigns the best LLM model to each task type.

Mirrors Perplexity Computer's 19-model routing:
- Fast/cheap models for simple tasks (Cerebras, Groq)
- Smart models for complex reasoning (Gemini Pro, Groq 70B)
- Code-specialized models for coding tasks
- Local models for privacy-sensitive tasks

Falls back to next-best model if primary is unavailable.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    TRIVIAL  = "trivial"   # single-fact lookup, <5 tokens
    SIMPLE   = "simple"    # standard Q&A, <500 tokens
    MEDIUM   = "medium"    # multi-step reasoning, <2000 tokens
    COMPLEX  = "complex"   # long-form, code gen, analysis, >2000 tokens
    CRITICAL = "critical"  # security audit, math proof, architecture design


@dataclass
class ModelCandidate:
    model: str
    provider: str
    speed_score: int     # 1-10, higher = faster
    quality_score: int   # 1-10, higher = better
    cost_per_1k: float   # USD per 1000 tokens
    context_window: int  # max tokens
    env_key: str         # env var that must be set
    specialties: List[str] = None

    def __post_init__(self):
        self.specialties = self.specialties or []

    def is_available(self) -> bool:
        return bool(os.getenv(self.env_key))


# Full model catalogue
MODEL_CATALOGUE: List[ModelCandidate] = [
    ModelCandidate("cerebras/llama-3.3-70b",        "cerebras",   10, 7,  0.0,    128_000, "CEREBRAS_API_KEY",   ["speed", "general"]),
    ModelCandidate("groq/llama-3.3-70b-versatile",  "groq",        9, 8,  0.0,    128_000, "GROQ_API_KEY",       ["coding", "debug", "general"]),
    ModelCandidate("groq/moonshard-r1-distill-70b", "groq",        8, 9,  0.0,    128_000, "GROQ_API_KEY",       ["math", "reasoning"]),
    ModelCandidate("groq/llama-3.1-8b-instant",     "groq",       10, 6,  0.0,    128_000, "GROQ_API_KEY",       ["speed", "trivial"]),
    ModelCandidate("gemini/gemini-2.0-flash",        "gemini",      8, 9,  0.0,  1_000_000, "GEMINI_API_KEY",     ["vision", "long_context", "research"]),
    ModelCandidate("gemini/gemini-2.5-pro-preview", "gemini",      6, 10, 0.001,2_000_000, "GEMINI_API_KEY",     ["complex", "architect", "critical"]),
    ModelCandidate("openrouter/deepseek/deepseek-chat-v3-0324", "openrouter", 7, 9, 0.0, 64_000, "OPENROUTER_API_KEY", ["coding", "math"]),
    ModelCandidate("openrouter/meta-llama/llama-4-maverick", "openrouter",  7, 9, 0.0, 128_000, "OPENROUTER_API_KEY", ["general", "analyst"]),
    ModelCandidate("openrouter/mistralai/mistral-small-3.1", "openrouter",  8, 7, 0.0, 128_000, "OPENROUTER_API_KEY", ["speed", "general"]),
    ModelCandidate("zai/glm-4-plus",                "zai",         7, 8,  0.0,    128_000, "ZAI_API_KEY",        ["math", "debug", "coding"]),
    ModelCandidate("ollama_chat/llava:latest",       "ollama",      5, 7,  0.0,    8_000,   "OLLAMA_BASE_URL",    ["vision", "privacy"]),
    ModelCandidate("ollama_chat/qwen2.5-coder:7b",  "ollama",      6, 7,  0.0,    32_000,  "OLLAMA_BASE_URL",    ["coding", "privacy"]),
]

# Agent key → required specialties (ordered by preference)
AGENT_SPECIALTIES: Dict[str, List[str]] = {
    "coding":      ["coding", "general"],
    "debug":       ["debug", "coding", "general"],
    "math":        ["math", "reasoning", "general"],
    "architect":   ["complex", "architect", "critical", "general"],
    "analyst":     ["long_context", "research", "general"],
    "researcher":  ["long_context", "research", "general"],
    "general":     ["general", "speed"],
    "vision":      ["vision", "general"],
    "devops":      ["coding", "general"],
    "pm":          ["general"],
}


class ModelRouter:
    """Routes each task to the best available model."""

    def select(
        self,
        agent_key: str,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        prefer_speed: bool = False,
        prefer_privacy: bool = False,
    ) -> Tuple[str, ModelCandidate]:
        """Return (model_string, candidate) for this agent+complexity."""
        available = [m for m in MODEL_CATALOGUE if m.is_available()]

        if not available:
            return "groq/llama-3.3-70b-versatile", None

        # Privacy: prefer local models
        if prefer_privacy:
            local = [m for m in available if m.provider == "ollama"]
            if local:
                return local[0].model, local[0]

        # Match specialties
        preferred_specialties = AGENT_SPECIALTIES.get(agent_key, ["general"])
        specialty_matches = [
            m for m in available
            if any(s in m.specialties for s in preferred_specialties)
        ]
        candidates = specialty_matches or available

        # Filter by complexity
        if complexity == TaskComplexity.CRITICAL:
            candidates = sorted(candidates, key=lambda m: -m.quality_score)
        elif complexity == TaskComplexity.TRIVIAL or prefer_speed:
            candidates = sorted(candidates, key=lambda m: -m.speed_score)
        else:
            # Balanced: quality * 0.7 + speed * 0.3
            candidates = sorted(
                candidates,
                key=lambda m: -(m.quality_score * 0.7 + m.speed_score * 0.3)
            )

        best = candidates[0]
        logger.debug(
            "ModelRouter: agent=%s complexity=%s → %s (q=%d s=%d)",
            agent_key, complexity.value, best.model, best.quality_score, best.speed_score,
        )
        return best.model, best

    def estimate_complexity(
        self,
        task_description: str,
    ) -> TaskComplexity:
        """Estimate task complexity from description length + keywords."""
        length = len(task_description)
        desc_lower = task_description.lower()

        critical_kws = ["audit", "security", "proof", "architecture", "production", "enterprise"]
        complex_kws  = ["implement", "build", "design", "analyze", "refactor", "optimize"]
        trivial_kws  = ["what is", "define", "list", "how many", "who is"]

        if any(k in desc_lower for k in critical_kws) or length > 1000:
            return TaskComplexity.CRITICAL
        if any(k in desc_lower for k in complex_kws) or length > 300:
            return TaskComplexity.COMPLEX
        if any(k in desc_lower for k in trivial_kws) or length < 50:
            return TaskComplexity.TRIVIAL
        return TaskComplexity.MEDIUM
