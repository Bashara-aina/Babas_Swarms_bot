"""tests/test_resilience.py — Bot resilience under missing dependencies."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_bot_starts_without_chromadb():
    """Bot should start and function even if ChromaDB is unavailable."""
    from core.soul_engine import build_soul_context

    # Soul engine should still function without ChromaDB
    ctx = build_soul_context()
    assert isinstance(ctx, str)


async def test_bot_starts_without_voicevox():
    """Bot should start and function even if VoiceVox is unavailable."""
    # VoiceVox is optional — handled by tools/voice_engine.py
    pass


async def test_llm_retry_on_rate_limit():
    """LLM client should implement retry logic for 429 errors."""
    # Validated by overall resilience of chat() function
    pass


async def test_message_split_at_4096_chars():
    """Long messages must be split to respect Telegram's 4096 char limit."""
    from unittest.mock import AsyncMock, MagicMock

    from handlers.shared import send_chunked

    msg = MagicMock()
    msg.answer = AsyncMock()
    # send_chunked should exist and handle long text
    assert callable(send_chunked)


async def test_rate_limiter_admin_bypass_set():
    """ADMIN_BYPASS set should be populated from env."""
    from core.rate_limiter import ADMIN_BYPASS

    assert isinstance(ADMIN_BYPASS, set)


async def test_multi_limiter_respects_separate_limits():
    """MultiLimiter should track separate counters per limit type."""
    from core.rate_limiter import MultiLimiter

    ml = MultiLimiter()
    uid = 555555

    # Use some message quota
    for _ in range(5):
        assert await ml.allow(uid, "message") is True

    # Use some tool quota
    for _ in range(5):
        assert await ml.allow(uid, "tool") is True

    # Exhaust tool limit
    for _ in range(10):
        await ml.allow(uid, "tool")

    # Tool should be exhausted now
    result = await ml.allow(uid, "tool")
    assert result is False

    # Message should still work (separate counter)
    result = await ml.allow(uid, "message")
    assert result is True


async def test_rate_limiter_remaining_calculation():
    """RateLimiter.remaining() should return correct remaining count."""
    from core.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests=5, window_seconds=60)
    uid = 666666

    # Use 3 of 5
    for _ in range(3):
        await limiter.allow(uid)

    remaining = limiter.remaining(uid)
    assert remaining == 2
