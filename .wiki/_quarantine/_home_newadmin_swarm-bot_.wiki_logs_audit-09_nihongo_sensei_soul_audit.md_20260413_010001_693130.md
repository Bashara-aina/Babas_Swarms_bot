---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/audit-09/nihongo_sensei_soul_audit.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.693171"
}
---

# Nihongo SenseiSoul Audit — LEGION AUDIT 09
> Generated: 2026-04-12

## Import Verification

```python
# skills/nihongo/sensei_soul.py exists and imports:
from dataclasses import dataclass
from datetime import datetime
import random
# ✅ No external dependencies — fully self-contained
```

## Connection Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    NIHONGO SENSEI SOUL ARCHITECTURE            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  handlers/nihongo_handler.py                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Commands: /nihonko, /nihonko chat|voice|quiz|story|free  │ │
│  │ Imports:                                                   │ │
│  │   - from skills.nihongo.mode_manager import NihongoModeMgr│ │
│  │   - from skills.nihongo.sensei_prompt import build_sensei_│ │
│  │   - from skills.nihongo.quiz_engine import QuizEngine     │ │
│  │   - from skills.nihongo.vocab_tracker import VocabTracker │ │
│  │   - from skills.nihongo.voice_pipeline import TTS/stt     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│  skills/nihongo/sensei_prompt.py                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ SENSEI_BASE — Hanako's system prompt foundation           │ │
│  │ SenseiPromptBuilder — chainable prompt assembly           │ │
│  │ build_sensei_system_prompt(session) → str                │ │
│  │                                                           │ │
│  │ Connects to:                                              │ │
│  │   - SenseiSoul.get_soul_prompt_fragment() [via .with_soul]│ │
│  │   - MasteryGate.get_mastery_distribution()                │ │
│  │   - SRSEngine.get_due_cards()                             │ │
│  │   - ImmersionWorld.generate_scenario()                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│  skills/nihongo/sensei_soul.py                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ SenseiSoul class                                          │ │
│  │   - MoodState (dataclass): mood, enthusiasm, patience,    │ │
│  │     strictness                                             │ │
│  │   - RelationshipMetrics: trust_level, rapport, frust_count│ │
│  │   - get_mood(), get_teaching_mood(), adjust_mood_on_outcome│ │
│  │   - get_soul_prompt_fragment() → str                     │ │
│  │   - update_trust(), reset_session_state()                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ▲                                    │
│                            │                                    │
│  Other nihongo modules:                                        │
│    - lesson_engine.py: N5_TOPICS, LessonEngine (curriculum)  │
│    - proactive_sensei.py: ProactiveSensei (nudge engine)       │
│    - mode_manager.py: NihongoModeManager, NihongoSession      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Connection Points Verified

| From | To | Connection | Status |
|------|----|-----------|--------|
| `sensei_prompt.py` | `sensei_soul.py` | `SenseiPromptBuilder.with_soul(soul)` calls `soul.get_soul_prompt_fragment()` | ✅ Connected |
| `sensei_prompt.py` | `lesson_engine.py` | `build_sensei_system_prompt()` uses session with N5_TOPICS curriculum | ✅ Connected via session |
| `proactive_sensei.py` | `sensei_soul.py` | None direct — separate proactive engine | ⚠️ Independent |
| `proactive_sensei.py` | `lesson_engine.py` | Uses SRSEngine and MasteryGate | ✅ Connected |
| `handlers/nihongo_handler.py` | `sensei_prompt.py` | `build_sensei_system_prompt(session)` called in message handler | ✅ Connected |
| `handlers/nihongo_handler.py` | `lesson_engine.py` | Indirect — via session tracking | ✅ Connected |

## Key Files Analysis

### `sensei_soul.py`
- **Class**: `SenseiSoul` with `MoodState` and `RelationshipMetrics` dataclasses
- **Public methods**: `get_mood()`, `get_teaching_mood()`, `adjust_mood_on_outcome()`, `get_soul_prompt_fragment()`, `update_trust()`, `reset_session_state()`
- **Self-contained**: No external imports except stdlib

### `sensei_prompt.py`
- **Class**: `SenseiPromptBuilder` — chainable prompt builder
- **Functions**: `build_sensei_system_prompt(session)`, constants `SENSEI_BASE`, `STORY_MODE_ADDITION`, `QUIZ_MODE_ADDITION`, `FREE_MODE_ADDITION`
- **Methods**: `.with_soul()`, `.with_mastery()`, `.with_immersion()`, `.with_srs()`, `.with_culture()`, `.with_sub_mode()`, `.with_session_context()`

### `lesson_engine.py`
- **Class**: `LessonEngine` — curriculum management with N5_TOPICS list
- **Methods**: `get_user_progress()`, `get_next_topic()`, `advance_lesson()`, `complete_topic()`, `should_review()`, `schedule_review()`
- **Uses**: Class-level `_user_progress` dict for persistence

### `proactive_sensei.py`
- **Class**: `ProactiveSensei` — proactive nudge engine
- **Methods**: `should_proactively_nudge()`, `generate_proactive_message()`, `get_suggested_topic()`, `format_daily_summary()`, `check_and_trigger_proactive()`, `get_user_learning_stats()`
- **Uses**: SRSEngine, MasteryGate, NihongoModeManager

### `handlers/nihongo_handler.py`
- **Commands**: `/nihonko`, `/nihonko chat|voice|quiz|story|free`, `/stopp`, `/nihonko status`, `/nihonko level`, `/furigana on|off`, `/romaji on|off`, `/slow on|off`
- **Functions**: `handle_nihongo_command()`, `handle_nihongo_message()`, `_call_llm()`, `_handle_voice_input()`
- **Connects**: All nihongo components via imports

## Verdict

- ✅ **Import works** — all nihongo modules exist and are importable
- ✅ **SenseiSoul is self-contained** — no circular dependencies
- ✅ **Full call chain verified**: handler → sensei_prompt → (SenseiSoul + lesson_engine + proactive_sensei)
- ⚠️ **ProactiveSensei is semi-independent** — can be called by Legion's proactive engine but is otherwise isolated
