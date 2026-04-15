"""Tests for Legion v6 humanization layer."""

from __future__ import annotations

import pytest


def test_core_memory_set_get() -> None:
    from core.memory.tiers import CoreMemory

    cm = CoreMemory()
    cm.set("test_key", "test_value_12345")
    assert cm.get("test_key") == "test_value_12345"
    cm.delete("test_key")
    assert cm.get("test_key") is None


@pytest.mark.asyncio
async def test_archival_memory_store_and_search() -> None:
    from core.memory.tiers import ArchivalMemory

    am = ArchivalMemory()
    await am._init_db()
    await am.store(
        "Legion loves working on pose estimation research",
        summary="Legion's interests",
        tags=["test"],
        importance=0.9,
    )
    results = await am.search("pose estimation")
    assert len(results) > 0
    assert any("pose" in str(item["content"]).lower() for item in results)


@pytest.mark.asyncio
async def test_recall_memory_conversation_log() -> None:
    from core.memory.tiers import RecallMemory

    rm = RecallMemory()
    await rm.add("user", "What's the best optimizer for ResNet?", session_id="test_session")
    await rm.add("assistant", "AdamW is a solid baseline for ResNet.", session_id="test_session")
    recent = await rm.get_recent(n=10, session_id="test_session")
    assert len(recent) >= 2


def test_user_profile_persistence() -> None:
    from core.memory.user_profile import UserProfile

    up = UserProfile()
    up.add_known_fact("test_fact_xyz_123")
    facts = up.get("known_facts", [])
    assert "test_fact_xyz_123" in facts


@pytest.mark.asyncio
async def test_memory_manager_save_and_search() -> None:
    from core.memory.memory_manager import MemoryManager

    mm = MemoryManager()
    await mm.save("RTX 3060 GPU has 12GB VRAM", importance=0.9, tags=["hardware"])
    results = await mm.search("GPU VRAM")
    assert len(results) > 0


@pytest.mark.asyncio
async def test_memory_context_block_not_empty() -> None:
    from core.memory.memory_manager import MemoryManager

    mm = MemoryManager()
    block = await mm.build_context_block()
    assert len(block) > 50
    assert "Bashara" in block


async def test_temporal_graph_add_and_retrieve() -> None:
    from core.memory.temporal_graph import TemporalKnowledgeGraph

    graph = TemporalKnowledgeGraph()
    await graph.add_fact("Bashara", "uses_model", "gemma4:e4b", confidence=1.0)
    facts = await graph.get_current_facts("Bashara")
    assert any(f["predicate"] == "uses_model" for f in facts)


async def test_temporal_graph_fact_update_closes_old() -> None:
    from core.memory.temporal_graph import TemporalKnowledgeGraph

    graph = TemporalKnowledgeGraph()
    await graph.add_fact("Bashara", "test_pred_xyz", "old_value")
    await graph.add_fact("Bashara", "test_pred_xyz", "new_value")
    facts = await graph.get_current_facts("Bashara")
    current = [f for f in facts if f["predicate"] == "test_pred_xyz"]
    assert len(current) == 1
    assert current[0]["object"] == "new_value"


async def test_temporal_graph_history() -> None:
    from core.memory.temporal_graph import TemporalKnowledgeGraph

    graph = TemporalKnowledgeGraph()
    history = await graph.get_history("Bashara", "uses_local_model")
    assert isinstance(history, list)


def test_emotion_state_loads() -> None:
    from core.personality.emotion_engine import EmotionEngine

    engine = EmotionEngine()
    state = engine.state
    assert 0.0 <= state.curiosity <= 1.0
    assert 0.0 <= state.joy <= 1.0
    assert -1.0 <= state.pleasure <= 1.0


def test_emotion_updates_on_positive_message() -> None:
    from core.personality.emotion_engine import EmotionEngine

    engine = EmotionEngine()
    joy_before = engine.state.joy
    engine.update_from_interaction("that's perfect, thanks!", "You're welcome.")
    assert engine.state.joy >= joy_before


def test_emotion_updates_on_error_message() -> None:
    from core.personality.emotion_engine import EmotionEngine

    engine = EmotionEngine()
    frustration_before = engine.state.frustration
    engine.update_from_interaction("it's broken again, error on line 45", "Let me debug that.")
    assert engine.state.frustration >= frustration_before


def test_emotion_prompt_block_format() -> None:
    from core.personality.emotion_engine import EmotionEngine

    engine = EmotionEngine()
    block = engine.to_prompt_block()
    assert "EMOTIONAL STATE" in block


def test_personality_description_contains_key_traits() -> None:
    from core.personality.personality import LEGION_PERSONALITY

    desc = LEGION_PERSONALITY.to_description()
    assert "Legion" in desc
    assert "yes-man" in desc.lower() or "push back" in desc.lower()
    assert "Bashara" in desc


def test_personality_ocean_values_in_range() -> None:
    from core.personality.personality import LEGION_PERSONALITY

    p = LEGION_PERSONALITY
    for attr in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        val = getattr(p, attr)
        assert 0.0 <= val <= 1.0


def test_router_detects_computer_control() -> None:
    from core.autonomous_router import AutonomousRouter

    router = AutonomousRouter(None, None)
    result = router.analyze("open WhatsApp and check my messages")
    assert result.skill_name == "computer_control"


def test_router_detects_code_generation() -> None:
    from core.autonomous_router import AutonomousRouter

    router = AutonomousRouter(None, None)
    result = router.analyze("write a Python function to calculate cosine similarity")
    assert result.skill_name == "code_generation"


def test_router_detects_research() -> None:
    from core.autonomous_router import AutonomousRouter

    router = AutonomousRouter(None, None)
    result = router.analyze("research the latest transformer architectures 2026")
    assert result.skill_name == "deep_research"


def test_router_falls_back_to_conversation() -> None:
    from core.autonomous_router import AutonomousRouter

    router = AutonomousRouter(None, None)
    result = router.analyze("hey, how are you doing today?")
    assert result.skill_name == "conversation"


def test_router_confidence_range() -> None:
    from core.autonomous_router import AutonomousRouter

    router = AutonomousRouter(None, None)
    for msg in ["hello", "debug my code", "research AI agents", "open chrome"]:
        result = router.analyze(msg)
        assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_system_prompt_contains_all_sections() -> None:
    from core.memory.memory_manager import MemoryManager
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    from core.personality.emotion_engine import EmotionEngine
    from core.system_prompt_builder import SystemPromptBuilder

    class MockReflection:
        def get_opinions_block(self) -> str:
            return "[TEST OPINION]"

    mm = MemoryManager()
    em = EmotionEngine()
    tg = TemporalKnowledgeGraph()
    builder = SystemPromptBuilder(mm, em, tg, MockReflection())
    prompt = await builder.build()

    assert "Legion" in prompt
    assert "Bashara" in prompt
    assert len(prompt) > 200


def test_system_prompt_no_yes_man_phrases() -> None:
    from core.personality.personality import LEGION_PERSONALITY

    desc = LEGION_PERSONALITY.to_description()
    forbidden = ["certainly!", "of course!", "great question", "i'd be happy to"]
    for phrase in forbidden:
        assert phrase.lower() not in desc.lower()
