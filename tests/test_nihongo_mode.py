"""Tests for Nihongo Mode — isolated Japanese teacher plugin."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode
from skills.nihongo.sensei_prompt import build_sensei_system_prompt
from skills.nihongo.furigana import annotate_japanese, extract_japanese_only
from skills.nihongo.constants import N5_VOCAB_SAMPLE, N5_GRAMMAR_PATTERNS

TEST_USER_ID = 99999


def test_isolation_when_off():
    NihongoModeManager.deactivate(TEST_USER_ID)
    assert NihongoModeManager.is_active(TEST_USER_ID) == False
    print("✅ Isolation: mode OFF is clean")


def test_activate_and_deactivate():
    session = NihongoModeManager.activate(TEST_USER_ID, NihongoSubMode.CHAT)
    assert session.active == True
    assert NihongoModeManager.is_active(TEST_USER_ID) == True

    NihongoModeManager.deactivate(TEST_USER_ID)
    assert NihongoModeManager.is_active(TEST_USER_ID) == False
    print("✅ Toggle ON/OFF works")


def test_sensei_prompt_no_legion_content():
    session = NihongoModeManager.activate(TEST_USER_ID)
    prompt = build_sensei_system_prompt(session)

    assert "Sensei" in prompt
    assert "Bashara" in prompt
    assert "N5" in prompt

    legion_system_markers = ["SOUL", "MASTER_PROMPT", "Soul Engine"]
    for marker in legion_system_markers:
        assert marker not in prompt, f"Legion system content leaked: {marker}"

    print("✅ Sensei prompt is fully isolated from Legion")


def test_furigana_annotation():
    try:
        import pykakasi
    except ImportError:
        print("⚠️ pykakasi not installed, skipping furigana test")
        return

    result = annotate_japanese("学生")
    assert "学生" in result
    print(f"✅ Furigana: {result}")


def test_extract_japanese_only():
    mixed = "Ini adalah 学生 (がくせい) yang belajar di sini."
    jp_only = extract_japanese_only(mixed)
    assert "学生" in jp_only
    assert "Ini" not in jp_only
    print(f"✅ Japanese extraction: {jp_only}")


def test_sub_modes():
    for mode in NihongoSubMode:
        session = NihongoModeManager.activate(TEST_USER_ID, mode)
        prompt = build_sensei_system_prompt(session)
        assert "Sensei" in prompt
    print("✅ All sub-modes generate valid prompts")


def test_exchange_counter():
    NihongoModeManager.activate(TEST_USER_ID)
    for i in range(5):
        count = NihongoModeManager.increment_exchange(TEST_USER_ID)
    assert count == 5
    print("✅ Exchange counter works")


def test_n5_vocab_loaded():
    assert len(N5_VOCAB_SAMPLE) > 0
    assert N5_VOCAB_SAMPLE[0]["word"] == "学生"
    print(f"✅ N5 vocab loaded: {len(N5_VOCAB_SAMPLE)} words")


def test_n5_grammar_loaded():
    assert len(N5_GRAMMAR_PATTERNS) > 0
    assert N5_GRAMMAR_PATTERNS[0]["pattern"] == "は"
    print(f"✅ N5 grammar loaded: {len(N5_GRAMMAR_PATTERNS)} patterns")


def test_mode_settings():
    session = NihongoModeManager.activate(TEST_USER_ID, NihongoSubMode.CHAT)
    assert session.show_furigana == True
    assert session.show_romaji == True
    assert session.slow_speech == True

    NihongoModeManager.toggle_furigana(TEST_USER_ID)
    assert session.show_furigana == False

    NihongoModeManager.toggle_romaji(TEST_USER_ID)
    assert session.show_romaji == False

    NihongoModeManager.toggle_slow_speech(TEST_USER_ID)
    assert session.slow_speech == False

    print("✅ Mode settings (furigana, romaji, slow_speech) toggle correctly")


# =============================================================================
# NEW COMPONENT TESTS (NIHONGO MODE v2.0)
# =============================================================================


def test_sensei_soul_mood_tracking():
    """Test SenseiSoul mood tracking and adjustment."""
    from skills.nihongo.sensei_soul import SenseiSoul

    soul = SenseiSoul(user_id=TEST_USER_ID)
    assert soul.get_mood().enthusiasm > 0

    # Initial patience should be higher after mistake (patience > enthusiasm)
    initial_enthusiasm = soul.get_mood().enthusiasm
    initial_patience = soul.get_mood().patience

    soul.adjust_mood_on_outcome(correct=False)
    assert soul.get_mood().patience >= initial_patience

    # After correct, enthusiasm should increase
    soul.adjust_mood_on_outcome(correct=True)
    assert soul.get_mood().enthusiasm > initial_enthusiasm

    print("✅ SenseiSoul mood tracking works")


def test_mastery_gate_bloom_classification():
    """Test MasteryGate Bloom level classification."""
    from skills.nihongo.mastery_gate import MasteryGate, BloomLevel

    gate = MasteryGate()

    # Test REMEMBER level classification
    level = gate.classify_question("Apa arti 学生?")
    assert level == BloomLevel.REMEMBER

    # Test UNDERSTAND level
    level = gate.classify_question("Jelaskan tentang 学生")
    assert level == BloomLevel.UNDERSTAND

    # Test APPLY level
    level = gate.classify_question("Buat kalimat dengan 学生")
    assert level == BloomLevel.APPLY

    # Test sigma score is in valid range
    sigma = gate.evaluate_mastery(user_id=TEST_USER_ID, item="nonexistent")[1]
    assert 0 <= sigma <= 3.0

    # Test mastery record
    record = gate.record_attempt(TEST_USER_ID, "test_item", correct=True, level=BloomLevel.REMEMBER)
    assert record.attempts == 1
    assert record.sigma > 0

    print("✅ MasteryGate Bloom classification works")


def test_immersion_world_scenarios():
    """Test ImmersionWorld location scenarios."""
    from skills.nihongo.immersion_world import ImmersionWorld, Location

    world = ImmersionWorld()

    # Test scenario generation
    scenario = world.generate_scenario(Location.NARITA_AIRPORT, {"situation": "check_in"})
    assert scenario.title is not None

    # Test Narita vocab
    vocab = world.get_narita_vocab()
    assert len(vocab) > 0

    # Test campus phrases
    campus = world.get_campus_phrases()
    assert len(campus) > 0

    # Test location enum has values
    assert Location.NARITA_AIRPORT.value == "narita_airport"

    print("✅ ImmersionWorld scenarios work")


def test_srs_engine_sm2_algorithm():
    """Test SRSEngine SM-2 algorithm implementation."""
    from skills.nihongo.srs_engine import SRSEngine, SRSCard

    engine = SRSEngine()

    # Test add card
    engine.add_card(user_id=TEST_USER_ID, item="学生")
    card = engine.get_due_cards(user_id=TEST_USER_ID)[0]
    assert card.item_id == "学生"

    # Test record review
    card = engine.record_review(user_id=TEST_USER_ID, item="学生", quality=4)
    assert card.repetitions == 1
    assert card.interval > 0

    # Test mastery percentage calculation
    pct = engine.get_mastery_percentage(user_id=TEST_USER_ID)
    assert 0.0 <= pct <= 100.0

    # Test failed items
    failed = engine.get_failed_items(user_id=TEST_USER_ID)
    assert isinstance(failed, list)

    print("✅ SRSEngine SM-2 algorithm works")


def test_cultural_intel_notes():
    """Test CulturalIntel cultural notes."""
    from skills.nihongo.cultural_intel import CulturalIntel, CulturalNote, ImportanceLevel

    intel = CulturalIntel()

    # Test keigo awareness
    keigo = intel.get_keigo_awareness("N5")
    assert keigo is not None

    # Test cultural notes for topic
    notes = intel.get_cultural_notes_for_topic("bowing")
    assert len(notes) > 0
    assert all(isinstance(n, CulturalNote) for n in notes)

    # Test importance level
    note = notes[0]
    assert note.importance_level in [ImportanceLevel.HIGH, ImportanceLevel.MEDIUM, ImportanceLevel.LOW]

    # Test situation culture
    culture = intel.get_situation_culture("university", "meeting_professor")
    assert culture is None or isinstance(culture, CulturalNote)

    # Test formatting
    formatted = intel.format_cultural_note(note)
    assert formatted is not None

    print("✅ CulturalIntel notes work")


def test_proactive_sensei_nudge():
    """Test ProactiveSensei nudge generation."""
    from skills.nihongo.proactive_sensei import ProactiveSensei

    pro = ProactiveSensei()

    # Test nudge message
    nudge = pro.generate_proactive_message(user_id=TEST_USER_ID)
    assert len(nudge) > 0

    # Test suggested topic returns valid topic
    topic = pro.get_suggested_topic(user_id=TEST_USER_ID)
    assert topic is not None

    # Test daily summary format
    summary = pro.format_daily_summary(user_id=TEST_USER_ID)
    assert summary is not None

    # Test learning stats
    stats = pro.get_user_learning_stats(user_id=TEST_USER_ID)
    assert "srs_mastery_percentage" in stats
    assert "suggested_topic" in stats

    print("✅ ProactiveSensei nudge works")


def test_shadow_engine_phoneme_tracking():
    """Test ShadowEngine phoneme tracking."""
    from skills.nihongo.shadow_engine import ShadowEngine

    shadow = ShadowEngine()

    # Test exercise for level
    exercise = shadow.get_exercise_for_level(user_id=TEST_USER_ID, level="N5")
    assert exercise.japanese_text is not None
    assert exercise.difficulty == "N5"

    # Test Narita shadow scripts
    scripts = shadow.get_narita_shadow_scripts()
    assert len(scripts) > 0

    # Test phoneme tracking
    record = shadow.track_shadow_progress(user_id=TEST_USER_ID, phoneme="ら", accuracy=85.0)
    assert record.phoneme == "ら"
    assert record.accuracy > 0

    # Test phoneme weaknesses
    weak = shadow.get_phoneme_weaknesses(user_id=TEST_USER_ID)
    assert isinstance(weak, list)

    # Test shadow comparison
    result = shadow.compare_shadow_attempt(
        user_id=TEST_USER_ID, original="ありがとうございます", attempt_transcription="arigatou gozaimasu"
    )
    assert "similarity_score" in result
    assert "feedback" in result

    print("✅ ShadowEngine phoneme tracking works")


def test_sensei_prompt_builder():
    """Test SenseiPromptBuilder chainable interface."""
    from skills.nihongo.sensei_prompt import SenseiPromptBuilder
    from skills.nihongo.mode_manager import NihongoModeManager

    # Test old interface still works
    session = NihongoModeManager.activate(TEST_USER_ID)
    prompt = build_sensei_system_prompt(session)
    assert "Sensei" in prompt

    # Test new chainable interface
    builder = SenseiPromptBuilder()
    built = builder.base().with_sub_mode(session.sub_mode).with_session_context(session).build()
    assert "Sensei" in built

    # Test soul integration
    from skills.nihongo.sensei_soul import SenseiSoul

    soul = SenseiSoul(user_id=TEST_USER_ID)
    built_with_soul = builder.base().with_soul(soul).build()
    assert "Sensei" in built_with_soul

    # Test mastery integration
    from skills.nihongo.mastery_gate import MasteryGate

    gate = MasteryGate()
    built_with_mastery = builder.base().with_mastery(gate, TEST_USER_ID).build()
    assert "Sensei" in built_with_mastery

    print("✅ SenseiPromptBuilder works")


if __name__ == "__main__":
    test_isolation_when_off()
    test_activate_and_deactivate()
    test_sensei_prompt_no_legion_content()
    test_furigana_annotation()
    test_extract_japanese_only()
    test_sub_modes()
    test_exchange_counter()
    test_n5_vocab_loaded()
    test_n5_grammar_loaded()
    test_mode_settings()
    # New component tests
    test_sensei_soul_mood_tracking()
    test_mastery_gate_bloom_classification()
    test_immersion_world_scenarios()
    test_srs_engine_sm2_algorithm()
    test_cultural_intel_notes()
    test_proactive_sensei_nudge()
    test_shadow_engine_phoneme_tracking()
    test_sensei_prompt_builder()
    print("\n⛩ ALL NIHONGO MODE TESTS PASSED")
    print("Mode is ready. Try: /nihonko in Telegram.")
