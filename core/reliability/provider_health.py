"""Provider health tracking and circuit breaker for API rate limits.

Tracks provider availability and automatically routes away from recently
rate-limited providers to prevent cascading failures.
"""

from __future__ import annotations

import logging
import time
from typing import Literal

logger = logging.getLogger(__name__)

# Provider health state: tracks last rate limit time and circuit breaker status
_provider_health: dict[str, dict[str, float | str]] = {}

# Circuit breaker thresholds (seconds)
_CIRCUIT_OPEN_DURATION = 120  # Block provider for 2 minutes after rate limit
_RATE_LIMIT_COOLDOWN = 60     # Remember rate limit for 1 minute minimum


ProviderStatus = Literal["healthy", "degraded", "unavailable"]


def record_rate_limit(provider: str) -> None:
    """Record a rate limit event for a provider.
    
    Args:
        provider: Provider name (e.g., "openrouter", "cerebras")
    """
    now = time.monotonic()
    _provider_health[provider] = {
        "last_rate_limit": now,
        "circuit_status": "open",  # Circuit open = block requests
    }
    logger.warning(
        "Provider '%s' rate limited — circuit open for %d seconds",
        provider, _CIRCUIT_OPEN_DURATION
    )


def check_provider_health(provider: str) -> ProviderStatus:
    """Check if a provider is healthy enough to use.
    
    Args:
        provider: Provider name
        
    Returns:
        "healthy" if provider is safe to use
        "degraded" if recently rate-limited but cooldown expired
        "unavailable" if circuit breaker is still open
    """
    if provider not in _provider_health:
        return "healthy"
    
    health = _provider_health[provider]
    now = time.monotonic()
    last_rate_limit = health.get("last_rate_limit", 0.0)
    time_since_limit = now - last_rate_limit
    
    # Circuit breaker still open — completely block this provider
    if time_since_limit < _CIRCUIT_OPEN_DURATION:
        remaining = int(_CIRCUIT_OPEN_DURATION - time_since_limit)
        logger.debug(
            "Provider '%s' circuit open (unavailable for %ds more)",
            provider, remaining
        )
        return "unavailable"
    
    # Cooldown period — provider usable but considered degraded
    if time_since_limit < (_CIRCUIT_OPEN_DURATION + _RATE_LIMIT_COOLDOWN):
        logger.debug("Provider '%s' in cooldown (degraded)", provider)
        return "degraded"
    
    # Full recovery — clear health record
    logger.debug("Provider '%s' fully recovered", provider)
    del _provider_health[provider]
    return "healthy"


def get_healthy_provider(preferred: str, fallback: str = "ollama") -> str:
    """Get the best available provider, considering health status.
    
    Args:
        preferred: Preferred provider (e.g., "openrouter")
        fallback: Fallback provider if preferred is unavailable
        
    Returns:
        Provider name to use
    """
    status = check_provider_health(preferred)
    
    if status == "healthy":
        logger.debug("Using preferred provider: %s", preferred)
        return preferred
    elif status == "degraded":
        logger.info(
            "Provider '%s' recently rate-limited but available — using with caution",
            preferred
        )
        return preferred
    else:  # unavailable
        logger.warning(
            "Provider '%s' circuit open — routing to fallback: %s",
            preferred, fallback
        )
        return fallback


def reset_provider_health(provider: str) -> None:
    """Manually reset provider health (for testing or admin intervention).
    
    Args:
        provider: Provider name
    """
    if provider in _provider_health:
        del _provider_health[provider]
        logger.info("Provider '%s' health reset by admin", provider)


def get_all_provider_status() -> dict[str, ProviderStatus]:
    """Get health status for all tracked providers.
    
    Returns:
        Dict mapping provider names to their current status
    """
    return {
        provider: check_provider_health(provider)
        for provider in _provider_health.keys()
    }
