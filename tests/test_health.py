"""Tests for the health HTTP endpoint."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


class TestHealthHandler:
    @pytest.mark.asyncio
    async def test_health_returns_200(self):
        try:
            from aiohttp.test_utils import make_mocked_request
            from core.health import _health_handler
            request = make_mocked_request("GET", "/health")
            response = await _health_handler(request)
            assert response.status == 200
        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_health_response_body(self):
        try:
            import json
            from aiohttp.test_utils import make_mocked_request
            from core.health import _health_handler
            request = make_mocked_request("GET", "/health")
            response = await _health_handler(request)
            body = json.loads(response.text)
            assert body["status"] == "ok"
            assert "bot" in body
        except ImportError:
            pytest.skip("aiohttp not available")
