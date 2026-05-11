---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/decisions/adr-041-nihongo-v2.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-07T01:00:00.666275"
}
---

---
title: Adr 041 Nihongo V2
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: Upgrade Nihongo Mode from a basic Japanese teaching interface into a sophisticated,
 multi-component language learning system while maintaining full backward compatibility
 with existing commands and...
wikilinks: []
confidence: medium
source: research
---
Upgrade Nihongo Mode from a basic Japanese teaching interface into a sophisticated, multi-component language learning system while maintaining full backward compatibility with existing commands and complete isolation from Legion's core.
---

## Current Architecture Summary

### Existing Components

```
skills/nihongo/
├── __init__.py # Module exports
├── constants.py # N5_VOCAB_SAMPLE, N5_GRAMMAR_PATTERNS, LESSON_TEMPLATES
├── sensei_prompt.py # Static SENSEI_BASE + additions, build_sensei_system_prompt()
├── mode_manager.py # NihongoModeManager, NihongoSession, NihongoSubMode enum
├── lesson_engine.py # LessonEngine with N5_TOPICS
├── quiz_engine.py # QuizEngine with scoring
├── voice_pipeline.py # Whisper STT + VoiceVox/gTTS TTS
├── correction_engine.py # Grammar/vocab correction
├── progress_store.py # Supabase adapter (in-memory cache)
├── vocab_tracker.py # Tracks words seen/failed/mastered
└── furigana.py # pykakasi-based furigana + romaji

handlers/
└── nihongo_handler.py # Telegram handler, all /nihonko commands

data/nihongo/
├── n5_vocab.json # 30 N5 vocabulary words
├── n5_grammar.json # 15 grammar patterns
└── lesson_templates.json # 8 lesson templates
```

### Current Data Flow

```
User → /nihonko → nihongo_handler.py → NihongoModeManager.activate()
User message → build_sensei_system_prompt(session) → LLM → response → user
```

### Limitations of Current Architecture

1. **Static Prompt**: `build_sensei_system_prompt()` concatenates static strings, no dynamic personalization
2. **No Spaced Repetition**: Lesson engine has no SM-2 algorithm; review scheduling is manual
3. **No Mastery Tracking**: No systematic Bloom taxonomy tracking; no 2-sigma mastery measurement
4. **No Cultural Intelligence**: Cultural notes not systematically integrated
5. **No Pronunciation Shadowing**: No shadow speaking engine
6. **No Proactive Learning**: System is purely reactive (user must initiate)
7. **No Soul/Identity Layer**: Hanako has no dynamic emotional state or personality evolution
8. **No Narita-Specific Content**: Generic N5 content, not tailored to Bashara's actual locations

---

