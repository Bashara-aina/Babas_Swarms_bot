"""Screenpipe tool — mocked HTTP."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("aiohttp")


@pytest.mark.asyncio
async def test_screenpipe_disabled_returns_empty() -> None:
    os.environ["SCREENPIPE_ENABLED"] = "0"
    from tools.screenpipe_tool import ScreenpipeTool

    t = ScreenpipeTool(base_url="http://127.0.0.1:3030")
    out = await t.search("test")
    assert out == ""


@pytest.mark.asyncio
async def test_screenpipe_parses_response() -> None:
    os.environ["SCREENPIPE_ENABLED"] = "1"
    from tools.screenpipe_tool import ScreenpipeTool

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "data": [
                {
                    "timestamp": "2026-04-08T12:00:00",
                    "type": "OCR",
                    "content": {"text": "hello world", "app_name": "terminal"},
                }
            ]
        }
    )
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_cm)
    mock_sess_cm = MagicMock()
    mock_sess_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_sess_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("tools.screenpipe_tool.aiohttp.ClientSession", return_value=mock_sess_cm):
        t = ScreenpipeTool(base_url="http://127.0.0.1:3030")
        out = await t.search("q")
        assert "SCREENPIPE" in out
        assert "terminal" in out
        assert "hello" in out
