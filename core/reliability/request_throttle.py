"""Client-side request throttling to prevent hitting upstream rate limits.

Implements per-provider token bucket rate limiting to space out requests
and avoid overwhelming free-tier API endpoints.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)

# Per-provider rate limits (requests per minute)
_PROVIDER_LIMITS: Dict[str, float] = {
    "openrouter": 6.0,      # OpenRouter free tier: ~6 requests/min
    "cerebras": 10.0,       # Cerebras: more generous
    "groq": 30.0,           # Groq: high rate limit
    "gemini": 60.0,         # Gemini: very high rate limit
    "ollama": 9999.0,       # Local: no limit
}

# Token bucket state per provider
_buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {
    "tokens": 1.0,           # Start with 1 token available
    "last_update": time.monotonic(),
})


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
        rate_limit = _PROVIDER_LIMITS.get(provider, 10.0)  # Default: 10 req/min
        
        # No throttling for local or high-limit providers
        if rate_limit >= 60:
            return True
        
        bucket = _buckets[provider]
        tokens_per_second = rate_limit / 60.0
        max_tokens = 2.0  # Burst capacity
        
        start_time = time.monotonic()
        
        while True:
            now = time.monotonic()
            elapsed = now - bucket["last_update"]
            
            # Refill tokens based on elapsed time
            bucket["tokens"] = min(
                max_tokens,
                bucket["tokens"] + (elapsed * tokens_per_second)
            )
            bucket["last_update"] = now
            
            # Try to consume 1 token
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                logger.debug(
                    "Token acquired for provider '%s' (%.2f tokens remaining)",
                    provider, bucket["tokens"]
                )
                return True
            
            # Check timeout
            if now - start_time >= timeout:
                logger.warning(
                    "Request throttle timeout for provider '%s' after %.1fs",
                    provider, timeout
                )
                return False
            
            # Wait for next token to become available
            wait_time = (1.0 - bucket["tokens"]) / tokens_per_second
            wait_time = min(wait_time, 2.0)  # Cap at 2 seconds per iteration
            
            logger.debug(
                "Provider '%s' throttled, waiting %.1fs for token",
                provider, wait_time
            )
            await asyncio.sleep(wait_time)

    @staticmethod
    def reset(provider: str) -> None:
        """Reset throttle state for a provider (admin intervention).
        
        Args:
            provider: Provider name
        """
        if provider in _buckets:
            _buckets[provider] = {
                "tokens": 1.0,
                "last_update": time.monotonic(),
            }
            logger.info("Request throttle reset for provider '%s'", provider)

    @staticmethod
    def get_wait_time(model: str) -> float:
        """Get estimated wait time before next request is allowed.
        
        Args:
            model: Model string
            
        Returns:
            Estimated wait time in seconds (0 if ready immediately)
        """
        provider = RequestThrottle._extract_provider(model)
        rate_limit = _PROVIDER_LIMITS.get(provider, 10.0)
        
        if rate_limit >= 60:
            return 0.0
        
        bucket = _buckets[provider]
        if bucket["tokens"] >= 1.0:
            return 0.0
        
        tokens_per_second = rate_limit / 60.0
        return (1.0 - bucket["tokens"]) / tokens_per_second
