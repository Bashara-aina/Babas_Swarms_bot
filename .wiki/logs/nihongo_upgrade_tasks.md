---
# NIHONGO MODE v2.0 — Upgrade Task List
> Planned by @planner | Date: 2026-04-12

## Overview
Upgrade the existing Nihongo Mode with 9 major components while maintaining full backward compatibility with the existing command interface (`/nihonko`, `/nihonko off`, `/nihonko quiz`, etc.).

---

## CONSTRAINTS (MUST NOT BREAK)
- Existing command interface: `/nihonko`, `/nihonko chat`, `/nihonko voice`, `/nihonko quiz`, `/nihonko story`, `/nihonko free`, `/stop`, `/nihonko status`, `/nihonko level`, `/furigana on/off`, `/romaji on/off`, `/slow on/off`
- All new code isolated from Legion's core
- DO NOT touch: `SOUL.md`, `CLAUDE.md`, `LEGION_MASTER.md`, `core/character_enforcer.py`, `core/soul_engine.py`

---

## EXISTING FILES (READ-ONLY REFERENCE)
| File | Purpose |
|------|---------|
| `skills/nihongo/__init__.py` | Module exports |
| `skills/nihongo/constants.py` | N5_VOCAB_SAMPLE, N5_GRAMMAR_PATTERNS, LESSON_TEMPLATES, LessonType enum |
| `skills/nihongo/sensei_prompt.py` | Static SENSEI_BASE + additions, `build_sensei_system_prompt()` |
| `skills/nihongo/mode_manager.py` | NihongoModeManager, NihongoSession, NihongoSubMode enum |
| `skills/nihongo/lesson_engine.py` | LessonEngine with N5_TOPICS |
| `skills/nihongo/quiz_engine.py` | QuizEngine with scoring |
| `skills/nihongo/voice_pipeline.py` | Whisper STT + VoiceVox/gTTS TTS |
| `skills/nihongo/correction_engine.py` | Grammar/vocab correction |
| `skills/nihongo/progress_store.py` | Supabase adapter |
| `skills/nihongo/vocab_tracker.py` | Tracks words seen/failed/mastered |
| `skills/nihongo/furigana.py` | pykakasi-based furigana + romaji |
| `handlers/nihongo_handler.py` | Telegram handler |
| `data/nihongo/n5_vocab.json` | 30 N5 vocabulary words |
| `data/nihongo/n5_grammar.json` | 15 grammar patterns |
| `data/nihongo/lesson_templates.json` | 8 lesson templates |

---

## SUBTASK 1: SenseiSoul (Dynamic Soul Layer with Hanako Identity)
**Files to create**: `skills/nihongo/sensei_soul.py`

**What to do**:
- Create `SenseiSoul` class that represents Hanako's dynamic identity as the teacher's "soul"
- Implement emotional state tracking: `mood`, `enthusiasm`, `patience`, `strictness` (0-100 scale)
- Implement relationship metrics: `trust_level`, `rapport`, `frustration_count`
- Add `get_teaching_mood()` method that returns contextual mood based on time of day, session performance
- Add `adjust_mood_on_outcome(correct: bool)` method for feedback-driven mood changes
- Add `get_soul_prompt_fragment()` method that returns personality-specific prompt additions
- Mood affects: response style (more encouraging when patience is low, more challenging when enthusiasm is high)

**Expected outcome**:
- Hanako has a dynamic "soul" that evolves through the learning session
- Mood fragments are appended to the system prompt to give Hanako personality variation

**Verification**:
```python
from skills.nihongo.sensei_soul import SenseiSoul
soul = SenseiSoul(user_id=123)
assert soul.get_mood()["enthusiasm"] > 0
soul.adjust_mood_on_outcome(correct=False)
assert soul.get_mood()["patience"] >= soul.get_mood()["enthusiasm"]  # patience becomes higher after mistake
```

---

## SUBTASK 2: MasteryGate (Bloom 2-Sigma Mastery Learning)
**Files to create**: `skills/nihongo/mastery_gate.py`

**What to do**:
- Create `MasteryGate` class implementing Bloom's taxonomy for language learning
- Implement 6 cognitive levels: REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE
- Track each word/grammar point at which level the user has achieved mastery (2-sigma = ~95% accuracy)
- Implement `classify_question(text: str) -> BloomLevel` using keyword patterns
- Implement `evaluate_mastery(user_id: int, item: str) -> (level, sigma)` returning current mastery level and sigma score
- Implement `get_next_difficulty(user_id: int, current_item: str) -> str` for adaptive progression
- Add `@mastery_gate` decorator on questions to tag difficulty level

**Expected outcome**:
- Questions are classified by Bloom level
- Mastery tracking per item with sigma score (2-sigma = ~95% correct = mastered)
- Adaptive difficulty selection based on mastery level

