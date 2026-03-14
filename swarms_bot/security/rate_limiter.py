"""Rate limiter — token bucket per user with configurable limits.

Prevents abuse through per-user request throttling.
Uses in-memory storage (single-user bot).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int = 0
    reset_seconds: float = 0.0
    reason: str = ""


@dataclass
class _Bucket:
    """Token bucket for a single user."""

    tokens: float
    last_update: float
    max_tokens: int


class RateLimiter:
    """Token bucket rate limiter.

    Refills tokens over time, deducts one per request.
    Suitable for Telegram bot with single authorized user.
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        burst_size: int = 10,
    ) -> None:
        self.rpm = requests_per_minute
        self.burst_size = burst_size
        self._buckets: Dict[int, _Bucket] = {}

    def check(self, user_id: int) -> RateLimitResult:
        """Check if user is within rate limit. Consumes one token if allowed.

        Args:
            user_id: Telegram user ID.

        Returns:
            RateLimitResult indicating if request is allowed.
        """
        now = time.monotonic()

        if user_id not in self._buckets:
            self._buckets[user_id] = _Bucket(
                tokens=float(self.burst_size),
                last_update=now,
                max_tokens=self.burst_size,
            )

        bucket = self._buckets[user_id]

        # Refill tokens based on elapsed time
        elapsed = now - bucket.last_update
        refill = elapsed * (self.rpm / 60.0)
        bucket.tokens = min(bucket.max_tokens, bucket.tokens + refill)
        bucket.last_update = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return RateLimitResult(
                allowed=True,
                remaining=int(bucket.tokens),
            )

        # Calculate when next token available
        deficit = 1.0 - bucket.tokens
        wait_seconds = deficit / (self.rpm / 60.0)

        return RateLimitResult(
            allowed=False,
            remaining=0,
            reset_seconds=wait_seconds,
            reason=f"Rate limit: wait {wait_seconds:.1f}s",
        )

    def reset(self, user_id: int) -> None:
        """Reset rate limit for a user."""
        if user_id in self._buckets:
            del self._buckets[user_id]
