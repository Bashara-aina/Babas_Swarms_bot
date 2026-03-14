"""Shared pytest fixtures for Legion test suite."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(username="LegionBot", id=123))
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


@pytest.fixture
def mock_message(mock_bot):
    msg = AsyncMock()
    msg.bot = mock_bot
    msg.from_user = MagicMock(id=99999, username="testuser", first_name="Test")
    msg.chat = MagicMock(id=99999)
    msg.text = "/test"
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.reply = AsyncMock()
    return msg


@pytest.fixture
def mock_llm_response():
    """Mock a successful litellm acompletion response."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = "Mock LLM response"
    resp.choices[0].message.tool_calls = None
    resp.choices[0].finish_reason = "stop"
    resp.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    return resp


@pytest.fixture
def mock_acompletion(mock_llm_response):
    """Patch litellm.acompletion so tests run fully offline."""
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_llm_response) as m:
        yield m


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