**Verification**:
```python
from skills.nihongo.mastery_gate import MasteryGate, BloomLevel
gate = MasteryGate()
level = gate.classify_question("Apa arti 学生?")
assert level == BloomLevel.REMEMBER
sigma = gate.evaluate_mastery(user_id=123, item="学生")
assert 0 <= sigma <= 3.0
```

---

## SUBTASK 3: ImmersionWorld (Narita-Specific Scenarios)
**Files to create**: `skills/nihongo/immersion_world.py`

**What to do**:
- Create `ImmersionWorld` class with location-specific Japanese scenarios
- Define location contexts: NARITA_AIRPORT, KEIOSHIBAURA_CAMPUS, CONBINI, TRAIN_STATION, HOSPITAL, CITY_HALL
- Create scenario templates for each location with N5 Japanese dialogues
- Implement `generate_scenario(location: str, context: dict) -> Scenario` returning scenario data
- Implement `get_narita_vocab() -> list[dict]` returning Narita-specific vocabulary (Keisei line, airport signs, campus vocabulary)
- Implement `get_campus_phrases() -> list[dict]` for university-specific Japanese
- Scenarios include: checking in at Narita Airport, buying bento at FamilyMart, asking for directions to campus

**Expected outcome**:
- Rich, location-aware scenarios that make learning relevant for Bashara's daily life in Narita
- Narita-specific vocabulary integrated into lessons

**Verification**:
```python
from skills.nihongo.immersion_world import ImmersionWorld, Location
world = ImmersionWorld()
scenario = world.generate_scenario(Location.NARITA_AIRPORT, {"situation": "check_in"})
assert " Narita" in scenario.title or "空港" in scenario.title
vocab = world.get_narita_vocab()
assert len(vocab) > 0
```

---

## SUBTASK 4: SRSEngine (Spaced Repetition with SM-2)
**Files to create**: `skills/nihongo/srs_engine.py`

**What to do**:
- Create `SRSEngine` class implementing the SM-2 spaced repetition algorithm
- Implement `SRSCard` dataclass: `item_id`, `ease_factor` (default 2.5), `interval` (days), `repetitions`, `next_review`, `last_review`
- Implement `add_card(user_id: int, item: str)` to create a new SRS card
- Implement `record_review(user_id: int, item: str, quality: int)` where quality is 0-5 (0-2 = fail, 3-5 = pass)
- Implement `get_due_cards(user_id: int) -> list[SRSCard]` returning cards due for review
- Implement `calculate_next_review(card: SRSCard, quality: int) -> (interval, ease_factor)` SM-2 logic
- Implement `get_mastery_percentage(user_id: int) -> float` based on cards at 2-sigma (interval > 21 days)

**Expected outcome**:
- Full SM-2 algorithm implementation
- Cards scheduled for review at optimal retention intervals
- Mastery percentage tracked

**Verification**:
```python
from skills.nihongo.srs_engine import SRSEngine, SRSCard
engine = SRSEngine()
engine.add_card(user_id=123, item="学生")
card = engine.get_due_cards(user_id=123)[0]
assert card.item_id == "学生"
engine.record_review(user_id=123, item="学生", quality=4)
```

---

## SUBTASK 5: CulturalIntel (Cultural Intelligence Layer)
**Files to create**: `skills/nihongo/cultural_intel.py`

**What to do**:
- Create `CulturalIntel` class providing context-aware cultural guidance
- Define `CulturalNote` dataclass: `topic`, `japanese_practice`, `indonesian_explanation`, `importance_level`
- Implement `get_cultural_notes_for_topic(topic: str) -> list[CulturalNote]`
- Implement `get_keigo_awareness(user_level: str) -> str` returning keigo guidance
- Implement `get_situation_culture(location: str, situation: str) -> CulturalNote`
- Topics: bowing, business card exchange (meishi), keigo levels, gift-giving, seasonal greetings, university etiquette
- Implement `format_cultural_note(note: CulturalNote) -> str` for Telegram-formatted output

**Expected outcome**:
- Cultural intelligence integrated into lessons without breaking the flow
- Bashara learns cultural context alongside language

**Verification**:
```python
from skills.nihongo.cultural_intel import CulturalIntel, CulturalNote
intel = CulturalIntel()
notes = intel.get_cultural_notes_for_topic("keigo")
assert len(notes) > 0
note = intel.get_situation_culture("university", "meeting_professor")
assert note.importance_level in ["high", "medium", "low"]
```

---

## SUBTASK 6: ProactiveSensei (Integrates with Legion's Proactive Engine)
**Files to create**: `skills/nihongo/proactive_sensei.py`

