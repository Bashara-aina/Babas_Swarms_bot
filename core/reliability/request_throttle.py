"""Client-side request throttling to prevent hitting upstream rate limits.

Implements per-provider token bucket rate limiting to space out requests
and avoid overwhelming free-tier API endpoints. Includes a per-provider
circuit breaker that opens after consecutive failures and recovers
automatically.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)

FAILURE_THRESHOLD = 5
FAILURE_RESET_TIMEOUT = 60.0

# Per-provider rate limits (requests per minute)
# Tuned based on observed API behavior
_PROVIDER_LIMITS: Dict[str, float] = {
    "openrouter": 12.0,     # OpenRouter free tier: conservative 12 req/min (was 6)
    "cerebras": 20.0,       # Cerebras: generous
    "groq": 30.0,           # Groq: high rate limit
    "gemini": 60.0,         # Gemini: very high rate limit
    "anthropic": 50.0,      # Claude: high tier
    "openai": 60.0,         # OpenAI: high tier
    "ollama": 9999.0,       # Local: no limit
    "ollama_chat": 9999.0,  # Local: no limit
}

# Token bucket state per provider
_buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {
    "tokens": 2.0,
    "last_update": time.monotonic(),
})

_circuit_failures: Dict[str, int] = defaultdict(int)
_circuit_open_since: Dict[str, float] = {}


class RequestThrottle:
    """Token bucket rate limiter for API requests."""

    @staticmethod
    def _extract_provider(model: str) -> str:
        """Extract provider name from model string.

        Args:
            model: Full model string (e.g., "openrouter/qwen/qwen3-coder:free")

        Returns:
            Provider name (e.g., "openrouter")
        """
        if model.startswith("ollama"):
            return "ollama"
        # Extract first part before /
        parts = model.split("/")
        return parts[0] if parts else "unknown"

    @staticmethod
    async def acquire(model: str, timeout: float = 30.0) -> bool:
        """Acquire permission to make a request (async token bucket).

        Args:
            model: Model string to extract provider from
            timeout: Maximum seconds to wait for token (default 30s)

        Returns:
            True if token acquired, False if timeout
        """
        provider = RequestThrottle._extract_provider(model)
        rate_limit = _PROVIDER_LIMITS.get(provider, 15.0)

        if rate_limit >= 60:
            return True

        if provider in _circuit_open_since:
            elapsed = time.monotonic() - _circuit_open_since[provider]
            if elapsed < FAILURE_RESET_TIMEOUT:
                if _circuit_failures[provider] >= FAILURE_THRESHOLD:
                    logger.warning("Circuit OPEN for provider '%s' (failed %d times, %.0fs until reset)",
                        provider, _circuit_failures[provider], FAILURE_RESET_TIMEOUT - elapsed)
                    return False
            else:
                logger.info("Circuit HALF-OPEN for provider '%s' — allowing one probe", provider)

        bucket = _buckets[provider]
        tokens_per_second = rate_limit / 60.0
        max_tokens = 3.0

        start_time = time.monotonic()

        while True:
            now = time.monotonic()
            elapsed = now - bucket["last_update"]

            bucket["tokens"] = min(
                max_tokens,
                bucket["tokens"] + (elapsed * tokens_per_second)
            )
            bucket["last_update"] = now

            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                if provider in _circuit_open_since:
                    _circuit_failures.pop(provider, None)
                    _circuit_open_since.pop(provider, None)
                    logger.info("Circuit CLOSED for provider '%s' — recovered", provider)
                logger.debug(
                    "Token acquired for provider '%s' (%.2f tokens remaining)",
                    provider, bucket["tokens"],
                )
                return True

            if now - start_time >= timeout:
                _circuit_failures[provider] = _circuit_failures.get(provider, 0) + 1
                if _circuit_failures[provider] >= FAILURE_THRESHOLD:
                    _circuit_open_since[provider] = time.monotonic()
                    logger.error(
                        "Circuit OPENED for provider '%s' after %d consecutive failures",
                        provider, _circuit_failures[provider],
                    )
                else:
                    logger.warning(
                        "Request throttle timeout for provider '%s' after %.1fs (failures: %d/%d)",
                        provider, timeout, _circuit_failures[provider], FAILURE_THRESHOLD,
                    )
                return False

            wait_time = (1.0 - bucket["tokens"]) / tokens_per_second
            wait_time = min(wait_time, 1.0)

            logger.debug(
                "Provider '%s' throttled, waiting %.1fs for token",
                provider, wait_time,
            )
            await asyncio.sleep(wait_time)

    @staticmethod
    def reset(provider: str) -> None:
        """Reset throttle and circuit breaker state for a provider (admin intervention)."""
        if provider in _buckets:
            _buckets[provider] = {
                "tokens": 3.0,
                "last_update": time.monotonic(),
            }
        _circuit_failures.pop(provider, None)
        _circuit_open_since.pop(provider, None)
        logger.info("Request throttle and circuit breaker reset for provider '%s'", provider)

    @staticmethod
    def get_wait_time(model: str) -> float:
        """Get estimated wait time before next request is allowed.

        Args:
            model: Model string

        Returns:
            Estimated wait time in seconds (0 if ready immediately)
        """
        provider = RequestThrottle._extract_provider(model)
        rate_limit = _PROVIDER_LIMITS.get(provider, 15.0)

        if rate_limit >= 60:
            return 0.0

        bucket = _buckets[provider]
        if bucket["tokens"] >= 1.0:
            return 0.0

        tokens_per_second = rate_limit / 60.0
        return (1.0 - bucket["tokens"]) / tokens_per_second
