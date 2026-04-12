"""Correction engine for Nihongo Mode — grammar/vocab correction logic."""

import logging
import re

logger = logging.getLogger("nihongo.correction")


class CorrectionEngine:
    @classmethod
    def extract_mistakes(cls, user_text: str, expected_text: str) -> list[dict]:
        mistakes = []
        if user_text != expected_text:
            mistakes.append(
                {
                    "type": "wrong_text",
                    "user": user_text,
                    "correct": expected_text,
                }
            )
        return mistakes

    @classmethod
    def format_correction(cls, mistake: dict) -> str:
        if mistake["type"] == "wrong_text":
            return (
                f'❌ Hmm, "{mistake["user"]}" → harusnya "{mistake["correct"]}"\n'
                "Kenapa? [one sentence in Indonesian]\n"
                "✅ Sekarang coba lagi ya."
            )
        return ""

    @classmethod
    def is_close_match(cls, user_text: str, correct_text: str) -> bool:
        user_clean = re.sub(r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "", user_text)
        correct_clean = re.sub(r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "", correct_text)
        if not user_clean or not correct_clean:
            return False
        similarity = sum(1 for a, b in zip(user_clean, correct_clean) if a == b)
        return similarity / max(len(user_clean), len(correct_clean)) > 0.7

    @classmethod
    def format_close_correction(cls, attempt: str, correction: str) -> str:
        return f'👍 Hampir! "{attempt}" → lebih tepatnya "{correction}"\n[one-sentence fix]'
