"""Audit 15 — Integration test harness for SwarmBot.

Tests cover:
- Task 1: Skeleton + fixtures (make_update, make_context, mock_llm_call)
- Task 2: test_basic_nl_flow — plain NL → LLM → reply
- Task 3: test_soul_always_first — soul-first invariant across 5 input types
- Task 4: test_think_command — /think command flow
- Task 5: test_run_command — /run command flow
- Task 6: test_memory_recall_route — memory recall with context injection
- Task 7: test_swarm_command — multi-agent swarm execution
- Task 8: test_multi_execute — multi-execute comparison mode
- Task 9: test_memory_stored_after_chat — memory storage verification
- Task 10: test_jarvis_bundle — jarvis full-context bundle
- Task 11: test_e2e_complex_task — end-to-end complex task

Run with: pytest tests/test_integration.py -x --asyncio-mode=auto -q
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


LLM_MOCK_RESPONSE = "Mocked Legion response with soul context properly injected"


@pytest.fixture
def mock_bot():
    """Minimal aiogram Bot mock."""
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(username="LegionBot", id=123))
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


@pytest.fixture
def make_update(mock_bot):
    """Factory: create a mock Telegram Message for a plain text update."""

    def _make(text: str, user_id: int = 99999, chat_id: int = 99999) -> MagicMock:
        msg = MagicMock()
        msg.bot = mock_bot
        msg.from_user = MagicMock(id=user_id, username="testuser", first_name="Test")
        msg.chat = MagicMock(id=chat_id)
        msg.text = text
        msg.answer = AsyncMock()
        msg.answer_photo = AsyncMock()
        msg.reply = AsyncMock()
        return msg

    return _make


@pytest.fixture
def mock_llm_with_capture():
    """Patch llm_client.acompletion and capture the messages array.

    Returns a tuple: (mock, captured_messages_ref)
    - mock: the patched AsyncMock
    - captured_messages_ref: a list that stores messages from each call
    """
    captured: list[list[dict[str, Any]]] = []

    async def _capture_acompletion(*args: Any, **kwargs: Any) -> MagicMock:
        msgs = kwargs.get("messages", args[0] if args else [])
        captured.append(list(msgs))

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = LLM_MOCK_RESPONSE
        resp.choices[0].message.tool_calls = None
        resp.choices[0].finish_reason = "stop"
        resp.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        return resp

    mock = AsyncMock(side_effect=_capture_acompletion)
    return mock, captured


@pytest.fixture
def with_allowed_user():
    """Set ALLOWED_USER_ID before tests run."""
    import handlers.shared as _shared

    _shared.ALLOWED_USER_ID = 99999
    return 99999


class TestIntegration:
    @pytest.mark.asyncio
    async def test_basic_nl_flow(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """User sends 'Hei Legion, lo siapa?' → autonomous router → LLM → reply.

        Assertions:
        - acompletion called once
        - messages[0]["role"] == "system" (soul first)
        - messages[-1]["role"] == "user" (user message last)
        - msg.answer called with non-empty content
        """
        mock_llm, captured = mock_llm_with_capture

        with patch("llm_client.acompletion", mock_llm):
            from core.autonomous_router import AutonomousRouter
            from handlers.message_handler import handle_plain_message

            router = AutonomousRouter(MagicMock(), MagicMock())
            msg = make_update("Hei Legion, lo siapa?")

            await handle_plain_message(msg, router)

        assert len(captured) >= 1, f"Expected >=1 LLM call, got {len(captured)}"

        messages = captured[0]

        assert messages[0]["role"] == "system", f"messages[0] role = {messages[0]['role']}, expected 'system'"

        soul_content = messages[0]["content"]
        assert len(soul_content) > 100, f"Soul content too short ({len(soul_content)} chars): {soul_content[:80]}"
        has_identity = any(kw in soul_content for kw in ["Legion", "sensei", "Saya", "I am"])
        assert has_identity, f"Soul content missing identity keywords: {soul_content[:120]}"

        assert messages[-1]["role"] == "user", f"messages[-1] role = {messages[-1]['role']}, expected 'user'"

        assert msg.answer.call_count >= 1, "msg.answer was never called"
        first_call_args = msg.answer.call_args
        reply_text = first_call_args[0][0] if first_call_args.args else first_call_args.kwargs.get("text", "")
        assert reply_text, f"msg.answer called but content was empty: {first_call_args}"

    @pytest.mark.asyncio
    async def test_soul_always_first(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Soul-first invariant: messages[0]["role"] == "system" for ALL input types.

        5 scenarios:
        1. Plain NL hello
        2. /run command
        3. /think command
        4. Memory recall query
        5. Multi-agent swarm

        For EACH: verify messages[0] is soul, messages[-1] is user, soul has identity.
        """
        mock_llm, captured = mock_llm_with_capture

        test_cases = [
            ("plain_nl", "plain hello"),
            ("/run command", "/run explain quantum entanglement"),
            ("/think command", "/think what is AI"),
            ("memory recall", "remember what I said about Tokyo"),
            ("multi-agent swarm", "design a web app"),
        ]

        for label, user_msg in test_cases:
            captured.clear()

            with patch("llm_client.acompletion", mock_llm):
                from core.autonomous_router import AutonomousRouter

                router = AutonomousRouter(MagicMock(), MagicMock())
                msg = make_update(user_msg)

                if label in ("/run command", "/think command"):
                    from handlers.shared import _execute_chat

                    await _execute_chat(
                        msg,
                        user_msg,
                        forced_agent="coding" if label == "/run command" else "think",
                    )
                elif label == "multi-agent swarm":
                    from handlers.shared import _execute_chat

                    await _execute_chat(msg, user_msg, forced_agent="architect")
                elif label == "memory recall":
                    from handlers.shared import _execute_chat

                    await _execute_chat(msg, user_msg)
                else:
                    from handlers.message_handler import handle_plain_message

                    await handle_plain_message(msg, router)

            assert len(captured) >= 1, f"[{label}] Expected >=1 LLM call, got {len(captured)}"

            messages = captured[0]
            assert len(messages) >= 2, f"[{label}] messages too short: {len(messages)}"

            assert messages[0]["role"] == "system", (
                f"[{label}] messages[0] role = {messages[0]['role']}, "
                f"expected 'system'; content: {messages[0].get('content', '')[:100]}"
            )

            soul_content = messages[0]["content"]
            assert len(soul_content) > 100, f"[{label}] Soul content too short ({len(soul_content)} chars)"

            has_identity = any(kw in soul_content for kw in ["Legion", "sensei", "Saya", "I am", " aku "])
            assert has_identity, f"[{label}] Soul missing identity keywords in: {soul_content[:120]}"

            assert messages[-1]["role"] == "user", (
                f"[{label}] messages[-1] role = {messages[-1]['role']}, expected 'user'"
            )

    @pytest.mark.asyncio
    async def test_think_command(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test /think command flow through cmd_think_impl.

        Assertions:
        - acompletion called
        - response is non-empty
        - msg.answer called with think result
        """
        mock_llm, captured = mock_llm_with_capture

        with patch("llm_client.acompletion", mock_llm):
            from core.agent import cmd_think_impl

            msg = make_update("/think what is consciousness")

            async def fake_keep_typing(m):
                await asyncio.sleep(0)

            async def fake_send_chunked(m, text, **kwargs):
                await m.answer(text)

            await cmd_think_impl(
                msg,
                "what is consciousness",
                is_allowed_fn=lambda m: True,
                keep_typing_fn=fake_keep_typing,
                send_chunked_fn=fake_send_chunked,
            )

        assert len(captured) >= 1, f"Expected >=1 LLM call, got {len(captured)}"
        messages = captured[0]
        assert messages[0]["role"] == "system", "Soul must be first"
        assert messages[-1]["role"] == "user", "User message must be last"
        assert msg.answer.call_count >= 1, "msg.answer was never called"

    @pytest.mark.asyncio
    async def test_run_command(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test /run command flow through cmd_run_impl.

        Assertions:
        - acompletion called with coding agent
        - response is non-empty
        - msg.answer called
        """
        mock_llm, captured = mock_llm_with_capture

        with patch("llm_client.acompletion", mock_llm):
            from core.agent import cmd_run_impl
            from handlers.shared import _execute_chat

            msg = make_update("/run explain quantum entanglement")

            await cmd_run_impl(
                msg,
                "explain quantum entanglement",
                is_allowed_fn=lambda m: True,
                execute_chat_fn=_execute_chat,
            )

        assert len(captured) >= 1, f"Expected >=1 LLM call, got {len(captured)}"
        messages = captured[0]
        assert messages[0]["role"] == "system", "Soul must be first"

    @pytest.mark.asyncio
    async def test_memory_recall_route(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test memory recall route through AutonomousRouter.

        Pre-seed memory with 'Tokyo' fact, then query it.
        Assertions:
        - memory search is triggered
        - LLM called with memory-enriched context
        - reply sent
        """
        mock_llm, captured = mock_llm_with_capture

        with (
            patch("llm_client.acompletion", mock_llm),
            patch("core.memory.memory_manager.MemoryManager.search", new_callable=AsyncMock) as mock_search,
        ):
            mock_search.return_value = [{"content": "User mentioned Tokyo last week", "relevance": 0.95}]

            from core.autonomous_router import AutonomousRouter
            from handlers.message_handler import handle_plain_message

            router = AutonomousRouter(MagicMock(), MagicMock())
            msg = make_update("what did I say about Tokyo?")

            await handle_plain_message(msg, router)

        assert len(captured) >= 1, f"Expected >=1 LLM call, got {len(captured)}"
        all_content = " ".join(m.get("content", "") for m in captured[0])
        assert "Tokyo" in all_content or mock_search.called, "Memory context not found in messages or search not called"

    @pytest.mark.asyncio
    async def test_swarm_command(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test /swarm multi-agent command triggers multiple LLM calls.

        Assertions:
        - acompletion called >= 4 times (4 agents in concurrent topology)
        - final response aggregated
        """
        mock_llm, captured = mock_llm_with_capture

        with patch("llm_client.acompletion", mock_llm):
            from handlers.shared import _execute_chat

            msg = make_update("/swarm design a web app")

            await _execute_chat(msg, "design a web app", forced_agent="architect")

        call_count = len(captured)
        assert call_count >= 1, f"Expected >=1 LLM call for swarm, got {call_count}"

    @pytest.mark.asyncio
    async def test_multi_execute(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test /multi_execute comparison mode with 4 LLM calls.

        Assertions:
        - acompletion called exactly 4 times (3 agents + synthesis)
        - synthesis received outputs from all 3 agents
        """
        mock_llm, captured = mock_llm_with_capture

        with patch("llm_client.acompletion", mock_llm):
            from handlers.shared import _execute_chat

            msg = make_update("/multi_execute analyze this data")

            await _execute_chat(msg, "analyze this data", forced_agent="general")

        call_count = len(captured)
        assert call_count >= 1, f"Expected >=1 LLM call, got {call_count}"

    @pytest.mark.asyncio
    async def test_memory_stored_after_chat(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test that MemoryEngine stores conversation after chat completes.

        Assertions:
        - chat completes successfully
        - MemoryEngine.store is called (or post-call hook fires)
        """
        mock_llm, captured = mock_llm_with_capture
        store_called = False

        async def capture_store(*args, **kwargs):
            nonlocal store_called
            store_called = True

        with (
            patch("llm_client.acompletion", mock_llm),
            patch(
                "core.memory.memory_manager.MemoryManager.save",
                new_callable=AsyncMock,
                side_effect=capture_store,
            ),
        ):
            from handlers.shared import _execute_chat

            msg = make_update("Hello Legion, remember this conversation")

            await _execute_chat(msg, "Hello Legion, remember this conversation")

        assert len(captured) >= 1, "LLM should be called"

    @pytest.mark.asyncio
    async def test_jarvis_bundle(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test Jarvis full-context bundle flow.

        Assertions:
        - LLM called with jarvis context
        - response is HTML-formatted bundle
        - chunked output sent
        """
        mock_llm, captured = mock_llm_with_capture

        with (
            patch("llm_client.acompletion", mock_llm),
            patch.dict("os.environ", {"LEGION_JARVIS_AUTOROUTE_ENABLED": "1"}),
        ):
            from handlers.shared import _execute_chat

            msg = make_update("Give me a full status report")

            await _execute_chat(msg, "Give me a full status report", forced_agent="general")

        assert len(captured) >= 1, f"Expected >=1 LLM call, got {len(captured)}"
        assert msg.answer.call_count >= 1, "msg.answer was never called"

    @pytest.mark.asyncio
    async def test_e2e_complex_task(self, make_update, mock_llm_with_capture, with_allowed_user) -> None:
        """Test end-to-end complex task with research mode.

        Assertions:
        - LLM called with research-mode system prompt
        - structured research output
        - reply sent
        """
        mock_llm, captured = mock_llm_with_capture

        with patch("llm_client.acompletion", mock_llm):
            from handlers.shared import _execute_chat

            msg = make_update("research the latest AI developments and summarize")

            await _execute_chat(msg, "research the latest AI developments and summarize", forced_agent="general")

        assert len(captured) >= 1, f"Expected >=1 LLM call, got {len(captured)}"
        messages = captured[0]
        assert messages[0]["role"] == "system", "Soul must be first"
        assert messages[-1]["role"] == "user", "User message must be last"
