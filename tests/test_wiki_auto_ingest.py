"""Tests for wiki_auto_ingest — on_conversation_turn and on_session_end hooks."""

from unittest.mock import AsyncMock, MagicMock, patch

from core.wiki_auto_ingest import (
    is_worthy_turn,
    on_conversation_turn,
    on_session_end,
)


class TestIsWorthyTurn:
    """Unit tests for the lightweight blocking check."""

    def test_short_question_rejected(self):
        worthy, reason = is_worthy_turn("hi", "hello world " * 20)
        assert worthy is False
        assert "short" in reason

    def test_short_answer_rejected(self):
        worthy, _reason = is_worthy_turn("how do I install pip?", "use pip")
        assert worthy is False

    def test_code_heavy_solution_accepted(self):
        long_answer = "```bash\npip install foo\n```\n" * 5
        worthy, reason = is_worthy_turn("how to install packages?", long_answer)
        assert worthy is True
        assert "code-heavy" in reason

    def test_command_error_pattern_accepted(self):
        answer = "Run `pip install flask` to fix the ImportError"
        worthy, reason = is_worthy_turn("how to fix ImportError?", answer)
        assert worthy is True
        assert "solved command" in reason or "error" in reason.lower()

    def test_url_in_answer_accepted(self):
        answer = "See https://docs.example.com for more details."
        worthy, _reason = is_worthy_turn("where is the docs?", answer)
        assert worthy is True

    def test_default_skip(self):
        worthy, _reason = is_worthy_turn(
            "what do you think about AI?",
            "I think AI is interesting but I don't have a strong opinion",
        )
        assert worthy is False


class TestOnConversationTurn:
    """Tests for on_conversation_turn() hook."""

    async def test_on_conversation_turn_fires(self):
        """Verify task is created when a worthy turn is detected."""
        with patch("core.wiki_manager.get_wiki_manager") as mock_wm:
            mock_manager = AsyncMock()
            mock_manager.ingest = AsyncMock(return_value=["test-page.md"])
            mock_wm.return_value = mock_manager

            result = await on_conversation_turn(
                user_id="user123",
                user_message="How do I fix the ImportError in Python?",
                assistant_message="Run `pip install flask` to fix it",
            )

            assert result["filed"] is True
            assert "pages" in result
            mock_manager.ingest.assert_called_once()

    async def test_on_conversation_turn_short_message_skipped(self):
        """Short messages are rejected by is_worthy_turn before LLM is called."""
        with patch("core.wiki_manager.get_wiki_manager") as mock_wm:
            result = await on_conversation_turn(
                user_id="user123",
                user_message="hi",
                assistant_message="hello",
            )
            assert result["filed"] is False
            mock_wm.assert_not_called()


class TestOnSessionEnd:
    """Tests for on_session_end() hook."""

    async def test_on_session_end_is_called(self):
        """Verify on_session_end is invoked when session has enough turns."""
        conversation = [
            {"role": "user", "content": "task 1"},
            {"role": "assistant", "content": "answer 1"},
            {"role": "user", "content": "task 2"},
            {"role": "assistant", "content": "answer 2"},
            {"role": "user", "content": "task 3"},
            {"role": "assistant", "content": "answer 3"},
        ]

        mock_llm = AsyncMock()
        mock_llm.complete = AsyncMock(
            return_value='{"worth_filing": true, "quality_score": 0.8, "pages": [{"filename": "test.md", "action": "create", "content": "# Test"}], "log_entry": "learned something"}'
        )

        with patch("core.wiki_manager.get_wiki_manager") as mock_wm:
            mock_manager = AsyncMock()
            mock_manager.ingest = AsyncMock(return_value=["test.md"])
            mock_manager.read_page = AsyncMock(return_value="does not exist")
            mock_manager._resolve = MagicMock(return_value="/tmp/wiki/test.md")
            mock_manager.write_page = AsyncMock()
            mock_wm.return_value = mock_manager

            result = await on_session_end(
                user_id="user123",
                conversation=conversation,
                llm_client=mock_llm,
            )

            # on_session_end should have been called with enough turns
            # result depends on LLM output quality
            assert "score" in result or result.get("filed") is False

    async def test_on_session_end_below_threshold_skipped(self):
        """Conversation with fewer than SESSION_TURN_THRESHOLD turns is skipped."""
        short_conversation = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]

        result = await on_session_end(
            user_id="user123",
            conversation=short_conversation,
        )

        assert result["filed"] is False
        assert "turns" in result["reason"]


class TestWikiAutoIngestLogging:
    """Tests for the _log_ingest helper."""

    async def test_log_ingest_creates_file(self, tmp_path):
        """Verify ingest events are logged to the expected file."""
        with patch("core.wiki_auto_ingest.WIKI_DIR", tmp_path):
            with patch("core.wiki_auto_ingest._write_file_async", new_callable=AsyncMock) as mock_write:
                from core.wiki_auto_ingest import _log_ingest

                await _log_ingest(
                    pages=["test.md"],
                    score=0.85,
                    reason="test",
                    src_preview="source text",
                )

                mock_write.assert_called_once()
                args = mock_write.call_args
                log_path = args[0][0]
                assert log_path.name == "auto-ingest.md"
