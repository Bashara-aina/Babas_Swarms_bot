"""Quiz engine for Nihongo Mode — auto-quiz after N exchanges."""

import logging
import random

logger = logging.getLogger("nihongo.quiz")


class QuizEngine:
    _user_scores: dict[int, dict] = {}

    @classmethod
    def get_user_score(cls, user_id: int) -> dict:
        if user_id not in cls._user_scores:
            cls._user_scores[user_id] = {
                "correct": 0,
                "total": 0,
                "streak": 0,
                "best_streak": 0,
            }
        return cls._user_scores[user_id]

    @classmethod
    def record_answer(cls, user_id: int, correct: bool) -> dict:
        score = cls.get_user_score(user_id)
        score["total"] += 1
        if correct:
            score["correct"] += 1
            score["streak"] += 1
            if score["streak"] > score["best_streak"]:
                score["best_streak"] = score["streak"]
        else:
            score["streak"] = 0
        return score

    @classmethod
    def get_quiz_status(cls, user_id: int) -> str:
        score = cls.get_user_score(user_id)
        return f"🎯 {score['correct']}/{score['total']} | Streak: {score['streak']}"

    @classmethod
    def generate_vocab_quiz(cls, user_id: int, words: list[dict]) -> str | None:
        if not words:
            return None

        word = random.choice(words)
        quiz_types = ["meaning", "reading", "fill_blank"]
        quiz_type = random.choice(quiz_types)

        if quiz_type == "meaning":
            return (
                f"Apa arti dari: {word.get('word', word.get('orig', '?'))} "
                f"({word.get('reading', '')})?\n"
                f"Ayo cobain jawab!"
            )
        elif quiz_type == "reading":
            return f"Bagaimana bacaan dari: {word.get('word', '?')}?\n(petunjuk: {word.get('meaning', '')})"
        else:
            return f"Lengkapi: {word.get('hint', '___')} = {word.get('meaning', '')}"

    @classmethod
    def reset_session(cls, user_id: int) -> None:
        if user_id in cls._user_scores:
            cls._user_scores[user_id] = {
                "correct": 0,
                "total": 0,
                "streak": 0,
                "best_streak": 0,
            }
