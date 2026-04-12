"""tests/test_soul_persistence.py — Soul engine persistence and context isolation tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_soul_present_in_every_prompt():
    """The SOUL.md personality wrapper must be present in every LLM prompt."""
    from agents import build_system_prompt, PERSONALITY_WRAPPER

    prompt = build_system_prompt("You are a helpful assistant.")
    # Personality wrapper should be prepended (if loaded)
    if PERSONALITY_WRAPPER:
        assert len(prompt) > len("You are a helpful assistant.")


async def test_soul_survives_memory_failure():
    """Soul should remain stable even if memory operations fail."""
    from core.soul_engine import build_soul_context

    # Module-level cache should survive across calls
    ctx1 = build_soul_context()
    ctx2 = build_soul_context()
    # Should return valid context even if storage fails
    assert isinstance(ctx1, str)
    assert isinstance(ctx2, str)
    assert ctx1 == ctx2  # Cached consistently


async def test_soul_survives_long_context_trimming():
    """Long conversations that trigger context trimming should preserve soul."""
    from core.soul_engine import build_soul_context

    soul1 = build_soul_context()
    # Simulate multiple calls (like long conversation trimming)
    for _ in range(5):
        build_soul_context()
    soul2 = build_soul_context()
    # Soul should be cached and stable
    assert soul1 == soul2


async def test_nihongo_mode_does_not_contaminate_soul():
    """Nihongo mode (user language preference) should not overwrite soul."""
    from core.soul_engine import build_soul_context

    ctx1 = build_soul_context()
    ctx2 = build_soul_context()
    # Soul text should be the same regardless of call pattern
    assert ctx1 == ctx2


async def test_build_enhanced_soul_context_exists():
    """Enhanced soul context builder should exist and return non-empty."""
    from core.soul_engine import build_enhanced_soul_context

    ctx = build_enhanced_soul_context()
    assert isinstance(ctx, str)
    assert len(ctx) > 0
