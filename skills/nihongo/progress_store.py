"""Progress store for Nihongo Mode — Supabase adapter (isolated namespace)."""

import logging
from collections import OrderedDict

logger = logging.getLogger("nihongo.progress_store")

MAX_CACHE_SIZE = 200


class ProgressStore:
    _cache: OrderedDict[int, dict] = OrderedDict()

    @classmethod
    def get_user_progress(cls, user_id: int) -> dict:
        if user_id not in cls._cache:
            if len(cls._cache) >= MAX_CACHE_SIZE:
                cls._cache.popitem(last=False)  # evict oldest
            cls._cache[user_id] = {
                "words_seen": [],
                "words_mastered": [],
                "words_failed": [],
                "grammar_seen": [],
                "lesson_count": 0,
            }
        else:
            cls._cache.move_to_end(user_id)  # mark as recently used
        return cls._cache[user_id]

    @classmethod
    async def save_progress(cls, user_id: int, progress: dict) -> None:
        cls._cache[user_id] = progress
        logger.info(f"Progress saved for user {user_id}")

    @classmethod
    async def load_progress(cls, user_id: int) -> dict:
        return cls.get_user_progress(user_id)

    @classmethod
    def add_word_seen(cls, user_id: int, word: str) -> None:
        progress = cls.get_user_progress(user_id)
        if word not in progress["words_seen"]:
            progress["words_seen"].append(word)

    @classmethod
    def add_word_mastered(cls, user_id: int, word: str) -> None:
        progress = cls.get_user_progress(user_id)
        if word not in progress["words_mastered"]:
            progress["words_mastered"].append(word)
        if word in progress["words_failed"]:
            progress["words_failed"].remove(word)

    @classmethod
    def add_word_failed(cls, user_id: int, word: str) -> None:
        progress = cls.get_user_progress(user_id)
        if word not in progress["words_failed"]:
            progress["words_failed"].append(word)
