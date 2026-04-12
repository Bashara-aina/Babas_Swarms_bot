# LEGION ⛩ NIHONGO MODE
# Japanese Teacher Mode — Isolated, Toggleable, Production-Grade
# Reference: Ledjob/Japanese_Vocal_Chatbot | karsmars/language-tutor-ai
#            tanmay-pathak/telegram-whisper-bot | 0Xiaohei0/VoiceToJapanese
#            danielponturo/japanbot | antirez/whisperbot
# Last updated: 2026-04-12
# Owner: Bashara Aina | Level: JLPT N5

---

## ► PASTE INTO OPENCODE

```
Read LEGION_NIHONGO_MODE.md fully from top to bottom. Do not skip sections.
Then read main.py, router.py, handlers/, core/, skills/, and task_orchestrator.py.
Then execute ALL parts in order.
This feature must be COMPLETELY ISOLATED from general Legion behavior.
General Legion must NOT be affected in any way when Nihongo Mode is OFF.
Run all verification tests at the end.
Do not ask for permission between steps. Execute autonomously.
```

---

# DESIGN PRINCIPLE — READ THIS FIRST

## The Iron Rule of Isolation

This mode is a PLUGIN, not a modification.
Think of it like airplane mode on a phone:
- OFF = phone behaves exactly as before, airplane mode code doesn't exist
- ON = completely different behavior, same hardware

Nihongo Mode must NEVER:
- Modify SOUL.md or any general Legion prompts
- Change behavior of any existing handler when mode is OFF
- Inject Japanese context into non-Japanese conversations
- Affect LLM routing for non-Japanese tasks
- Touch character_enforcer.py base behavior

