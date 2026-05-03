"""Skills registry — auto-imports all builtin skill modules."""

# Import standalone skill modules to trigger registration
from core.skills import code_review, deep_research, dify_analysis, doc_parser, timer

# Import all builtin modules to trigger registration
from core.skills.builtin import github, media, memory, personal, productivity, research, system, web
from core.skills.registry import SKILL_REGISTRY, get_skill_registry

__all__ = [
    "SKILL_REGISTRY",
    "code_review",
    "deep_research",
    "dify_analysis",
    "doc_parser",
    "get_skill_registry",
    "github",
    "media",
    "memory",
    "personal",
    "productivity",
    "research",
    "system",
    "timer",
    "web",
]
