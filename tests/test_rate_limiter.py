"""Unit tests for the sliding-window rate limiter."""
import asyncio
import pytest
from core.rate_limiter import RateLimiter


class TestRateLimiter:
    @pytest.fixture
    def limiter(self):
        return RateLimiter(max_requests=3, window_seconds=60)

    @pytest.mark.asyncio
    async def test_allows_under_limit(self, limiter):
        for _ in range(3):
            assert await limiter.allow(user_id=1) is True

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, limiter):
        for _ in range(3):
            await limiter.allow(user_id=1)
        assert await limiter.allow(user_id=1) is False

    @pytest.mark.asyncio
    async def test_different_users_independent(self, limiter):
        for _ in range(3):
            await limiter.allow(user_id=1)
        # user 2 should still be allowed
        assert await limiter.allow(user_id=2) is True

    @pytest.mark.asyncio
    async def test_reset_clears_window(self, limiter):
        for _ in range(3):
            await limiter.allow(user_id=1)
        assert await limiter.allow(user_id=1) is False
        await limiter.reset(user_id=1)
        assert await limiter.allow(user_id=1) is True

    @pytest.mark.asyncio
    async def test_remaining_decrements(self, limiter):
        assert limiter.remaining(1) == 3
        await limiter.allow(user_id=1)
        assert limiter.remaining(1) == 2

    @pytest.mark.asyncio
    async def test_window_expiry(self):
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        await limiter.allow(user_id=1)
        await limiter.allow(user_id=1)
        assert await limiter.allow(user_id=1) is False
        await asyncio.sleep(1.1)
        assert await limiter.allow(user_id=1) is True
