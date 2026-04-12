"""MasteryGate — Bloom's Taxonomy 2-Sigma Mastery Learning.

Implements Bloom's cognitive levels for adaptive question difficulty
and tracks mastery per item with sigma scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BloomLevel(Enum):
    """Bloom's taxonomy cognitive levels (lower = easier)."""

    REMEMBER = 1  # Recall facts, define terms
    UNDERSTAND = 2  # Explain concepts in own words
    APPLY = 3  # Use in new situation
    ANALYZE = 4  # Break down relationships
    EVALUATE = 5  # Judge and critique
    CREATE = 6  # Produce original work


@dataclass
class MasteryRecord:
    """Record of user's mastery level for an item."""

    item: str
    level: BloomLevel
    sigma: float  # 2-sigma ≈ 95% accuracy = mastered
    attempts: int = 0
    correct_count: int = 0
    last_attempt: datetime = field(default_factory=datetime.now)


def mastery_gate(item: str, level: BloomLevel):
    """Decorator to tag questions/lessons with Bloom difficulty level.

    Usage:
        @mastery_gate("学生", BloomLevel.REMEMBER)
        def vocab_quiz():
            pass
    """

    def decorator(func):
        func._bloom_level = level
        func._bloom_item = item
        return func

    return decorator


class MasteryGate:
    """Bloom's Taxonomy Mastery Gate for Nihongo Mode.

    Tracks each word/grammar point at which level the user has achieved
    mastery (2-sigma = ~95% accuracy). Implements adaptive difficulty
    selection based on mastery level.
    """

    # Keywords for classifying question difficulty
    BLOOM_KEYWORDS = {
        BloomLevel.REMEMBER: [
            "apa arti",
            "apa artinya",
            "arti",
            "meaning",
            "define",
            "apa itu",
            "sebutkan",
            "tuliskan",
            "bacalah",
            "apa",
            "siapa",
            "dimana",
            "kapan",
            "berapa",
            "apa bahasa Jepangnya",
            "terjemahkan",
        ],
        BloomLevel.UNDERSTAND: [
            "jelaskan",
            "explain",
            "apa bedanya",
            "beda antara",
            "kenapa",
            "mengapa",
            "bagaimana",
            "caranya",
            "menjelaskan",
            "deskripsikan",
            "artinya",
            "yang mana",
            "termasuk",
            "adalah",
        ],
        BloomLevel.APPLY: [
            "gunakan",
            "gunakan dalam kalimat",
            "buat kalimat",
            "buat kalimat dengan",
            "tulis kalimat",
            "susuns kalimat",
            "demonstrasikan",
            "praktekkan",
            "coba",
            "tolong",
            "silakan",
        ],
        BloomLevel.ANALYZE: [
            "analisis",
            "bandingkan",
            "bedakan",
            "apa hubungan",
            "mengapa bisa",
            "mengapa harus",
            "sebab",
            "akibat",
            "karena",
            "komponen",
        ],
        BloomLevel.EVALUATE: [
            "evaluasi",
            "kritik",
            "setujukah",
            "menurutmu",
            "lebih baik",
            "pilihan",
            "putuskan",
            "rekomendasikan",
            "sebaiknya",
            "seharusnya",
            "bagaimana kalau",
        ],
        BloomLevel.CREATE: [
            "buat cerita",
            "ciptakan",
            "rumuskan",
            "design",
            "rencanakan",
            "kembangkan",
            "tulis dialog",
            "buat dialog",
            "arang",
        ],
    }

    # Minimum sigma for each Bloom level
    LEVEL_SIGMA_THRESHOLDS = {
        BloomLevel.REMEMBER: 0.5,
        BloomLevel.UNDERSTAND: 1.0,
        BloomLevel.APPLY: 1.5,
        BloomLevel.ANALYZE: 1.8,
        BloomLevel.EVALUATE: 2.0,
        BloomLevel.CREATE: 2.5,
    }

    def __init__(self) -> None:
        # In-memory: user_id -> {item -> MasteryRecord}
        self._mastery: dict[int, dict[str, MasteryRecord]] = {}

    def classify_question(self, text: str) -> BloomLevel:
        """Classify a question's Bloom level based on keywords.

        Args:
            text: The question text (Indonesian, English, or mixed)

        Returns:
            BloomLevel classification
        """
        text_lower = text.lower()

        for level in BloomLevel:
            for keyword in self.BLOOM_KEYWORDS.get(level, []):
                if keyword in text_lower:
                    return level

        # Default to REMEMBER for basic translation prompts
        return BloomLevel.REMEMBER

    def evaluate_mastery(self, user_id: int, item: str) -> tuple[BloomLevel, float]:
        """Evaluate current mastery level and sigma for an item.

        Args:
            user_id: The user's ID
            item: The item identifier (word, grammar, etc.)

        Returns:
            Tuple of (current BloomLevel, sigma score)
        """
        if user_id not in self._mastery or item not in self._mastery[user_id]:
            return BloomLevel.REMEMBER, 0.0

        record = self._mastery[user_id][item]
        return record.level, record.sigma

    def record_attempt(self, user_id: int, item: str, correct: bool, level: BloomLevel) -> MasteryRecord:
        """Record a user's attempt on an item.

        Args:
            user_id: The user's ID
            item: The item identifier
            correct: Whether the attempt was correct
            level: The Bloom level of the question

        Returns:
            Updated MasteryRecord
        """
        if user_id not in self._mastery:
            self._mastery[user_id] = {}

        if item not in self._mastery[user_id]:
            self._mastery[user_id][item] = MasteryRecord(
                item=item,
                level=BloomLevel.REMEMBER,
                sigma=0.0,
            )

        record = self._mastery[user_id][item]
        record.attempts += 1
        record.last_attempt = datetime.now()

        # Update sigma (2-sigma ≈ 95% mastery)
        if correct:
            record.sigma = min(3.0, record.sigma + 0.3)
            if record.sigma >= self.LEVEL_SIGMA_THRESHOLDS.get(level, 2.0):
                # Achieved mastery at this level
                if level.value > record.level.value:
                    record.level = level
        else:
            record.sigma = max(0.0, record.sigma - 0.4)
            record.correct_count += 0  # Already incremented below if correct

        if correct:
            record.correct_count += 1

        return record

    def get_mastery_level(self, user_id: int, item: str) -> BloomLevel:
        """Get the highest Bloom level the user has achieved mastery for."""
        if user_id not in self._mastery or item not in self._mastery[user_id]:
            return BloomLevel.REMEMBER

        return self._mastery[user_id][item].level

    def get_next_difficulty(self, user_id: int, current_item: str) -> str:
        """Get next recommended difficulty/item based on mastery gaps.

        Args:
            user_id: The user's ID
            current_item: The current item being studied

        Returns:
            Identifier for next item to study, or current item if at limit
        """
        if user_id not in self._mastery or current_item not in self._mastery[user_id]:
            return current_item

        record = self._mastery[user_id][current_item]

        # Find items at same level that haven't been mastered
        if user_id in self._mastery:
            for item, rec in self._mastery[user_id].items():
                if item != current_item and rec.level == record.level and rec.sigma < 2.0:
                    return item

        # Progress to next level if mastered
        if record.sigma >= 2.0 and record.level.value < BloomLevel.CREATE.value:
            next_level = BloomLevel(record.level.value + 1)
            # Return guidance for next level
            return f"next:{next_level.name.lower()}"

        return current_item

    def get_mastery_distribution(self, user_id: int) -> dict[BloomLevel, int]:
        """Get distribution of items across Bloom levels.

        Returns:
            Dict mapping BloomLevel to count of items at that level
        """
        if user_id not in self._mastery:
            return {level: 0 for level in BloomLevel}

        distribution = {level: 0 for level in BloomLevel}
        for record in self._mastery[user_id].values():
            distribution[record.level] += 1

        return distribution

    def get_mastery_percentage(self, user_id: int) -> float:
        """Get overall mastery percentage (items at 2-sigma or higher)."""
        if user_id not in self._mastery or not self._mastery[user_id]:
            return 0.0

        mastered = sum(1 for r in self._mastery[user_id].values() if r.sigma >= 2.0)
        return (mastered / len(self._mastery[user_id])) * 100.0
