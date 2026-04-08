"""Tests for mem0 semantic façade (core/memory_manager.py) and prompt formatting."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_legion_semantic_memory_search_formats_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_mem0_search(user_id: str, query: str, limit: int = 10) -> list[dict]:
        assert user_id == "42"
        assert "hello" in query
        _ = limit
        return [
            {"memory": "User prefers dark mode", "score": 0.9},
            {"content": "  ", "score": 0.1},
            {"text": "Works on Ubuntu", "score": 0.5},
        ]

    monkeypatch.setattr("tools.mem0_client.mem0_search", fake_mem0_search)

    from core.memory_manager import LegionSemanticMemory

    out = await LegionSemanticMemory().search_memories("hello world", "42", limit=5)
    assert "User prefers dark mode" in out
    assert "Works on Ubuntu" in out
    assert len(out) == 2


@pytest.mark.asyncio
async def test_legion_semantic_memory_save_fallback_per_message(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict]] = []

    async def fake_add(user_id: str, content: str, metadata: dict | None = None) -> None:
        calls.append((user_id, content, metadata or {}))

    monkeypatch.setattr("tools.mem0_client.get_mem0", lambda: None)
    monkeypatch.setattr("tools.mem0_client.mem0_add", fake_add)

    from core.memory_manager import LegionSemanticMemory

    await LegionSemanticMemory().save_memory(
        [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "yo"},
        ],
        "99",
    )
    assert len(calls) == 2
    assert calls[0][0] == "99" and calls[0][1] == "hi"
    assert calls[1][1] == "yo"


def test_format_retrieved_memories_section_empty() -> None:
    from core.system_prompt_builder import format_retrieved_memories_section

    assert format_retrieved_memories_section([]) == ""


def test_format_retrieved_memories_section_heading() -> None:
    from core.system_prompt_builder import format_retrieved_memories_section

    block = format_retrieved_memories_section(["alpha", "beta"], max_items=5)
    assert "## RETRIEVED MEMORIES FROM PAST CONVERSATIONS" in block
    assert "- alpha" in block
    assert "- beta" in block
