"""Skills registry — auto-imports all builtin skill modules."""

from core.skills.registry import SKILL_REGISTRY, get_skill_registry

# Import all builtin modules to trigger registration
from core.skills.builtin import github, media, memory, personal, productivity, research, system, web

__all__ = [
    "SKILL_REGISTRY",
    "get_skill_registry",
    "github",
    "media",
    "memory",
    "personal",
    "productivity",
    "research",
    "system",
    "web",
]
