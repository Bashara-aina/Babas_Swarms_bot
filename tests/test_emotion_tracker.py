from __future__ import annotations

from core.emotion_tracker import emotion_prompt_block


def test_emotion_prompt_block_non_empty() -> None:
    block = emotion_prompt_block()
    assert isinstance(block, str)
    assert "EMOTION" in block.upper() or "neutral" in block.lower()
