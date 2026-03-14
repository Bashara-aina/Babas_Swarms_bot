"""Per-user request rate limiter (token bucket).

Prevents runaway API cost loops even from the authorised user.

Usage:
    from core.rate_limiter import RateLimiter
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    if not await limiter.allow(user_id):
        await msg.answer("⚠️ Rate limit reached. Wait 60 seconds.")
        return
"""
import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Deque


class RateLimiter:
    """Sliding-window rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: Dict[int, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, user_id: int) -> bool:
        """Returns True if the request is allowed, False if rate limited."""
        now = time.monotonic()
        async with self._lock:
            window = self._windows[user_id]
            cutoff = now - self.window_seconds
            # evict expired timestamps
            while window and window[0] < cutoff:
                window.popleft()
            if len(window) >= self.max_requests:
                return False
            window.append(now)
            return True

    async def reset(self, user_id: int) -> None:
        """Reset the window for a user (e.g. after a timeout)."""
        async with self._lock:
            self._windows[user_id].clear()

    def remaining(self, user_id: int) -> int:
        """How many requests the user can still make in the current window."""
        now = time.monotonic()
        window = self._windows[user_id]
        cutoff = now - self.window_seconds
        active = sum(1 for t in window if t >= cutoff)
        return max(0, self.max_requests - active)
