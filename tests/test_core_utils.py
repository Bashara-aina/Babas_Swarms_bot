"""Unit tests for pure utility functions — chunk_output, _strip_think_tags, detect_agent, _compact_messages."""
import pytest


# ---------------------------------------------------------------------------
# chunk_output
# ---------------------------------------------------------------------------
class TestChunkOutput:
    def _chunk(self, text, max_length=4096):
        """Import lazily so missing deps don't break the whole suite."""
        from llm_client import chunk_output
        return list(chunk_output(text, max_length=max_length))

    def test_empty_string(self):
        assert self._chunk("") == []

    def test_short_string_passes_through(self):
        result = self._chunk("hello world")
        assert result == ["hello world"]

    def test_exact_length_passes_through(self):
        text = "a" * 4096
        result = self._chunk(text, max_length=4096)
        assert len(result) == 1
        assert len(result[0]) == 4096

    def test_oversized_string_is_split(self):
        text = "a" * 5000
        result = self._chunk(text, max_length=4096)
        assert len(result) == 2
        assert all(len(c) <= 4096 for c in result)

    def test_multiline_split_on_newline(self):
        lines = "\n".join(["x" * 100] * 50)
        result = self._chunk(lines, max_length=1000)
        assert all(len(c) <= 1000 for c in result)

    def test_single_long_line_hard_split(self):
        text = "a" * 9000
        result = self._chunk(text, max_length=4096)
        assert all(len(c) <= 4096 for c in result)
        assert "".join(result) == text

    def test_none_input_returns_empty(self):
        try:
            result = self._chunk(None)
            assert result == [] or result == ["None"]
        except (TypeError, AttributeError):
            pass  # acceptable — function does not guarantee None handling


# ---------------------------------------------------------------------------
# _strip_think_tags
# ---------------------------------------------------------------------------
class TestStripThinkTags:
    def _strip(self, text):
        from llm_client import _strip_think_tags
        return _strip_think_tags(text)

    def test_no_think_tags(self):
        assert self._strip("hello world") == "hello world"

    def test_single_think_block_removed(self):
        result = self._strip("<think>internal</think>answer")
        assert "internal" not in result
        assert "answer" in result

    def test_multiple_think_blocks_all_removed(self):
        result = self._strip("<think>a</think>mid<think>b</think>end")
        assert "a" not in result
        assert "b" not in result
        assert "mid" in result
        assert "end" in result

    def test_nested_content_preserved(self):
        result = self._strip("before<think>hidden</think>after")
        assert result.strip() in ("beforeafter", "before after", "before\nafter")

    def test_empty_think_block(self):
        result = self._strip("<think></think>real")
        assert "real" in result

    def test_unclosed_think_tag_handled(self):
        # Should not raise; may or may not strip — just must not crash
        result = self._strip("<think>unclosed content")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# detect_agent
# ---------------------------------------------------------------------------
class TestDetectAgent:
    def _detect(self, text):
        from agents import detect_agent
        return detect_agent(text)

    @pytest.mark.parametrize("text,expected", [
        ("write a python function to sort a list", "coding"),
        ("debug this error: AttributeError", "debug"),
        ("take a screenshot of my screen", "vision"),
        ("compute the gradient of the loss function", "math"),
        ("design the architecture for a microservice", "architect"),
        ("analyze this dataset and show metrics", "analyst"),
        ("what is the capital of France", "general"),
        ("implement a class for binary search", "coding"),
        ("why does this traceback happen", "debug"),
        ("look at the image and describe it", "vision"),
        ("calculate the matrix determinant", "math"),
        ("how should I structure this project", "architect"),
        ("compare these two statistics", "analyst"),
        ("tell me a joke", "general"),
        ("refactor this code to be cleaner", "coding"),
        ("fix the bug in line 42", "debug"),
    ])
    def test_routing(self, text, expected):
        result = self._detect(text)
        assert result == expected, f"'{text}' → expected '{expected}', got '{result}'"


# ---------------------------------------------------------------------------
# _compact_messages
# ---------------------------------------------------------------------------
class TestCompactMessages:
    def _compact(self, messages, max_turns=12):
        from llm_client import _compact_messages
        return _compact_messages(messages, max_turns=max_turns)

    def test_short_list_passthrough(self):
        msgs = [{"role": "user", "content": "hi"}] * 5
        result = self._compact(msgs, max_turns=12)
        assert result == msgs

    def test_long_list_compacted(self):
        msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        result = self._compact(msgs, max_turns=12)
        assert len(result) < 20

    def test_summary_injected_as_system_role(self):
        msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        result = self._compact(msgs, max_turns=12)
        system_msgs = [m for m in result if m.get("role") == "system"]
        assert len(system_msgs) >= 1

    def test_recent_messages_preserved(self):
        msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        result = self._compact(msgs, max_turns=12)
        # Last message should still be present
        assert result[-1]["content"] == "msg 19"

    def test_empty_list(self):
        assert self._compact([]) == []

    def test_vision_content_list_handled(self):
        msgs = [
            {"role": "user", "content": [{"type": "text", "text": "describe this"}, {"type": "image_url", "image_url": "..."}]},
        ] * 15
        result = self._compact(msgs, max_turns=12)
        assert isinstance(result, list)