**What to do**:
- Create `ProactiveSensei` class that integrates with Legion's proactive engine
- Implement `should_proactively_nudge(user_id: int) -> bool` based on:
  - Time since last session (>48hr = warm-up needed)
  - Cards due in SRS engine
  - Failed words that need reintroduction
- Implement `generate_proactive_message(user_id: int) -> str` returning gentle nudge message
- Implement `get_suggested_topic(user_id: int) -> str` based on mastery gaps
- Implement `format_daily_summary(user_id: int) -> str` for end-of-day summary
- Implement `check_and_trigger_proactive()` method that checks all nudge conditions
- This class can be called by Legion's proactive engine without breaking isolation

**Expected outcome**:
- Proactive nudges for review sessions
- Daily summary capability
- Integration point for Legion's proactive engine

**Verification**:
```python
from skills.nihongo.proactive_sensei import ProactiveSensei
pro = ProactiveSensei()
nudge = pro.generate_proactive_message(user_id=123)
assert len(nudge) > 0
topic = pro.get_suggested_topic(user_id=123)
assert topic in ["greetings", "numbers", "directions", ...]
```

---

## SUBTASK 7: ShadowEngine (Shadow Speaking for Pronunciation)
**Files to create**: `skills/nihongo/shadow_engine.py`

**What to do**:
- Create `ShadowEngine` class for shadow speaking practice
- Implement `ShadowExercise` dataclass: `japanese_text`, `romaji`, `audio_url` (optional), `difficulty`, `scenario`
- Implement `get_exercise_for_level(user_id: int, level: str) -> ShadowExercise`
- Implement `compare_shadow_attempt(user_id: int, original: str, attempt_transcription: str) -> dict`
  - Returns: similarity_score, problem_phonemes, feedback
- Implement `get_narita_shadow_scripts() -> list[ShadowExercise]` returning Narita-specific shadowing scripts
- Implement `track_shadow_progress(user_id: int, phoneme: str, accuracy: float)` tracking per-phoneme accuracy
- Implement `get_phoneme_weaknesses(user_id: int) -> list[str]` returning problematic phonemes

**Expected outcome**:
- Shadow speaking exercises with phoneme-level feedback
- Pronunciation improvement tracking
- Narita-specific scripts (airport announcements, campusPA)

**Verification**:
```python
from skills.nihongo.shadow_engine import ShadowEngine
shadow = ShadowEngine()
exercise = shadow.get_exercise_for_level(user_id=123, level="N5")
assert exercise.japanese_text is not None
scripts = shadow.get_narita_shadow_scripts()
assert len(scripts) > 0
```

---

## SUBTASK 8: Upgrade sensei_prompt.py to Dynamic Building
**Files to modify**: `skills/nihongo/sensei_prompt.py`

**What to do**:
- Refactor `build_sensei_system_prompt()` to use dynamic component assembly
- Add `SenseiPromptBuilder` class with chainable methods:
  - `base()` - SENSEI_BASE
  - `with_soul(soul: SenseiSoul)` - append soul fragment
  - `with_mastery(gate: MasteryGate, user_id: int)` - append mastery context
  - `with_immersion(world: ImmersionWorld, location: str)` - append immersion scenario
  - `with_srs(engine: SRSEngine, user_id: int)` - append SRS due cards info
  - `with_culture(intel: CulturalIntel, topic: str)` - append cultural note
  - `with_sub_mode(sub_mode: NihongoSubMode)` - existing mode additions
  - `with_session_context(session: NihongoSession)` - existing context section
- Keep SENSEI_BASE as static foundation but make additions dynamic
- Maintain backward compatibility: `build_sensei_system_prompt(session)` must still work exactly as before

**Expected outcome**:
- Prompt building becomes modular and component-driven
- Hanako's soul, mastery state, immersion context, SRS cards, cultural notes can all be dynamically included
- Backward compatible with existing code

**Verification**:
```python
from skills.nihongo.sensei_prompt import build_sensei_system_prompt, SenseiPromptBuilder
# Old interface still works
session = NihongoModeManager.activate(123)
prompt = build_sensei_system_prompt(session)
assert "Sensei" in prompt
# New interface
builder = SenseiPromptBuilder().base().with_sub_mode(session.sub_mode).with_session_context(session)
assert "Sensei" in builder.build()
```

---

## SUBTASK 9: Upgrade /nihonko status — Beautiful Dashboard
**Files to modify**: `handlers/nihongo_handler.py`

