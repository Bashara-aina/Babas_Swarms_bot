"""Nihongo Mode Toggle System.
Completely isolated from Legion's general state.
Uses its own in-memory dict + Supabase persistence.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger("nihongo.mode_manager")


class NihongoSubMode(Enum):
    CHAT = "chat"
    VOICE = "voice"
    QUIZ = "quiz"
    STORY = "story"
    FREE = "free"


@dataclass
class NihongoSession:
    user_id: int
    active: bool = False
    sub_mode: NihongoSubMode = NihongoSubMode.CHAT
    jlpt_level: str = "N5"
    lesson_count: int = 0
    exchange_count: int = 0
    current_topic: str | None = None
    voice_enabled: bool = False
    slow_speech: bool = True
    show_furigana: bool = True
    show_romaji: bool = True
    started_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    words_seen: list = field(default_factory=list)
    words_mastered: list = field(default_factory=list)
    words_failed: list = field(default_factory=list)
    grammar_seen: list = field(default_factory=list)


class NihongoModeManager:
    _sessions: dict[int, NihongoSession] = {}

    @classmethod
    def get_session(cls, user_id: int) -> NihongoSession:
        if user_id not in cls._sessions:
            cls._sessions[user_id] = NihongoSession(user_id=user_id)
        return cls._sessions[user_id]

    @classmethod
    def is_active(cls, user_id: int) -> bool:
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

    @classmethod
    def set_sub_mode(cls, user_id: int, sub_mode: NihongoSubMode) -> None:
        session = cls.get_session(user_id)
        session.sub_mode = sub_mode
        logger.info(f"Sub mode set to {sub_mode.value} for user {user_id}")

    @classmethod
    def toggle_furigana(cls, user_id: int) -> bool:
        session = cls.get_session(user_id)
        session.show_furigana = not session.show_furigana
        return session.show_furigana

    @classmethod
    def toggle_romaji(cls, user_id: int) -> bool:
        session = cls.get_session(user_id)
        session.show_romaji = not session.show_romaji
        return session.show_romaji

    @classmethod
    def toggle_slow_speech(cls, user_id: int) -> bool:
        session = cls.get_session(user_id)
        session.slow_speech = not session.slow_speech
        return session.slow_speech
