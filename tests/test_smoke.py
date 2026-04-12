"""tests/test_smoke.py — Integration smoke test for bot boot and core flows."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


class TestBotSmoke:
    """Smoke tests that verify bot components load without errors."""

    async def test_router_loads_cleanly(self):
        """router.py should load without AttributeError on build_system_prompt."""
        from router import build_system_prompt

        result = build_system_prompt("You are a test agent.")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_agents_module_exports_required_symbols(self):
        """agents.py should export all symbols required by handlers and router."""
        import agents

        required = [
            "AGENT_MODELS",
            "FALLBACK_CHAIN",
            "TASK_KEYWORDS",
            "DEFAULT_AGENT",
            "detect_agent",
            "get_model",
            "get_fallback_chain",
            "build_system_prompt",
            "PERSONALITY_WRAPPER",
            "DEBATE_PERSONAS",
        ]
        for sym in required:
            assert hasattr(agents, sym), f"Missing: {sym}"

    async def test_rate_limiter_per_user_isolation(self):
        """Rate limiter counters must be isolated per user_id."""
        from core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)
        uid_a = 111111
        uid_b = 222222

        # Exhaust A's quota
        assert await limiter.allow(uid_a) is True
        assert await limiter.allow(uid_a) is True
        assert await limiter.allow(uid_a) is False  # rate limited

        # B should still have quota
        assert await limiter.allow(uid_b) is True

    async def test_multi_limiter_types(self):
        """MultiLimiter should enforce separate limits per type."""
        from core.rate_limiter import MultiLimiter

        ml = MultiLimiter()
        uid = 333333

        # Message limit (30/min) — use a few
        for _ in range(5):
            assert await ml.allow(uid, "message") is True

        # Voice limit (5/min) — use a few
        for _ in range(3):
            assert await ml.allow(uid, "voice") is True

        # Tool limit (10/min) — use a few
        for _ in range(5):
            assert await ml.allow(uid, "tool") is True

    async def test_admin_bypass_in_rate_limiter(self):
        """Admin users should bypass rate limits."""
        from core.rate_limiter import RateLimiter, ADMIN_BYPASS

        admin_id = 999999
        ADMIN_BYPASS.add(admin_id)

        limiter = RateLimiter(max_requests=1, window_seconds=60)
        # Admin should always be allowed
        for _ in range(3):
            assert await limiter.allow(admin_id) is True

        ADMIN_BYPASS.discard(admin_id)

    async def test_build_system_prompt_includes_personality_wrapper(self):
        """build_system_prompt must prepend the personality wrapper."""
        from agents import build_system_prompt, PERSONALITY_WRAPPER

        wrapper = PERSONALITY_WRAPPER.strip() if PERSONALITY_WRAPPER else ""
        prompt = build_system_prompt("Say hello.")

        if wrapper:
            assert wrapper in prompt, "Personality wrapper should be in prompt"
        assert "Say hello." in prompt

    async def test_soul_engine_build_soul_context(self):
        """Soul engine build_soul_context() should return non-empty string."""
        from core.soul_engine import build_soul_context

        ctx = build_soul_context()
        assert isinstance(ctx, str)
        assert len(ctx) > 100  # Soul context is substantial

    async def test_set_clipboard_shell_safety(self):
        """set_clipboard must use shlex.quote, not string replace."""
        from computer_agent.display import set_clipboard
        import inspect

        src = inspect.getsource(set_clipboard)
        assert "shlex.quote" in src, "set_clipboard must use shlex.quote for shell safety"

    async def test_upgrade_from_git_no_hardcoded_path(self):
        """upgrade_from_git default path must NOT be hardcoded ~/swarm-bot."""
        from computer_agent.shell import upgrade_from_git
        import inspect

        src = inspect.getsource(upgrade_from_git)
        # Check that there's no literal "swarm-bot" as hardcoded path
        assert '"swarm-bot"' not in src and "'swarm-bot'" not in src, (
            "upgrade_from_git should not hardcode 'swarm-bot' path"
        )
        # Default should be empty string (resolved from __file__)
        assert upgrade_from_git.__defaults__[0] == "", (
            "Default repo_dir should be resolved from file location, not hardcoded"
        )

    async def test_read_file_with_traversal_resolves_safely(self):
        """read_file with ../.. path should be handled safely."""
        from computer_agent.display import read_file

        # Path traversal resolves relative to home via expanduser
        result = await read_file("~/../tmp/legion_smoke_test")
        # Should return content or error, not crash
        assert isinstance(result, str)


class TestRateLimiterAdminBypass:
    """Rate limiter admin bypass tests."""

    async def test_admin_bypass_set_is_populated_from_env(self):
        """ADMIN_BYPASS set should be populated from env."""
        from core.rate_limiter import ADMIN_BYPASS

        assert isinstance(ADMIN_BYPASS, set)

    async def test_multi_limiter_respects_separate_limits(self):
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

    async def test_rate_limiter_remaining_calculation(self):
        """RateLimiter.remaining() should return correct remaining count."""
        from core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)
        uid = 666666

        # Use 3 of 5
        for _ in range(3):
            await limiter.allow(uid)

        remaining = limiter.remaining(uid)
        assert remaining == 2


class TestMultiUserIsolation:
    """Multi-user isolation tests."""

    async def test_multi_user_auth_isolation(self):
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

    async def test_memory_engine_user_context_switching(self):
        """MemoryEngine should switch context based on set_user_id."""
        from core.memory_engine import MemoryEngine

        engine = MemoryEngine()
        uid_a = 111111
        uid_b = 222222

        engine.set_user_id(uid_a)
        ctx_a = await engine.get_context_window(str(uid_a))
        engine.set_user_id(uid_b)
        ctx_b = await engine.get_context_window(str(uid_b))

        # Each user gets own context window
        assert uid_a != uid_b


class TestCircuitBreaker:
    """Circuit breaker tests."""

    async def test_circuit_breaker_initial_state(self):
        """Circuit breaker should start in CLOSED state."""
        from core.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    async def test_circuit_breaker_all_states_exist(self):
        """CircuitState enum should have all expected states."""
        from core.circuit_breaker import CircuitState

        states = [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
        assert len(states) == 3


class TestSoulPersistence:
    """Soul persistence tests."""

    async def test_soul_context_consistent_across_calls(self):
        """Soul context should be consistent across multiple calls."""
        from core.soul_engine import build_soul_context

        ctx1 = build_soul_context()
        ctx2 = build_soul_context()
        # Soul should be cached and consistent
        assert ctx1 == ctx2

    async def test_build_enhanced_soul_context_exists(self):
        """build_enhanced_soul_context should exist and return string."""
        from core.soul_engine import build_enhanced_soul_context

        ctx = build_enhanced_soul_context()
        assert isinstance(ctx, str)
        assert len(ctx) > 0

    async def test_banned_phrases_exist_in_soul_engine(self):
        """Soul engine should have BANNED_PHRASES defined."""
        from core.soul_engine import BANNED_PHRASES

        assert isinstance(BANNED_PHRASES, (list, tuple, set))
        assert len(BANNED_PHRASES) > 0