## New Architecture Design

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ NIHONGO MODE v2.0 STACK │
├─────────────────────────────────────────────────────────────────────┤
│ │
│ ┌───────────────┐ ┌────────────────┐ ┌───────────────┐ │
│ │ SenseiSoul │────▶│ ProactiveSensei│◀────│ ShadowEngine │ │
│ │ (Dynamic soul)│ │ (Nudge engine) │ │ (Pronunciation│ │
│ └───────────────┘ └────────────────┘ └───────────────┘ │
│ │ ▲ │ │
│ ▼ │ ▼ │
│ ┌───────────────────────────────────────────────────────────────┐ │
│ │ SenseiPromptBuilder (Dynamic) │ │
│ │ .base() .with_soul() .with_mastery() .with_immersion() │ │
│ │ .with_srs() .with_culture() .with_sub_mode() .build() │ │
│ └───────────────────────────────────────────────────────────────┘ │
│ │ │
│ ▼ │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│ │ MasteryGate │ │ SRSEngine │ │ ImmersionWorld │ │
│ │ (Bloom 2σ) │ │ (SM-2) │ │ (Narita scenarios) │ │
│ └───────────────┘ └───────────────┘ └───────────────────────┘ │
│ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │ CulturalIntel │ │ VocabTracker │ │
│ │ (Keigo/etc) │ │ (existing) │ │
│ └───────────────┘ └───────────────┘ │
│ │
│ ┌───────────────────────────────────────────────────────────────┐ │
│ │ nihongo_handler.py (Telegram) │ │
│ │ /nihonko* commands ──► mode_manager ──► LLM call │ │
│ └───────────────────────────────────────────────────────────────┘ │
│ │
│ ┌───────────────────────────────────────────────────────────────┐ │
│ │ Legion Core (ISOLATED - NO CHANGES) │ │
│ │ SOUL.md, soul_engine.py, character_enforcer.py, LEGION_*.md │ │
│ └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### New Components

| Component | File | Purpose |
|-----------|------|---------|
| **SenseiSoul** | `sensei_soul.py` | Dynamic emotional state & personality layer for Hanako |
| **MasteryGate** | `mastery_gate.py` | Bloom taxonomy + 2-sigma mastery tracking |
| **SRSEngine** | `srs_engine.py` | SM-2 spaced repetition scheduler |
| **ImmersionWorld** | `immersion_world.py` | Narita-specific scenario generator |
| **CulturalIntel** | `cultural_intel.py` | Cultural intelligence layer |
| **ProactiveSensei** | `proactive_sensei.py` | Proactive nudge engine |
| **ShadowEngine** | `shadow_engine.py` | Shadow speaking + phoneme tracking |

---

## Key Design Decisions

### 1. Complete Isolation from Legion Core

**Decision**: Nihongo Mode v2.0 MUST NOT modify any file in `core/`, `SOUL.md`, `CLAUDE.md`, or `LEGION_MASTER.md`.

**Rationale**: 
- Nihongo Mode is a "plugin" that can be disabled/removed without affecting Legion
- Prevents soul pollution between Hanako (Sensei) and Legion's personality
- Avoids complexity in character enforcement

**Consequence**: ProactiveSensei provides an integration POINT, not integration. Legion's proactive engine can call `ProactiveSensei.check_and_trigger_proactive()` but Nihongo Mode does not modify Legion's core.

### 2. Dynamic Prompt Building with Builder Pattern

**Decision**: `sensei_prompt.py` adopts a Builder pattern while maintaining backward-compatible interface.

**Old interface** (MUST still work):
```python
build_sensei_system_prompt(session) → str
```

**New interface** (additive):
```python
SenseiPromptBuilder().base().with_soul(soul).with_mastery(gate, uid).build() → str
```

**Rationale**: 
- Avoids breaking existing handler code
- Allows new components to inject context fragments
- Each component adds its own section to the prompt independently

### 3. SM-2 for Spaced Repetition

**Decision**: SRSEngine implements SuperMemo 2 algorithm directly.

**Rationale**:
- SM-2 is well-documented, proven algorithm
- 2-sigma mastery (~95% retention) aligns with "mastery" concept
- Simple to implement, test, and verify
- Cards with interval > 21 days considered "mastered"

**SM-2 Formula**:
```
if quality >= 3:
 if repetitions == 0: interval = 1
 elif repetitions == 1: interval = 6
 else: interval = round(interval * ease_factor)
 repetitions += 1
else:
 repetitions = 0
 interval = 1

ease_factor = max(1.3, ease_factor + (0.1 - (5-quality) * (0.08 + (5-quality) * 0.02)))
```

### 4. Bloom Taxonomy for Mastery Classification

**Decision**: MasteryGate uses Bloom's taxonomy with 6 levels.

**Rationale**:
- Standard educational framework
- Maps well to language learning progression
- REMEMBER (lowest) → CREATE (highest)
- 2-sigma mastery achieved when user reaches EVALUATE with 95% accuracy

**Bloom Levels for Nihongo**:
| Level | Japanese Example |
|-------|-----------------|
| REMEMBER | "Apa arti ?" |
| UNDERSTAND | "Jelaskan penggunaan " |
| APPLY | "Buat kalimat dengan " |
| ANALYZE | "Bandingkan dan " |
| EVALUATE | ": A vs B?" |
| CREATE | "Buat dialog alami menggunakangrammar point ini" |

### 5. Narita-Specific Immersion

**Decision**: ImmersionWorld focuses on locations Bashara actually visits.

**Location Priorities**:
1. **Narita Airport** (Airport life, customs, luggage)
2. **Keio/Shibaura Campus** (University Japanese, lab, sensei meetings)
3. **Konbini** (FamilyMart, 7-Eleven, Lawson)
4. **Train Station** (Keisei Narita, transit, directions)
5. **Hospital** (Medical Japanese, insurance)
6. **City Hall** (Residence, immigration paperwork)

**Rationale**: 
- Learning is most effective when immediately applicable
- Bashara lives in Narita, Chiba — relevance drives motivation
- Narita-specific vocabulary (Keisei line, airport signs) not in standard N5 curricula

### 6. SenseiSoul for Emotional Dynamics

**Decision**: Hanako has a dynamic "soul" that evolves through sessions.

**Emotional State Variables**:
| Variable | Range | Effect on Teaching |
|----------|-------|-------------------|
| `enthusiasm` | 0-100 | High → more challenging problems |
| `patience` | 0-100 | Low → more corrections, encouragement |
| `strictness` | 0-100 | High → fewer hints, faster pace |
| `trust_level` | 0-100 | Increases with correct answers |
| `frustration_count` | 0-∞ | Resets on user success |

**Rationale**:
- Static teachers feel robotic
- Emotional dynamics make Hanako feel more human
- Mood adapts to user performance (patience increases after mistakes)

### 7. ShadowEngine for Pronunciation

**Decision**: ShadowEngine tracks phoneme-level accuracy.

**Rationale**:
- Indonesian speakers have specific phonetic challenges with Japanese
- Common problem phonemes: vs , vs ,, (gemination)
- Shadow speaking is evidence-based method for pronunciation improvement
- Tracks per-phoneme accuracy over time

### 8. Proactive Integration Point

**Decision**: ProactiveSensei is a passive integration point, not an active modification of Legion.

**Interface**:
```python
ProactiveSensei.should_proactively_nudge(user_id) → bool
ProactiveSensei.generate_proactive_message(user_id) → str
```

**Rationale**:
- Legion's proactive engine decides when to call
- Nihongo Mode provides query capability, not autonomous action
- Maintains isolation principle

### 9. Graceful Degradation

**Decision**: All components handle missing dependencies gracefully.

**Example**: `/nihonko status` shows dashboard with available data:
- If SRSEngine not initialized → hide SRS section
- If MasteryGate not initialized → hide Bloom distribution
- Always show core stats (words seen, quiz score, etc.)

**Rationale**:
- New components can be added incrementally
- Users who don't use all features still get working system
- No hard dependencies between components

---

## Backward Compatibility Matrix

| Command | Status | Notes |
|---------|--------|-------|
| `/nihonko` | ✅ Works | Activates CHAT mode |
| `/nihonko chat` | ✅ Works | Activates CHAT mode |
| `/nihonko voice` | ✅ Works | Activates VOICE mode |
| `/nihonko quiz` | ✅ Works | Activates QUIZ mode |
| `/nihonko story` | ✅ Works | Activates STORY mode |
| `/nihonko free` | ✅ Works | Activates FREE mode |
| `/stop` | ✅ Works | Deactivates mode |
| `/nihonko status` | ✅ Enhanced | Beautiful dashboard |
| `/nihonko level n5/n4/n3` | ✅ Works | Sets level |
| `/furigana on/off` | ✅ Works | Toggles furigana |
| `/romaji on/off` | ✅ Works | Toggles romaji |
| `/slow on/off` | ✅ Works | Toggles TTS speed |

---

## File Changes Summary

### New Files (9)
1. `skills/nihongo/sensei_soul.py` — SenseiSoul class
2. `skills/nihongo/mastery_gate.py` — MasteryGate + BloomLevel
3. `skills/nihongo/srs_engine.py` — SRSEngine + SRSCard
4. `skills/nihongo/immersion_world.py` — ImmersionWorld + Location
5. `skills/nihongo/cultural_intel.py` — CulturalIntel + CulturalNote
6. `skills/nihongo/proactive_sensei.py` — ProactiveSensei
7. `skills/nihongo/shadow_engine.py` — ShadowEngine + ShadowExercise

### Modified Files (3)
1. `skills/nihongo/sensei_prompt.py` — Add SenseiPromptBuilder, keep old interface
2. `handlers/nihongo_handler.py` — Enhance `/nihonko status` dashboard
3. `skills/nihongo/__init__.py` — Export all new classes

### No Changes (Isolated)
- `SOUL.md`, `CLAUDE.md`, `LEGION_MASTER.md`
- `core/character_enforcer.py`, `core/soul_engine.py`
- `core/skill_registry.py` (Nihongo already registered)

---

## Test Strategy

All tests in `tests/test_nihongo_mode.py`:
1. Existing tests MUST pass (backward compatibility)
2. New tests for each component
3. Test command: `pytest tests/test_nihongo_mode.py -x --asyncio-mode=auto -q`

---

## Open Questions

1. **SRS Persistence**: Should SRS data persist to Supabase? (Currently in-memory)
2. **Voice Integration**: Should ShadowEngine use Whisper for attempted transcription?
3. **Narita Maps**: Should ImmersionWorld include actual map references for directions scenarios?
4. **Proactive Frequency**: How often should ProactiveSensei suggest nudges? (Currently: >48hr since session OR cards due)

---

## Decision History

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-12 | Create ADR-041 | Document v2.0 architecture |
| 2026-04-12 | Builder pattern for prompts | Backward compatibility |
| 2026-04-12 | SM-2 for SRS | Proven algorithm, simple implementation |
| 2026-04-12 | Bloom 2-sigma for mastery | Educational standard |
| 2026-04-12 | Narita-specific immersion | Bashara's actual locations |
| 2026-04-12 | Passive integration point for ProactiveSensei | Maintain isolation |
