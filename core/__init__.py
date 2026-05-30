"""Core infrastructure package."""

from __future__ import annotations

import importlib
from typing import Any

# Re-exported for public API (documented in ADR-003)
from core.reliability.fallback_chain import FallbackChain, get_fallback_chain
from core.reliability.model_router import classify_complexity, select_model

_LAZY_CORE_SUBMODULES = frozenset({"openai_agents_bridge", "swarm_topologies"})

__all__ = [
    "FallbackChain",
    "classify_complexity",
    "get_fallback_chain",
    "select_model",
]


def __getattr__(name: str) -> Any:
    if name in _LAZY_CORE_SUBMODULES:
        return importlib.import_module(f"core.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_CORE_SUBMODULES) | set(__all__))