**What to do**:
- Redesign the `/nihonko status` handler to show a beautiful ASCII dashboard
- New dashboard format with:
  ```
  ╔══════════════════════════════════════════════╗
  ║  ⛩ NIHONGO MODE — 日本語학습               ║
  ║  Hanako Sensei | Status: Active              ║
  ╠══════════════════════════════════════════════╣
  ║  📊 Progress                                 ║
  ║  Words Mastered: 45/120  [████████░░] 37.5%  ║
  ║  Grammar Points: 12/15    [██████████░] 80% ║
  ║  SRS Mastery:     23/30  [████████░░] 76.7% ║
  ╠══════════════════════════════════════════════╣
  ║  🎯 Quiz Stats                              ║
  ║  Score: 28/35 | Streak: 7 🔥              ║
  ╠══════════════════════════════════════════════╣
  ║  📅 Next Review                             ║
  ║  5 cards due today | 3 cards overdue       ║
  ╠══════════════════════════════════════════════╣
  ║  🎙 Voice: ON | 🀄 Furigana: ON | ろ: ON   ║
  ║  Mode: CHAT | Level: N5 | Exchanges: 47    ║
  ╚══════════════════════════════════════════════╝
  ```
- Include SRS mastery percentage if srs_engine is available
- Include Bloom mastery distribution if mastery_gate is available
- Include ShadowEngine phoneme weaknesses if available
- Gracefully degrade if new components not initialized

**Expected outcome**:
- Beautiful dashboard display for `/nihonko status`
- Shows progress across all new components
- Still works if new components are not loaded

**Verification**:
- Send `/nihonko status` and verify dashboard renders correctly in Telegram

---

## SUBTASK 10: Update __init__.py Exports
**Files to modify**: `skills/nihongo/__init__.py`

**What to do**:
- Add exports for all new classes:
  - `SenseiSoul`
  - `MasteryGate`, `BloomLevel`
  - `ImmersionWorld`, `Location`
  - `SRSEngine`, `SRSCard`
  - `CulturalIntel`, `CulturalNote`
  - `ProactiveSensei`
  - `ShadowEngine`, `ShadowExercise`

**Expected outcome**:
- All new classes available via `from skills.nihongo import *`

**Verification**:
```python
from skills.nihongo import SenseiSoul, MasteryGate, BloomLevel, ImmersionWorld, Location, SRSEngine, SRSCard, CulturalIntel, ProactiveSensei, ShadowEngine
print("All imports successful")
```

---

## SUBTASK 11: Update Tests
**Files to create**: `tests/test_nihongo_mode.py` (append new tests)

**What to do**:
- Add tests for all 9 new components:
  - `test_sensei_soul_mood_tracking()`
  - `test_mastery_gate_bloom_classification()`
  - `test_immersion_world_scenarios()`
  - `test_srs_engine_sm2_algorithm()`
  - `test_cultural_intel_notes()`
  - `test_proactive_sensei_nudge()`
  - `test_shadow_engine_phoneme_tracking()`
  - `test_sensei_prompt_builder()`
  - `test_status_dashboard_format()`
- All tests must pass with `pytest tests/test_nihongo_mode.py -x --asyncio-mode=auto -q`

**Expected outcome**:
- Comprehensive test coverage for all new components
- All existing tests still pass

**Verification**:
```bash
pytest tests/test_nihongo_mode.py -x --asyncio-mode=auto -q
```

---

## SUBTASK 12: Create ADR Document
**Files to create**: `.wiki/decisions/adr-041-nihongo-v2.md`

**What to do**:
- Write Architecture Decision Record describing:
  - Current architecture summary
  - New architecture design
  - Key design decisions
  - Rationale for each component
  - Backward compatibility strategy

**Expected outcome**:
- ADR-041 document in `.wiki/decisions/`

---

## EXECUTION ORDER
1. SUBTASK 1: sensei_soul.py (foundation for personality)
2. SUBTASK 4: srs_engine.py (core learning algorithm)
3. SUBTASK 2: mastery_gate.py (depends on SRS)
4. SUBTASK 3: immersion_world.py
5. SUBTASK 5: cultural_intel.py
6. SUBTASK 7: shadow_engine.py
7. SUBTASK 6: proactive_sensei.py (depends on SRS, Mastery)
8. SUBTASK 8: sensei_prompt.py upgrade (depends on 1-7)
9. SUBTASK 9: handler dashboard (depends on 1-7)
10. SUBTASK 10: __init__.py exports
11. SUBTASK 11: tests
12. SUBTASK 12: ADR document

---

## BACKWARD COMPATIBILITY GUARANTEE
All existing commands MUST continue to work without modification:
- `/nihonko` → works
- `/nihonko chat` → works
- `/nihonko voice` → works
- `/nihonko quiz` → works
- `/nihonko story` → works
- `/nihonko free` → works
- `/stop` → works
- `/nihonko status` → works (enhanced)
- `/nihonko level n5/n4/n3` → works
- `/furigana on/off` → works
- `/romaji on/off` → works
- `/slow on/off` → works
