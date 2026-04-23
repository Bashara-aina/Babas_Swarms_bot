---
name: nihongo
description: "Skill for the Nihongo area of swarm-bot. 61 symbols across 12 files."
---

# Nihongo

61 symbols | 12 files | Cohesion: 89%

## When to Use

- Working with code in `skills/`
- Understanding how test_sensei_prompt_builder, get_teaching_mood, get_soul_prompt_fragment work
- Modifying nihongo-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_nihongo_mode.py` | test_sensei_prompt_builder, test_proactive_sensei_nudge, test_shadow_engine_phoneme_tracking, test_cultural_intel_notes, test_extract_japanese_only (+4) |
| `skills/nihongo/sensei_prompt.py` | base, with_soul, with_mastery, with_sub_mode, with_session_context (+4) |
| `skills/nihongo/srs_engine.py` | is_mastered, get_overdue_cards, get_mastery_percentage, get_mastered_items, get_due_cards (+4) |
| `skills/nihongo/proactive_sensei.py` | get_suggested_topic, get_user_learning_stats, should_proactively_nudge, generate_proactive_message, format_daily_summary (+1) |
| `skills/nihongo/voice_pipeline.py` | text_to_speech_japanese, _tts_voicevox, _tts_gtts_fallback, transcribe_voice_note, _transcribe_whisper_api (+1) |
| `skills/nihongo/shadow_engine.py` | get_exercise_for_level, compare_shadow_attempt, get_narita_shadow_scripts, track_shadow_progress, get_phoneme_weaknesses |
| `skills/nihongo/sensei_soul.py` | get_teaching_mood, get_soul_prompt_fragment, get_mood, adjust_mood_on_outcome |
| `skills/nihongo/mastery_gate.py` | get_mastery_distribution, classify_question, evaluate_mastery, record_attempt |
| `skills/nihongo/cultural_intel.py` | get_cultural_notes_for_topic, get_keigo_awareness, get_situation_culture, format_cultural_note |
| `skills/nihongo/immersion_world.py` | generate_scenario, get_narita_vocab, get_campus_phrases |

## Entry Points

Start here when exploring this area:

- **`test_sensei_prompt_builder`** (Function) — `tests/test_nihongo_mode.py:310`
- **`get_teaching_mood`** (Function) — `skills/nihongo/sensei_soul.py:53`
- **`get_soul_prompt_fragment`** (Function) — `skills/nihongo/sensei_soul.py:113`
- **`base`** (Function) — `skills/nihongo/sensei_prompt.py:201`
- **`with_soul`** (Function) — `skills/nihongo/sensei_prompt.py:207`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_sensei_prompt_builder` | Function | `tests/test_nihongo_mode.py` | 310 |
| `get_teaching_mood` | Function | `skills/nihongo/sensei_soul.py` | 53 |
| `get_soul_prompt_fragment` | Function | `skills/nihongo/sensei_soul.py` | 113 |
| `base` | Function | `skills/nihongo/sensei_prompt.py` | 201 |
| `with_soul` | Function | `skills/nihongo/sensei_prompt.py` | 207 |
| `with_mastery` | Function | `skills/nihongo/sensei_prompt.py` | 215 |
| `with_sub_mode` | Function | `skills/nihongo/sensei_prompt.py` | 285 |
| `with_session_context` | Function | `skills/nihongo/sensei_prompt.py` | 295 |
| `build` | Function | `skills/nihongo/sensei_prompt.py` | 312 |
| `test_proactive_sensei_nudge` | Function | `tests/test_nihongo_mode.py` | 250 |
| `is_mastered` | Function | `skills/nihongo/srs_engine.py` | 35 |
| `get_overdue_cards` | Function | `skills/nihongo/srs_engine.py` | 175 |
| `get_mastery_percentage` | Function | `skills/nihongo/srs_engine.py` | 184 |
| `get_mastered_items` | Function | `skills/nihongo/srs_engine.py` | 207 |
| `get_suggested_topic` | Function | `skills/nihongo/proactive_sensei.py` | 115 |
| `get_user_learning_stats` | Function | `skills/nihongo/proactive_sensei.py` | 193 |
| `get_mastery_distribution` | Function | `skills/nihongo/mastery_gate.py` | 276 |
| `test_shadow_engine_phoneme_tracking` | Function | `tests/test_nihongo_mode.py` | 276 |
| `handle_nihongo_command` | Function | `handlers/nihongo_handler.py` | 46 |
| `get_exercise_for_level` | Function | `skills/nihongo/shadow_engine.py` | 155 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_nl → Get_mastery_distribution` | cross_community | 3 |
| `Handle_nl → Get_phoneme_weaknesses` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_sensei_prompt_builder"})` — see callers and callees
2. `gitnexus_query({query: "nihongo"})` — find related execution flows
3. Read key files listed above for implementation details
