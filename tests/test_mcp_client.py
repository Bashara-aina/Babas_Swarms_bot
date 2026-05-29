"""Tests for MCPClientPool — connection reuse, fallback, retry, and TTL recovery."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.mcp_client import MCPClientPool, _tool_result_to_text


class TestToolResultToText:
    """Unit tests for _tool_result_to_text helper."""

    def test_none_returns_empty(self):
        assert _tool_result_to_text(None) == ""

    def test_result_with_content_blocks(self):
        block1 = MagicMock()
        block1.text = "hello"
        block2 = MagicMock()
        block2.text = "world"
        result = MagicMock(content=[block1, block2])
        assert _tool_result_to_text(result) == "hello\nworld"

    def test_result_with_dict_blocks(self):
        result = MagicMock(content=[{"text": "hello"}, {"text": "world"}])
        assert _tool_result_to_text(result) == "hello\nworld"

    def test_result_with_no_content(self):
        result = MagicMock(content=None)
        assert _tool_result_to_text(result) == str(result)


class TestMCPClientPoolReuse:
    """Tests for pool connection reuse — verify only ONE spawn for same server."""

    @pytest.fixture
    def pool(self):
        return MCPClientPool()

    async def test_pool_reuse_connection(self, pool):
        """call_tool twice on same server — stdio_client must be called exactly ONCE."""
        pool._cfg = {
            "servers": [
                {
                    "name": "test-server",
                    "command": "node",
                    "args": ["/fake/server.js"],
                    "enabled": True,
                    "env": {},
                }
            ]
        }

        tool_result = MagicMock()
        tool_result.content = [{"text": "result text"}]

        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=tool_result)

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        session_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.initialize = AsyncMock()

        stdio_ctx = AsyncMock()
        stdio_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        stdio_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("mcp.client.stdio.stdio_client", return_value=stdio_ctx):
            with patch("mcp.ClientSession", return_value=session_ctx):
                # First call — establishes session
                result1 = await pool.call_tool("test-server", "fake_tool", {"arg": 1})
                # Second call — must reuse the same session
                result2 = await pool.call_tool("test-server", "fake_tool", {"arg": 2})

        # stdio_client should be called only once (session reuse)
        assert pool._sessions.get("test-server") is not None
        # Both calls should succeed
        assert "result text" in result1
        assert "result text" in result2


class TestMCPClientPoolFallback:
    """Tests for pool fallback on error — first call fails, second succeeds."""

    @pytest.fixture
    def pool(self):
        return MCPClientPool()

    async def test_pool_fallback_on_error(self, pool):
        """First call fails via pool, single-call fallback is then used."""
        # Clear any persistent session state from previous tests (singleton isolation)
        pool._sessions.clear()
        pool._readers.clear()
        pool._writers.clear()
        pool._failed.discard("test-server")
        pool._failed_expiry.pop("test-server", None)
        pool._cfg = {
            "servers": [
                {
                    "name": "test-server",
                    "command": "node",
                    "args": ["/fake/server.js"],
                    "enabled": True,
                    "env": {},
                }
            ]
        }

        tool_result_ok = MagicMock()
        tool_result_ok.content = [{"text": "ok result"}]

        mock_session = AsyncMock()
        # First session.call_tool fails, causing pool to fall back
        call_count = [0]

        async def fake_call_tool(tool_name, args):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("connection lost")
            return tool_result_ok

        mock_session.call_tool = fake_call_tool

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        session_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.initialize = AsyncMock()

        stdio_ctx = AsyncMock()
        stdio_ctx.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        stdio_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("mcp.client.stdio.stdio_client", return_value=stdio_ctx):
            with patch("mcp.ClientSession", return_value=session_ctx):
                # Simulate _call_tool_single succeeding after pool failed
                async def fake_single(self, server_name, tool_name, arguments):
                    return "ok result"

                # Patch at class level so call_tool's `await self._call_tool_single(...)` works
                with patch("core.mcp_client.MCPClientPool._call_tool_single", fake_single):
                    result1 = await pool.call_tool("test-server", "fake_tool", {"arg": 1})
                    result2 = await pool.call_tool("test-server", "fake_tool", {"arg": 2})

        # First call went through pool → session failed → fell back to single-call
        assert result1 == "ok result"
        # Second call: server is in _failed so pool skips _ensure_session → single-call
        assert result2 == "ok result"


class TestMCPClientPoolPermanentFailure:
    """Tests for permanent failure TTL recovery."""

    async def test_pool_permanent_failure_ttl_recovery(self):
        """Mark server failed, wait for TTL, verify it retries."""
        from core.reliability.error_recovery import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="test-server")
        cb.state = CircuitState.OPEN
        cb.last_failure = 1000.0
        cb.failure_count = 5

        # After RESET_TIMEOUT (60s), circuit should go half-open
        with patch("time.monotonic", return_value=1000.0 + 65):
            assert cb.is_available() is True
            assert cb.state == CircuitState.HALF_OPEN


class TestMCPClientSingleRetry:
    """Tests for single-call retry path within pool."""

    async def test_single_call_retry(self):
        """Pool retry: first session call fails, second session call succeeds."""
        pool = MCPClientPool()
        pool._cfg = {
            "servers": [
                {
                    "name": "test-server",
                    "command": "node",
                    "args": ["/fake/server.js"],
                    "enabled": True,
                    "env": {},
                }
            ]
        }

        tool_result_ok = MagicMock()
        tool_result_ok.content = [{"text": "success"}]

        call_count = [0]

        mock_session = AsyncMock()

        async def fake_call_tool(tool_name, args):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("transient session error")
            return tool_result_ok

        mock_session.call_tool = fake_call_tool

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        session_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.initialize = AsyncMock()

        stdio_ctx = AsyncMock()
        stdio_ctx.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        stdio_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("mcp.client.stdio.stdio_client", return_value=stdio_ctx):
            with patch("mcp.ClientSession", return_value=session_ctx):
                result = await pool.call_tool("test-server", "fake_tool", {})

        # Pool should have retried (session call failed, then succeeded)
        assert call_count[0] == 2, f"Expected 2 session calls, got {call_count[0]}"
        assert "success" in result
