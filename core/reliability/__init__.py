"""Reliability layer: fallback chains, model routing, provider health, throttling.

Exports the public API for the reliability subsystem.
"""

from __future__ import annotations

try:
    from core.reliability.fallback_chain import FallbackChain, get_fallback_chain
except ImportError as exc:
    raise ImportError(f"core.reliability.fallback_chain unavailable: {exc}") from exc

try:
    from core.reliability.model_router import classify_complexity, select_model
except ImportError as exc:
    raise ImportError(f"core.reliability.model_router unavailable: {exc}") from exc

try:
    from core.reliability.provider_health import (
        check_provider_health,
        get_all_provider_status,
        record_rate_limit,
        reset_provider_health,
    )
except ImportError as exc:
    raise ImportError(f"core.reliability.provider_health unavailable: {exc}") from exc

try:
    from core.reliability.error_recovery import get_recovery
except ImportError as exc:
    raise ImportError(f"core.reliability.error_recovery unavailable: {exc}") from exc

try:
    from core.reliability.request_throttle import RequestThrottle
except ImportError as exc:
    raise ImportError(f"core.reliability.request_throttle unavailable: {exc}") from exc

__all__ = [
    "FallbackChain",
    "get_fallback_chain",
    "select_model",
    "classify_complexity",
    "check_provider_health",
    "record_rate_limit",
    "get_all_provider_status",
    "reset_provider_health",
    "get_recovery",
    "RequestThrottle",
]