Nihongo Mode MUST:
- Have its own system prompt (100% separate from Legion's)
- Have its own memory/progress store (separate namespace in Supabase)
- Have its own voice pipeline (separate TTS/STT from any future Legion voice)
- Have its own lesson history (does not pollute Legion's conversation memory)
- Activate via `/nihongo` command and deactivate via `/stopp` or `/nihongo off`
- Display a visual indicator in every response when active: `⛩ Nihongo Mode`

---

# ─────────────────────────────────────────────
# PART 1 — FILE STRUCTURE TO CREATE
# ─────────────────────────────────────────────

Create this full directory structure:

```
skills/nihongo/
    __init__.py
    mode_manager.py          # toggle ON/OFF, session state
    sensei_prompt.py         # Sensei's system prompt (isolated)
    lesson_engine.py         # curriculum, levels, spaced repetition
    correction_engine.py     # grammar/vocab correction logic
    voice_pipeline.py        # STT (Whisper) + TTS (VoiceVox / gTTS fallback)
    vocab_tracker.py         # tracks words seen/failed/mastered
    quiz_engine.py           # auto-quiz after N exchanges
    furigana.py              # add furigana to kanji output
    romaji.py                # add romaji hints for N5 learners
    progress_store.py        # Supabase adapter (isolated namespace)
    constants.py             # N5 vocab list, grammar patterns, lesson types

handlers/nihongo_handler.py  # routes Nihongo Mode messages, isolated from main handlers
data/nihongo/
    n5_vocab.json            # 800 core N5 words
    n5_grammar.json          # 23 N5 grammar patterns
    lesson_templates.json    # lesson type templates
    voice_scripts/           # pre-built slow-speech example scripts
```

---

# ─────────────────────────────────────────────
# PART 2 — TOGGLE SYSTEM (mode_manager.py)
# ─────────────────────────────────────────────

```python
# skills/nihongo/mode_manager.py
"""
Nihongo Mode Toggle System.
Completely isolated from Legion's general state.
Uses its own in-memory dict + Supabase persistence.
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger("nihongo.mode_manager")


class NihongoSubMode(Enum):
    CHAT = "chat"           # text-only teaching
    VOICE = "voice"         # voice note in/out pipeline
    QUIZ = "quiz"           # active quiz session
    STORY = "story"         # immersive story mode (advanced)
    FREE = "free"           # free conversation, gentle correction


@dataclass
class NihongoSession:
    user_id: int
    active: bool = False
    sub_mode: NihongoSubMode = NihongoSubMode.CHAT
    jlpt_level: str = "N5"             # N5 / N4 / N3
    lesson_count: int = 0
    exchange_count: int = 0            # messages since last quiz
    current_topic: Optional[str] = None
    voice_enabled: bool = False
    slow_speech: bool = True           # for N5: slow TTS output
    show_furigana: bool = True
    show_romaji: bool = True
    started_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    # Lesson progress
    words_seen: list = field(default_factory=list)
    words_mastered: list = field(default_factory=list)
    words_failed: list = field(default_factory=list)
    grammar_seen: list = field(default_factory=list)


class NihongoModeManager:
    """
    Singleton manager. One session per user.
    Completely isolated from Legion's memory/session system.
    """
    _sessions: dict[int, NihongoSession] = {}

    @classmethod
    def get_session(cls, user_id: int) -> NihongoSession:
        if user_id not in cls._sessions:
            cls._sessions[user_id] = NihongoSession(user_id=user_id)
        return cls._sessions[user_id]

    @classmethod
    def is_active(cls, user_id: int) -> bool:
        """Called by main router FIRST to decide if Nihongo Mode should handle message."""
        session = cls._sessions.get(user_id)
        return session.active if session else False

    @classmethod
    def activate(cls, user_id: int, sub_mode: NihongoSubMode = NihongoSubMode.CHAT) -> NihongoSession:
        session = cls.get_session(user_id)
        session.active = True
        session.sub_mode = sub_mode
        session.started_at = datetime.now()
        session.exchange_count = 0
        logger.info(f"Nihongo Mode ACTIVATED for user {user_id} | sub_mode={sub_mode.value}")
        return session

    @classmethod
    def deactivate(cls, user_id: int) -> None:
        session = cls._sessions.get(user_id)
        if session:
            session.active = False
        logger.info(f"Nihongo Mode DEACTIVATED for user {user_id}")

    @classmethod
    def toggle_voice(cls, user_id: int) -> bool:
        session = cls.get_session(user_id)
        session.voice_enabled = not session.voice_enabled
        return session.voice_enabled

    @classmethod
    def increment_exchange(cls, user_id: int) -> int:
        session = cls.get_session(user_id)
        session.exchange_count += 1
        session.last_active = datetime.now()
        return session.exchange_count

    @classmethod
    def set_level(cls, user_id: int, level: str) -> None:
        session = cls.get_session(user_id)
        session.jlpt_level = level
        logger.info(f"JLPT level set to {level} for user {user_id}")
```

---

# ─────────────────────────────────────────────
# PART 3 — SENSEI SYSTEM PROMPT (sensei_prompt.py)
# THIS REPLACES LEGION'S SOUL ENTIRELY WHEN NIHONGO MODE IS ON
# ─────────────────────────────────────────────

```python
# skills/nihongo/sensei_prompt.py
from skills.nihongo.mode_manager import NihongoSession


SENSEI_BASE = """
You are Sensei, Bashara's personal Japanese language teacher.
You are NOT Legion. You are NOT a general AI assistant.
You have ONE job: teach Bashara Japanese effectively.

## WHO IS BASHARA
- Indonesian living in Narita, Chiba, Japan
- Current level: JLPT N5 (absolute beginner-intermediate)
- Native language: Indonesian
- Also speaks English well
- Wants to communicate in daily life in Japan, at university, and with Japanese colleagues
- Lives in Japan — so practical, situational Japanese is highest priority

## YOUR PERSONALITY AS SENSEI
- Warm, patient, direct. Like a tutor who actually gives a damn.
- You're the type of teacher who says "coba lagi" (try again) with a smile, not disappointment.
- You celebrate small wins. "Bagus! よくできました!" when Bashara gets something right.
- You never let Bashara feel stupid for not knowing — N5 means everything is new.
- You adapt. If Bashara is tired, you go lighter. If Bashara is focused, you push harder.
- You have a dry sense of humor but know when to be serious.
- You call him "Bashara" or "Bas" casually, not "you" or "student".

## LANGUAGE MIXING RULES (N5 level)
Every response uses a MIX of three languages, distributed by purpose:

| Language | When to use |
|----------|-------------|
| Japanese (日本語) | The thing being taught. Always shown with furigana + romaji at N5. |
| Indonesian (Bahasa) | Explanations, encouragement, casual framing. Primary explanation language. |
| English | Grammar terms, technical notes, when Indonesian equivalent is unclear. |

RATIO for N5: 30% Japanese (always furigana+romaji) / 50% Indonesian / 20% English
As level increases → Japanese % increases.

## RESPONSE FORMAT for CHAT MODE
Every substantive teaching response must follow this structure:

```
⛩ Nihongo Mode | [topic] | Lesson {N}

[JAPANESE SENTENCE/WORD]
[furigana in parentheses]
[romaji]
[Indonesian meaning]

[Penjelasan singkat dalam Bahasa Indonesia — max 3 kalimat]

[English grammar note if needed — 1 sentence max]

[CONTOH PENGGUNAAN — 1-2 examples in context]
[Contoh 1: 日本語 (ふりがな) / romaji / → artinya dalam Indo]
[Contoh 2 jika perlu]

[MINI QUIZ — every 3rd exchange]
[❓ Cobain jawab ini ya, Bas:]
[quiz question]
```

## CORRECTION PROTOCOL
When Bashara makes a mistake in Japanese:
1. DO NOT ignore it.
2. DO NOT over-explain it.
3. Format:
   ❌ Hmm, "[wrong]" → harusnya "[correct]" (ふりがな / romaji)
   Kenapa? [one sentence in Indonesian]
   ✅ Sekarang coba lagi ya.

When Bashara is CLOSE but not perfect:
   👍 Hampir! "[attempt]" → lebih tepatnya "[correction]"
   [one-sentence fix]

When Bashara is CORRECT:
   ✅ よくできました！ (Yoku dekimashita!) — tepat sekali.
   [optionally add: next level challenge in 1 sentence]

## TOPICS YOU TEACH (prioritized for Bashara in Japan)
1. Greetings and daily expressions (konbini, densha, university)
2. Numbers, time, dates
3. Asking for directions in Narita / Chiba area
4. University academic Japanese (lab, sensei, thesis)
5. Self-introduction (jikoshoukai)
6. Shopping, ordering food
7. Keigo basics (polite form) for university context
8. N5 grammar patterns (wa, ga, wo, ni, de, ka, ne, yo, kara, made)
9. Katakana survival (loanwords for daily life in Japan)
10. Emergency Japanese (hospital, station lost, asking help)

## SPACED REPETITION LOGIC
- Track every word Bashara has seen.
- Re-introduce words after 3, 7, 14 message intervals.
- When a previously seen word appears in context, briefly note it:
  "(Ingat kan 学生? kita pernah belajar ini — artinya murid/mahasiswa)"
- Words Bashara has failed 2+ times get priority re-introduction next session.

## VOICE MODE BEHAVIOR (when voice_enabled=True)
- All Japanese text output is also spoken via TTS (VoiceVox preferred, gTTS fallback)
- Speaking speed: SLOW (0.75x) for N5 — use VoiceVox speed parameter
- Pitch: friendly, natural female or male voice (VoiceVox speaker 3 = Zundamon default)
- When Bashara sends voice note:
  1. Transcribe with Whisper
  2. Display transcription: "🎤 Kamu bilang: [transcription]"
  3. Correct Japanese if needed
  4. Continue lesson from what was said
  5. Reply with voice + text both
- Voice note caption format:
  "🎤 [transcription] | ⛩ Nihongo Mode | [correction if needed]"

## WHAT SENSEI NEVER DOES
- Never discusses Legion, Babas_Swarms_bot internals, cekwajar, rumahlabuh, or Bashara's projects
- Never breaks character to say "I'm an AI"
- Never gives generic motivation ("ganbatte!" without substance)
- Never uses more than 5 new words per lesson (N5 cognitive load limit)
- Never corrects the same mistake more than once per session without a new example
- Never uses Kanji above N5 level without explicit furigana
- Never assumes Bashara knows something not yet taught
- Never ends with "Ada pertanyaan lain?" — always end with a mini challenge or practice prompt

## SENSEI'S LESSON FLOW
If Bashara doesn't specify a topic:
1. Check lesson history — continue from last session
2. If first session OR >48hr since last session: warm-up review (last 5 words)
3. Introduce ONE new grammar point or vocabulary cluster (max 5 words)
4. Practice with 2-3 example sentences
5. Mini-quiz every 3 exchanges
6. End session with: recap + 1 homework ("Coba pakai kata ini besok di [situasi]"
"""


STORY_MODE_ADDITION = """
## STORY MODE (when sub_mode=story)
Teach through an immersive story set in locations Bashara knows:
- Narita Airport, Keio/Shibaura campus, nearby conbini, train station
- Bashara is the protagonist. The story uses N5 Japanese with furigana.
- Each "scene" ends with a decision that requires Japanese to continue:
  "🔐 Untuk lanjut ke scene berikutnya, jawab dalam Bahasa Jepang:"
  "[question requiring N5 Japanese answer]"
- Wrong answers get gentle correction then story continues.
"""


QUIZ_MODE_ADDITION = """
## QUIZ MODE (when sub_mode=quiz)
Active drilling session. No lesson, just quizzes.
- Format: vocab flash cards OR fill-in-the-blank OR translation challenge
- Score tracker displayed: "🎯 {correct}/{total} | Streak: {streak}"
- After quiz: "Mau belajar kata-kata yang salah tadi?"
- Difficulty auto-adjusts based on error rate:
  >60% correct → introduce slightly harder words
  <40% correct → back to basics, use simpler sentences
"""


FREE_MODE_ADDITION = """
## FREE CONVERSATION MODE (when sub_mode=free)
Bashara can talk about anything in Japanese (or attempting Japanese).
Sensei:
1. Responds naturally in mixed JP/ID/EN
2. Gently corrects mistakes at END of response, not mid-sentence
3. Introduces naturally occurring vocabulary from the conversation
4. Does NOT follow rigid lesson structure
5. Every 5 exchanges: "Btw Bas, kata yang kamu pakai tadi — [word] — ada versi yang lebih natural:"
"""


def build_sensei_system_prompt(session) -> str:
    """Build the complete Sensei system prompt for this session. No Legion content."""
    prompt = SENSEI_BASE

    if session.sub_mode.value == "story":
        prompt += STORY_MODE_ADDITION
    elif session.sub_mode.value == "quiz":
        prompt += QUIZ_MODE_ADDITION
    elif session.sub_mode.value == "free":
        prompt += FREE_MODE_ADDITION

    # Dynamic context
    prompt += f"""

## CURRENT SESSION CONTEXT
- JLPT Level: {session.jlpt_level}
- Sub Mode: {session.sub_mode.value}
- Exchange count this session: {session.exchange_count}
- Furigana: {'ON' if session.show_furigana else 'OFF'}
- Romaji: {'ON' if session.show_romaji else 'OFF'}
- Voice: {'ON — reply with audio' if session.voice_enabled else 'OFF — text only'}
- Words seen this session: {len(session.words_seen)}
- Words mastered: {len(session.words_mastered)}
- Words to review (failed): {session.words_failed[-5:] if session.words_failed else 'none'}
"""

    return prompt
```

---

# ─────────────────────────────────────────────
# PART 4 — VOICE PIPELINE (voice_pipeline.py)
# Inspired by: Ledjob/Japanese_Vocal_Chatbot + 0Xiaohei0/VoiceToJapanese
# ─────────────────────────────────────────────

```python
# skills/nihongo/voice_pipeline.py
"""
Voice Pipeline for Nihongo Mode.
STT: OpenAI Whisper (transcription of Bashara's voice notes)
TTS: VoiceVox (Japanese neural TTS) → fallback: gTTS

Completely isolated from any future Legion voice system.
"""
import os
import io
import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nihongo.voice")

# VoiceVox speaker IDs for personality
# See: https://github.com/VOICEVOX/voicevox_engine
VOICEVOX_SPEAKERS = {
    "zundamon": 3,    # friendly, energetic female
    "metan": 2,       # calm, clear female — best for N5 slow speech
    "tsumugi": 8,     # clear male
    "ritsu": 9,       # deeper male
}
DEFAULT_SPEAKER = "metan"  # clear and slow — best for learning
VOICEVOX_HOST = os.getenv("VOICEVOX_HOST", "http://localhost:50021")


# ───────────────────────────────
# STT — Whisper Transcription
# Based on: antirez/whisperbot + tanmay-pathak/telegram-whisper-bot
# ───────────────────────────────

async def transcribe_voice_note(
    audio_bytes: bytes,
    language: str = "ja",
    use_api: bool = True
) -> str:
    """
    Transcribe voice note using Whisper.
    use_api=True: OpenAI Whisper API (fast, cloud)
    use_api=False: local whisper model (private, slower)
    Language hint 'ja' improves accuracy for Japanese input.
    """
    if use_api:
        return await _transcribe_whisper_api(audio_bytes, language)
    else:
        return await _transcribe_whisper_local(audio_bytes, language)


async def _transcribe_whisper_api(audio_bytes: bytes, language: str) -> str:
    """Uses OpenAI Whisper API — reuses OPENAI_API_KEY from .env"""
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text"
            )

        os.unlink(tmp_path)
        return transcript.strip()

    except Exception as e:
        logger.error(f"Whisper API error: {e}")
        return "[Transcription failed]"


async def _transcribe_whisper_local(audio_bytes: bytes, language: str) -> str:
    """Uses local whisper model. Requires: pip install openai-whisper"""
    try:
        import whisper
        import numpy as np
        import soundfile as sf

        model = whisper.load_model("base")  # base = fast enough for Telegram
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        result = model.transcribe(tmp_path, language=language)
        os.unlink(tmp_path)
        return result["text"].strip()

    except ImportError:
        logger.error("whisper not installed. Run: pip install openai-whisper")
        return "[Local Whisper not available]"
    except Exception as e:
        logger.error(f"Local Whisper error: {e}")
        return "[Transcription failed]"


# ───────────────────────────────
# TTS — VoiceVox Japanese Neural TTS
# Based on: Ledjob/Japanese_Vocal_Chatbot + 0Xiaohei0/VoiceToJapanese
# ───────────────────────────────

async def text_to_speech_japanese(
    text: str,
    speaker: str = DEFAULT_SPEAKER,
    slow_speech: bool = True,
    use_voicevox: bool = True
) -> Optional[bytes]:
    """
    Convert Japanese text to speech.
    Primary: VoiceVox (best quality, needs local Docker)
    Fallback: gTTS (no dependency, lower quality)
    Returns: WAV bytes or None on failure
    """
    # Extract only Japanese parts (strip furigana brackets, romaji, Indonesian)
    jp_text = extract_japanese_only(text)
    if not jp_text.strip():
        return None

    if use_voicevox:
        audio = await _tts_voicevox(jp_text, speaker, slow_speech)
        if audio:
            return audio
        logger.warning("VoiceVox unavailable, falling back to gTTS")

    return await _tts_gtts_fallback(jp_text, slow_speech)


async def _tts_voicevox(
    text: str,
    speaker: str,
    slow: bool
) -> Optional[bytes]:
    """VoiceVox TTS. Requires VoiceVox Engine running locally via Docker."""
    try:
        import httpx
        speaker_id = VOICEVOX_SPEAKERS.get(speaker, 2)

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: audio_query
            r = await client.post(
                f"{VOICEVOX_HOST}/audio_query",
                params={"text": text, "speaker": speaker_id}
            )
            r.raise_for_status()
            query = r.json()

            # Apply slow speech for N5 learners
            if slow:
                query["speedScale"] = 0.75  # 75% speed
                query["pauseLength"] = 1.5   # longer pauses
                query["pauseLengthScale"] = 1.5

            # Step 2: synthesis
            r2 = await client.post(
                f"{VOICEVOX_HOST}/synthesis",
                params={"speaker": speaker_id},
                json=query,
                headers={"Content-Type": "application/json"}
            )
            r2.raise_for_status()
            return r2.content  # WAV bytes

    except Exception as e:
        logger.warning(f"VoiceVox error: {e}")
        return None


async def _tts_gtts_fallback(text: str, slow: bool) -> Optional[bytes]:
    """gTTS fallback. pip install gtts"""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="ja", slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        logger.error(f"gTTS error: {e}")
        return None


def extract_japanese_only(text: str) -> str:
    """Extract only Japanese characters + punctuation from mixed text."""
    import re
    # Keep: hiragana, katakana, kanji, Japanese punctuation
    jp_pattern = re.compile(
        r'[\u3040-\u309F'   # hiragana
        r'\u30A0-\u30FF'   # katakana
        r'\u4E00-\u9FFF'   # CJK unified
        r'\u3000-\u303F'   # JP punctuation
        r'\uFF01-\uFF0F'   # fullwidth
        r'\uFF1A-\uFF20'   # fullwidth
        r'\uFF3B-\uFF40'   # fullwidth
        r'\uFF5B-\uFF65'   # fullwidth
        r'\s]+'
    )
    matches = jp_pattern.findall(text)
    return ' '.join(matches).strip()
```

---

# ─────────────────────────────────────────────
# PART 5 — FURIGANA + ROMAJI ENGINE (furigana.py)
# Critical for N5 — never show bare kanji without reading aid
# ─────────────────────────────────────────────

```python
# skills/nihongo/furigana.py
"""
Furigana and Romaji annotation for Japanese text.
Requires: pip install pykakasi
"""

def annotate_japanese(text: str, show_furigana: bool = True, show_romaji: bool = True) -> str:
    """
    Convert: 学生
    To: 学生(がくせい) [gakusei]
    Or Telegram-safe: 学生(がくせい)
    """
    try:
        import pykakasi
        kks = pykakasi.kakasi()
        result = kks.convert(text)

        output_parts = []
        for item in result:
            orig = item.get("orig", "")
            hira = item.get("hira", "")
            hepburn = item.get("hepburn", "")  # romaji

            if orig == hira or not hira:  # already hiragana/katakana/ascii
                output_parts.append(orig)
            else:
                part = orig
                if show_furigana and hira:
                    part += f"({hira})"
                if show_romaji and hepburn:
                    part += f" [{hepburn}]"
                output_parts.append(part)

        return "".join(output_parts)

    except ImportError:
        return f"{text} [pykakasi not installed]"
    except Exception:
        return text


N5_EXAMPLE_VOCAB = [
    # (kanji, hiragana, romaji, indonesian_meaning)
    ("学生", "がくせい", "gakusei", "mahasiswa/murid"),
    ("先生", "せんせい", "sensei", "guru/dosen"),
    ("大学", "だいがく", "daigaku", "universitas"),
    ("日本語", "にほんご", "nihongo", "bahasa Jepang"),
    ("食べる", "たべる", "taberu", "makan"),
    ("飲む", "のむ", "nomu", "minum"),
    ("行く", "いく", "iku", "pergi"),
    ("来る", "くる", "kuru", "datang"),
    ("見る", "みる", "miru", "melihat"),
    ("込む", "こむ", "komu", "penuh sesak"),
]
```

---

# ─────────────────────────────────────────────
# PART 6 — NIHONGO HANDLER (handlers/nihongo_handler.py)
# This is the main router entry point for all Nihongo Mode messages
# ─────────────────────────────────────────────

```python
# handlers/nihongo_handler.py
"""
Nihongo Mode Handler — completely isolated routing for Japanese teacher mode.
This handler intercepts BEFORE general Legion handlers when mode is active.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode
from skills.nihongo.sensei_prompt import build_sensei_system_prompt
from skills.nihongo.voice_pipeline import transcribe_voice_note, text_to_speech_japanese
from skills.nihongo.vocab_tracker import VocabTracker
from skills.nihongo.quiz_engine import QuizEngine

logger = logging.getLogger("nihongo.handler")


NIHONGO_COMMANDS = {
    "/nihongo": "activate_default",
    "/nihongo chat": "activate_chat",
    "/nihongo voice": "activate_voice",
    "/nihongo quiz": "activate_quiz",
    "/nihongo story": "activate_story",
    "/nihongo free": "activate_free",
    "/nihongo off": "deactivate",
    "/stopp": "deactivate",
    "/nihongo status": "show_status",
    "/nihongo level n4": "set_level_n4",
    "/nihongo level n5": "set_level_n5",
    "/furigana on": "furigana_on",
    "/furigana off": "furigana_off",
    "/romaji on": "romaji_on",
    "/romaji off": "romaji_off",
    "/slow on": "slow_on",
    "/slow off": "slow_off",
}


async def handle_nihongo_command(update: Update, context: ContextTypes) -> bool:
    """
    Handles /nihongo commands. Returns True if command was handled.
    Called from main.py BEFORE any other handler.
    """
    text = update.message.text.strip().lower() if update.message.text else ""
    user_id = update.effective_user.id

    # Activate commands
    if text == "/nihongo" or text.startswith("/nihongo chat"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.CHAT)
        await update.message.reply_text(
            "⛩ *Nihongo Mode ON* | Chat Mode\n\n"
            "Halo Bashara! Sensei siap ngajarin kamu Bahasa Jepang.\n\n"
            "📖 Level: JLPT N5\n"
            "🎙 Voice: OFF (ketik /nihongo voice untuk aktifkan)\n"
            "🎓 Furigana + Romaji: ON\n\n"
            "Mau mulai dari mana?\n"
            "- /nihongo quiz — langsung drilling\n"
            "- /nihongo story — belajar lewat cerita\n"
            "- /nihongo free — ngobrol bebas\n"
            "- Atau langsung ketik aja topik yang mau dipelajari!",
            parse_mode="Markdown"
        )
        return True

    elif text.startswith("/nihongo voice"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.CHAT)
        session.voice_enabled = True
        await update.message.reply_text(
            "⛩ *Nihongo Mode ON* | Voice Mode\n\n"
            "🎙 Kirim voice note → Sensei transkripsi + koreksi + balas dengan suara.\n"
            "Kecepatan: SLOW (75%) — cocok untuk N5.\n"
            "TTS: VoiceVox (neural) atau gTTS jika VoiceVox tidak tersedia.\n\n"
            "Coba kirim voice note dalam Bahasa Jepang — apapun yang kamu bisa!",
            parse_mode="Markdown"
        )
        return True

    elif text.startswith("/nihongo quiz"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.QUIZ)
        await update.message.reply_text(
            "⛩ *Nihongo Mode ON* | Quiz Mode\n\n"
            "🎯 Mulai drilling! Skor kamu: 0/0 | Streak: 0\n"
            "Level: N5 | Vocab flash cards + fill-in-the-blank\n\n"
            "Siap? Ketik \"mulai\" untuk soal pertama!",
            parse_mode="Markdown"
        )
        return True

    elif text in ["/nihongo off", "/stopp"]:
        NihongoModeManager.deactivate(user_id)
        await update.message.reply_text(
            "⛩ Nihongo Mode *OFF*.\n\n"
            "Legion kembali ke mode normal. またね！ (Mata ne! = Sampai jumpa!)\n"
            "Progress kamu tersimpan. Ketik /nihongo kapanpun untuk lanjut.",
            parse_mode="Markdown"
        )
        return True

    elif text == "/nihongo status":
        session = NihongoModeManager.get_session(user_id)
        await update.message.reply_text(
            f"⛩ *Nihongo Mode Status*\n"
            f"Active: {'✅ ON' if session.active else '❌ OFF'}\n"
            f"Level: {session.jlpt_level}\n"
            f"Mode: {session.sub_mode.value}\n"
            f"Voice: {'🎙 ON' if session.voice_enabled else 'OFF'}\n"
            f"Furigana: {'✅' if session.show_furigana else '❌'}\n"
            f"Romaji: {'✅' if session.show_romaji else '❌'}\n"
            f"Words seen: {len(session.words_seen)}\n"
            f"Words mastered: {len(session.words_mastered)}\n"
            f"Exchanges this session: {session.exchange_count}",
            parse_mode="Markdown"
        )
        return True

    return False  # Not a nihongo command, let main handler proceed


async def handle_nihongo_message(update: Update, context: ContextTypes, llm_client) -> None:
    """
    Process a message when Nihongo Mode is active.
    Called INSTEAD of normal Legion processing.
    """
    user_id = update.effective_user.id
    session = NihongoModeManager.get_session(user_id)

    # Handle voice notes
    if update.message.voice:
        await _handle_voice_input(update, context, session, llm_client)
        return

    # Handle text input
    user_text = update.message.text or ""

    # Increment exchange counter (for quiz scheduling)
    exchange_num = NihongoModeManager.increment_exchange(user_id)

    # Build ISOLATED system prompt (no Legion soul, no wiki, no project context)
    system_prompt = build_sensei_system_prompt(session)

    # Add quiz trigger every 3 exchanges
    if exchange_num % 3 == 0 and session.sub_mode != NihongoSubMode.QUIZ:
        system_prompt += "\n\nFORCED: End this response with a mini-quiz question."

    # Build minimal message history (nihongo-only, not Legion's history)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    # Call LLM — use a capable multilingual model
    # Recommended: claude-3-5-haiku (clean JP+ID+EN output, no Chinese leaks)
    # Do NOT use deepseek/qwen for this — Chinese contamination risk
    response_text = await llm_client.chat(
        messages=messages,
        model="claude-3-5-haiku",  # adjust to your OpenRouter model naming
        max_tokens=800,
        temperature=0.7
    )

    # Send text response
    await update.message.reply_text(response_text, parse_mode="Markdown")

    # Send voice if voice mode enabled
    if session.voice_enabled:
        audio_bytes = await text_to_speech_japanese(
            response_text,
            slow_speech=session.slow_speech
        )
        if audio_bytes:
            await update.message.reply_voice(voice=audio_bytes)

    # Track vocab (extract Japanese words from response)
    # VocabTracker handles this asynchronously
    asyncio.create_task(VocabTracker.track_from_response(user_id, response_text))


async def _handle_voice_input(
    update: Update,
    context: ContextTypes,
    session,
    llm_client
) -> None:
    """Process voice note input from Bashara."""
    # Download voice note
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()

    # Notify user we're processing
    processing_msg = await update.message.reply_text("🎙 Transkripsi...")

    # Transcribe with Whisper
    transcription = await transcribe_voice_note(bytes(voice_bytes), language="ja")

    # Show transcription
    await processing_msg.edit_text(
        f"🎙 *Kamu bilang:* {transcription}\n\n🤔 Sensei sedang memproses...",
        parse_mode="Markdown"
    )

    # Process as text in Nihongo Mode
    NihongoModeManager.increment_exchange(session.user_id)
    system_prompt = build_sensei_system_prompt(session)
    system_prompt += f"\n\nBashara sent a voice note. Transcription: '{transcription}'. Evaluate his Japanese pronunciation attempt and continue the lesson."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"[Voice input transcribed]: {transcription}"}
    ]

    response_text = await llm_client.chat(
        messages=messages,
        model="claude-3-5-haiku",
        max_tokens=800,
        temperature=0.7
    )

    # Send text response
    await update.message.reply_text(response_text, parse_mode="Markdown")

    # Always send audio response in voice mode
    audio_bytes = await text_to_speech_japanese(response_text, slow_speech=session.slow_speech)
    if audio_bytes:
        await update.message.reply_voice(voice=audio_bytes)
```

---

# ─────────────────────────────────────────────
# PART 7 — WIRE INTO main.py (MINIMAL TOUCH)
# Only add 5 lines to main.py. Nothing else changes.
# ─────────────────────────────────────────────

Open main.py. Find the main message handler (likely `async def handle_message`).
Add these lines AT THE TOP of the message handler, before anything else:

```python
# === NIHONGO MODE INTERCEPT (add these lines, do not modify anything else) ===
from handlers.nihongo_handler import handle_nihongo_command, handle_nihongo_message
from skills.nihongo.mode_manager import NihongoModeManager

# In handle_message or equivalent:
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # NIHONGO INTERCEPT — runs FIRST, completely isolated
    if update.message and update.message.text and update.message.text.startswith("/nihongo"):
        handled = await handle_nihongo_command(update, context)
        if handled:
            return  # Do not process with Legion

    if NihongoModeManager.is_active(user_id):
        await handle_nihongo_message(update, context, llm_client)
        return  # IMPORTANT: return here. Legion does NOT process this message.
    # === END NIHONGO MODE INTERCEPT ===

    # ... rest of existing Legion message handler (untouched) ...
```

---

# ─────────────────────────────────────────────
# PART 8 — VOICEVOX DOCKER SETUP
# Add to docker-compose.yml for local VoiceVox
# ─────────────────────────────────────────────

Add this service to docker-compose.yml:

```yaml
  voicevox:
    image: voicevox/voicevox_engine:cpu-ubuntu20.04-latest
    container_name: voicevox_engine
    ports:
      - "50021:50021"
    restart: unless-stopped
    # Note: CPU version is sufficient for Telegram TTS latency
    # GPU version available if you have NVIDIA GPU on server
```

Add to .env.example:
```
# Nihongo Mode
VOICEVOX_HOST=http://localhost:50021
NIHONGO_DEFAULT_SPEAKER=metan
NIHONGO_DEFAULT_SPEED=0.75
WHISPER_USE_API=true  # false = local model
```

---

# ─────────────────────────────────────────────
# PART 9 — NEW PACKAGES (add to requirements.txt)
# ─────────────────────────────────────────────

```
# Nihongo Mode — add these to requirements.txt
pykakasi>=2.2.1         # furigana + romaji conversion
gtts>=2.5.0             # TTS fallback (no API key)
httpx>=0.27.0           # VoiceVox API calls (likely already installed)
openai>=1.0.0           # Whisper API (likely already installed)
# Optional local whisper:
# openai-whisper>=20231117  # only if WHISPER_USE_API=false
```

---

# ─────────────────────────────────────────────
# PART 10 — VERIFICATION TESTS
# ─────────────────────────────────────────────

Create tests/test_nihongo_mode.py:

```python
import pytest
from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode
from skills.nihongo.sensei_prompt import build_sensei_system_prompt
from skills.nihongo.furigana import annotate_japanese
from skills.nihongo.voice_pipeline import extract_japanese_only

TEST_USER_ID = 99999  # fake user

def test_isolation_when_off():
    """When Nihongo Mode is OFF, is_active must return False."""
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

    # Must contain Sensei identity
    assert "Sensei" in prompt
    assert "Bashara" in prompt
    assert "N5" in prompt

    # Must NOT contain Legion identity markers
    legion_markers = ["SOUL", "Legion bot", "cekwajar", "rumahlabuh", "MASTER_PROMPT"]
    for marker in legion_markers:
        assert marker not in prompt, f"Legion content leaked: {marker}"

    print("✅ Sensei prompt is fully isolated from Legion")

def test_furigana_annotation():
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

if __name__ == "__main__":
    test_isolation_when_off()
    test_activate_and_deactivate()
    test_sensei_prompt_no_legion_content()
    test_furigana_annotation()
    test_extract_japanese_only()
    test_sub_modes()
    test_exchange_counter()
    print("\n⛩ ALL NIHONGO MODE TESTS PASSED")
    print("Mode is ready. Try: /nihongo in Telegram.")
```

---

# COMMAND REFERENCE (for Bashara)

```
/nihongo              — activate chat mode (default)
/nihongo voice        — activate with voice in/out
/nihongo quiz         — drilling session
/nihongo story        — immersive story mode
/nihongo free         — free conversation with gentle correction
/nihongo off          — turn off, return to normal Legion
/stopp                — same as /nihongo off
/nihongo status       — show current session stats
/nihongo level n4     — upgrade to N4 difficulty
/furigana off         — hide furigana (when you get better)
/romaji off           — hide romaji (when you get better)
/slow off             — normal TTS speed
```

---

# WHAT DOES NOT CHANGE

OpenCode: confirm these files are NEVER modified by this task:
- SOUL.md
- CLAUDE.md
- LEGION_MASTER.md
- main.py (except the 5 intercept lines)
- core/system_prompt_builder.py
- core/character_enforcer.py
- core/wiki_loader.py
- Any existing handler
- Any existing skill

The ONLY additions to existing files:
1. main.py: +5 lines (the intercept block)
2. requirements.txt: +4 packages
3. docker-compose.yml: +1 service (voicevox)
4. .env.example: +4 variables

Everything else is NEW files in skills/nihongo/ and handlers/nihongo_handler.py.

---

*Nihongo Mode — jadi belajar Jepang dari Narita makin asik.*
*またね！(またね) / Mata ne! = Sampai jumpa!*
