"""Vocab tracker for Nihongo Mode — tracks words seen/failed/mastered."""

import logging
import re

logger = logging.getLogger("nihongo.vocab")


class VocabTracker:
    _user_vocab: dict[int, dict[str, dict]] = {}

    @classmethod
    def get_user_vocab(cls, user_id: int) -> dict[str, dict]:
        if user_id not in cls._user_vocab:
            cls._user_vocab[user_id] = {}
        return cls._user_vocab[user_id]

    @classmethod
    async def track_from_response(cls, user_id: int, response_text: str) -> None:
        japanese_words = cls._extract_japanese_words(response_text)
        user_vocab = cls.get_user_vocab(user_id)

        for word, reading in japanese_words:
            if word not in user_vocab:
                user_vocab[word] = {
                    "reading": reading,
                    "seen_count": 0,
                    "failed_count": 0,
                    "mastered": False,
                }
            user_vocab[word]["seen_count"] += 1

    @classmethod
    def mark_failed(cls, user_id: int, word: str) -> None:
        user_vocab = cls.get_user_vocab(user_id)
        if word in user_vocab:
            user_vocab[word]["failed_count"] += 1
            if user_vocab[word]["failed_count"] >= 3:
                user_vocab[word]["mastered"] = False

    @classmethod
    def mark_mastered(cls, user_id: int, word: str) -> None:
        user_vocab = cls.get_user_vocab(user_id)
        if word in user_vocab:
            user_vocab[word]["mastered"] = True
            user_vocab[word]["failed_count"] = 0

    @classmethod
    def get_words_to_review(cls, user_id: int, limit: int = 5) -> list[dict]:
        user_vocab = cls.get_user_vocab(user_id)
        reviewable = [w for w in user_vocab.values() if not w["mastered"] and w["seen_count"] > 0]
        reviewable.sort(key=lambda x: (x["failed_count"], x["seen_count"]), reverse=True)
        return reviewable[:limit]

    @classmethod
    def _extract_japanese_words(cls, text: str) -> list[tuple[str, str]]:
        import pykakasi

        kks = pykakasi.kakasi()
        words = []

        kanji_pattern = re.compile(r"[\u4E00-\u9FFF]+")
        kanji_words = kanji_pattern.findall(text)

        for word in kanji_words:
            try:
                result = kks.convert(word)
                if result:
                    reading = result[0].get("hira", "")
                    words.append((word, reading))
            except Exception:
                pass

        return words
