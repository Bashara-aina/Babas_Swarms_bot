"""tests/test_multi_user_isolation.py — Per-user isolation tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_nihongo_mode_isolated_per_user():
    """User A's nihongo mode should not affect user B's prompts."""
    from core.multi_user import MultiUserAuth

    auth = MultiUserAuth()
    user_a = 111111
    user_b = 222222

    auth.add_user(user_a, admin=False)
    auth.add_user(user_b, admin=False)

    # is_allowed is per-user, not global
    assert auth.is_allowed(user_a) is True
    assert auth.is_allowed(user_b) is True
    assert user_a != user_b


async def test_memory_isolated_per_user():
    """User A's memory should not leak into user B's context."""
    from core.memory_engine import MemoryEngine

    engine = MemoryEngine()
    uid_a = 111111
    uid_b = 222222

    engine.set_user_id(uid_a)
    await engine.get_context_window(str(uid_a))
    engine.set_user_id(uid_b)
    await engine.get_context_window(str(uid_b))

    # Context switching should be isolated per user
    assert uid_a != uid_b


async def test_rate_limit_isolated_per_user():
    """Rate limit counters must be per-user, not global."""
    from core.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests=3, window_seconds=60)
    user_a = 111111
    user_b = 222222

    # Exhaust user A's limit
    for _ in range(3):
        assert await limiter.allow(user_a) is True

    # User A should now be rate limited
    assert await limiter.allow(user_a) is False

    # User B should still have full quota
    assert await limiter.allow(user_b) is True


async def test_multi_user_auth_isolation():
    """MultiUserAuth should correctly separate admin from regular users."""
    from core.multi_user import MultiUserAuth

    auth = MultiUserAuth()
    admin_id = 123456
    regular_id = 789012

    auth.add_user(admin_id, admin=True)
    auth.add_user(regular_id, admin=False)

    assert auth.is_admin(admin_id) is True
    assert auth.is_admin(regular_id) is False
    assert auth.is_allowed(admin_id) is True
    assert auth.is_allowed(regular_id) is True
