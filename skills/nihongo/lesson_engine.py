"""Lesson engine for Nihongo Mode — curriculum, levels, spaced repetition."""

import logging
import random
from typing import Optional

logger = logging.getLogger("nihongo.lesson")

N5_TOPICS = [
    "greetings",
    "self_introduction",
    "numbers",
    "time",
    "dates",
    "directions",
    "university",
    "shopping",
    "food",
    "keigo",
    "grammar_wa",
    "grammar_ga",
    "grammar_wo",
    "grammar_ni",
    "grammar_de",
    "grammar_ka",
    "grammar_ne",
    "grammar_yo",
    "grammar_kara",
    "grammar_made",
    "katakana",
    "emergency",
]


class LessonEngine:
    _user_progress: dict[int, dict] = {}

    @classmethod
    def get_user_progress(cls, user_id: int) -> dict:
        if user_id not in cls._user_progress:
            cls._user_progress[user_id] = {
                "current_topic": None,
                "completed_topics": [],
                "lesson_count": 0,
                "last_lesson": None,
            }
        return cls._user_progress[user_id]

    @classmethod
    def get_next_topic(cls, user_id: int) -> str:
        progress = cls.get_user_progress(user_id)
        available = [t for t in N5_TOPICS if t not in progress["completed_topics"]]
        if not available:
            available = N5_TOPICS
        return random.choice(available)

    @classmethod
    def advance_lesson(cls, user_id: int) -> None:
        progress = cls.get_user_progress(user_id)
        progress["lesson_count"] += 1
        topic = cls.get_next_topic(user_id)
        progress["current_topic"] = topic

    @classmethod
    def complete_topic(cls, user_id: int, topic: str) -> None:
        progress = cls.get_user_progress(user_id)
        if topic not in progress["completed_topics"]:
            progress["completed_topics"].append(topic)

    @classmethod
    def should_review(cls, user_id: int, word: str) -> bool:
        progress = cls.get_user_progress(user_id)
        review_words = progress.get("review_words", [])
        return word in review_words

    @classmethod
    def schedule_review(cls, user_id: int, word: str) -> None:
        progress = cls.get_user_progress(user_id)
        if "review_words" not in progress:
            progress["review_words"] = []
        if word not in progress["review_words"]:
            progress["review_words"].append(word)
