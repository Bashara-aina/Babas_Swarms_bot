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
    "RequestThrottle",
    "check_provider_health",
    "classify_complexity",
    "get_all_provider_status",
    "get_fallback_chain",
    "get_recovery",
    "record_rate_limit",
    "reset_provider_health",
    "select_model",
]
