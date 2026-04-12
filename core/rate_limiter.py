"""Per-user request rate limiter (token bucket).

Prevents runaway API cost loops even from the authorised user.

Usage:
    from core.rate_limiter import RateLimiter
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    if not await limiter.allow(user_id):
        await msg.answer("⚠️ Rate limit reached. Wait 60 seconds.")
        return

Multi-limit support (per-type):
    from core.rate_limiter import MultiLimiter
    ml = MultiLimiter()
    if not ml.allow(user_id, "message"):
        ...
"""

import asyncio
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict

# ── Default limits ─────────────────────────────────────────────────────────────
DEFAULT_MESSAGE_LIMIT = 30  # messages per minute
DEFAULT_VOICE_LIMIT = 5  # voice messages per minute
DEFAULT_TOOL_LIMIT = 10  # tool calls per minute
WINDOW_SECONDS = 60  # sliding window

# Admin bypass — comma-separated user IDs from env
_ADMIN_BYPASS_STR = os.getenv("ADMIN_USER_IDS", os.getenv("ALLOWED_USER_ID", ""))
ADMIN_BYPASS: set[int] = set()
for part in _ADMIN_BYPASS_STR.replace(" ", "").split(","):
    if part.isdigit():
        ADMIN_BYPASS.add(int(part))


class RateLimiter:
    """Sliding-window rate limiter — one counter per user."""

    def __init__(self, max_requests: int = 10, window_seconds: int = WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: Dict[int, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _is_admin(self, user_id: int) -> bool:
        return user_id in ADMIN_BYPASS

    async def allow(self, user_id: int) -> bool:
        """Returns True if the request is allowed, False if rate limited."""
        if self._is_admin(user_id):
            return True
        now = time.monotonic()
        async with self._lock:
            window = self._windows[user_id]
            cutoff = now - self.window_seconds
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
        if self._is_admin(user_id):
            return self.max_requests
        now = time.monotonic()
        window = self._windows[user_id]
        cutoff = now - self.window_seconds
        active = sum(1 for t in window if t >= cutoff)
        return max(0, self.max_requests - active)


class MultiLimiter:
    """Per-user, per-type rate limiter with admin bypass."""

    def __init__(
        self,
        message_limit: int = DEFAULT_MESSAGE_LIMIT,
        voice_limit: int = DEFAULT_VOICE_LIMIT,
        tool_limit: int = DEFAULT_TOOL_LIMIT,
    ):
        self._limiters: Dict[str, RateLimiter] = {
            "message": RateLimiter(max_requests=message_limit),
            "voice": RateLimiter(max_requests=voice_limit),
            "tool": RateLimiter(max_requests=tool_limit),
        }

    async def allow(self, user_id: int, limit_type: str = "message") -> bool:
        """Check if request of given type is allowed for user."""
        limiter = self._limiters.get(limit_type, self._limiters["message"])
        return await limiter.allow(user_id)

    async def reset(self, user_id: int) -> None:
        """Reset all limits for a user."""
        for limiter in self._limiters.values():
            await limiter.reset(user_id)

    def remaining(self, user_id: int, limit_type: str = "message") -> int:
        """Requests remaining for user of given type."""
        limiter = self._limiters.get(limit_type, self._limiters["message"])
        return limiter.remaining(user_id)
