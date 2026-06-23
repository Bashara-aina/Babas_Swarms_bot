"""Tests for core/reliability/request_throttle.py"""

import pytest

from core.reliability.request_throttle import (
    RequestThrottle,
    _buckets,
    _circuit_failures,
    _circuit_open_since,
)


class TestRequestThrottle:
    def setup_method(self):
        _buckets.clear()
        _circuit_failures.clear()
        _circuit_open_since.clear()

    def test_extract_provider_ollama(self):
        assert RequestThrottle._extract_provider("ollama_chat/gemma4:e4b") == "ollama"
        assert RequestThrottle._extract_provider("ollama/qwen2:7b") == "ollama"

    def test_extract_provider_slash_format(self):
        assert RequestThrottle._extract_provider("minimax-coding-plan/MiniMax-M3") == "minimax-coding-plan"
        assert RequestThrottle._extract_provider("openrouter/qwen/qwen3-coder:free") == "openrouter"

    def test_extract_provider_no_slash(self):
        assert RequestThrottle._extract_provider("unknown-model") == "unknown-model"

    @pytest.mark.asyncio
    async def test_acquire_high_rate_limit_returns_true(self):
        # Providers with rate >= 60 should skip throttling
        result = await RequestThrottle.acquire("ollama_chat/gemma4:e4b")
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_rate_limited_provider(self):
        # First call should succeed after token refill
        result = await RequestThrottle.acquire("openrouter/test-model", timeout=5.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_timeout_returns_false(self):
        # Exhaust tokens first
        _buckets["openrouter"]["tokens"] = 0.0
        result = await RequestThrottle.acquire("openrouter/test-model", timeout=0.01)
        assert result is False

    def test_reset_clears_state(self):
        _circuit_failures["openrouter"] = 10
        _circuit_open_since["openrouter"] = 999
        RequestThrottle.reset("openrouter")
        assert "openrouter" not in _circuit_failures
        assert "openrouter" not in _circuit_open_since

    def test_get_wait_time_high_rate_limit(self):
        wait = RequestThrottle.get_wait_time("ollama_chat/gemma4:e4b")
        assert wait == 0.0

    def test_get_wait_time_no_tokens(self):
        _buckets["openrouter"]["tokens"] = 0.0
        wait = RequestThrottle.get_wait_time("openrouter/test-model")
        assert wait > 0


class TestRequestThrottleCircuitBreaker:
    def setup_method(self):
        _buckets.clear()
        _circuit_failures.clear()
        _circuit_open_since.clear()

    @pytest.mark.asyncio
    async def test_circuit_opens_after_consecutive_failures(self):
        # Set circuit to be recently opened (within FAILURE_RESET_TIMEOUT)
        import time
        _circuit_failures["testprovider"] = 5
        _circuit_open_since["testprovider"] = time.monotonic()  # just now
        # Should immediately return False
        result = await RequestThrottle.acquire("testprovider/model", timeout=5.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_circuit_half_open_allows_probe(self):
        import time
        _circuit_failures["testprovider"] = 5
        _circuit_open_since["testprovider"] = time.monotonic() - 61  # past timeout
        # HALF_OPEN state - should allow through
        result = await RequestThrottle.acquire("testprovider/model", timeout=5.0)
        assert result is True


class TestRequestThrottleEdgeCases:
    def setup_method(self):
        _buckets.clear()
        _circuit_failures.clear()
        _circuit_open_since.clear()

    def test_unknown_provider_defaults_to_15(self):
        wait = RequestThrottle.get_wait_time("unknown/model")
        # Unknown providers get 15.0 rate limit, should have wait time when tokens=0
        _buckets["unknown"]["tokens"] = 0.0
        wait = RequestThrottle.get_wait_time("unknown/model")
        assert wait > 0

    def test_reset_clears_buckets(self):
        bucket_before = _buckets["testprovider"]
        bucket_before["tokens"] = 2.5
        RequestThrottle.reset("testprovider")
        # After reset, tokens should be 3.0
        assert _buckets["testprovider"]["tokens"] == 3.0

    @pytest.mark.asyncio
    async def test_acquire_ollama_always_true(self):
        # ollama and ollama_chat have rate 9999
        result = await RequestThrottle.acquire("ollama_chat/gemma4:e4b", timeout=0.001)
        assert result is True
        result = await RequestThrottle.acquire("ollama/qwen2:7b", timeout=0.001)
        assert result is True
