"""SRSEngine — Spaced Repetition System using SM-2 Algorithm.

Implements the SM-2 spaced repetition algorithm for optimal review scheduling.
Cards are scheduled based on user performance to maximize retention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class SRSCard:
    """Individual SRS card tracking one vocabulary/grammar item.

    Attributes:
        item_id: Unique identifier (word, grammar pattern, etc.)
        ease_factor: Difficulty multiplier (default 2.5, min 1.3)
        interval: Days until next review
        repetitions: Number of successful reviews in a row
        next_review: Date of next scheduled review
        last_review: Date of last review
        sigma: Mastery sigma score (2-sigma ≈ 95% accuracy = mastered)
    """

    item_id: str
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    next_review: datetime = field(default_factory=datetime.now)
    last_review: datetime = field(default_factory=datetime.now)
    sigma: float = 0.0

    def is_mastered(self) -> bool:
        """Check if card has reached 2-sigma mastery (interval > 21 days)."""
        return self.interval > 21 and self.sigma >= 2.0


class SRSEngine:
    """SM-2 Spaced Repetition Engine for Nihongo Mode.

    Implements the SuperMemo 2 algorithm for scheduling reviews at
    optimal intervals for long-term retention.
    """

    # Quality ratings for SM-2
    QUALITY_FAIL = (0, 1, 2)  # Complete blackout, wrong, serious difficulty
    QUALITY_PASS = (3, 4, 5)  # Correct with difficulty, correct, perfect

    def __init__(self) -> None:
        # In-memory storage: user_id -> {item_id -> SRSCard}
        self._cards: dict[int, dict[str, SRSCard]] = {}

    def add_card(self, user_id: int, item: str) -> SRSCard:
        """Create a new SRS card for an item.

        Args:
            user_id: The user's ID
            item: The item identifier (word, grammar pattern, etc.)

        Returns:
            The newly created SRSCard
        """
        if user_id not in self._cards:
            self._cards[user_id] = {}

        # Don't duplicate if card already exists
        if item in self._cards[user_id]:
            return self._cards[user_id][item]

        card = SRSCard(item_id=item)
        self._cards[user_id][item] = card
        return card

    def get_card(self, user_id: int, item: str) -> Optional[SRSCard]:
        """Get a specific card for a user."""
        return self._cards.get(user_id, {}).get(item)

    def record_review(self, user_id: int, item: str, quality: int) -> SRSCard:
        """Record a review outcome and calculate next review date.

        SM-2 Algorithm:
        - quality 0-2: fail (reset repetitions, shorten interval)
        - quality 3-5: pass (increase repetitions, extend interval)

        Args:
            user_id: The user's ID
            item: The item identifier
            quality: Review quality 0-5 (0-2=fail, 3-5=pass)

        Returns:
            The updated SRSCard with new interval and next_review
        """
        if user_id not in self._cards or item not in self._cards[user_id]:
            self.add_card(user_id, item)

        card = self._cards[user_id][item]
        card.last_review = datetime.now()

        interval, ef, rep = self.calculate_next_review(card, quality)
        card.interval = interval
        card.ease_factor = ef
        card.repetitions = rep
        card.next_review = datetime.now() + timedelta(days=interval)

        # Update sigma (2-sigma ≈ 95% correct)
        # Track rolling accuracy for sigma calculation
        if quality >= 3:
            # Update sigma based on successful reviews
            card.sigma = min(3.0, card.sigma + 0.2 * (quality - 2))
        else:
            # Decrease sigma on failure
            card.sigma = max(0.0, card.sigma - 0.5)

        return card

    def calculate_next_review(self, card: SRSCard, quality: int) -> tuple[int, float, int]:
        """Calculate next interval and ease factor using SM-2 formula.

        SM-2 Formula:
        - If quality < 3: reset to beginning (repetitions = 0, interval = 1)
        - If quality >= 3:
          - repetitions = 0 → interval = 1
          - repetitions = 1 → interval = 6
          - repetitions >= 2 → interval = previous_interval * ease_factor
        - Ease factor adjusted based on quality

        Args:
            card: The current SRSCard
            quality: Review quality 0-5

        Returns:
            Tuple of (new_interval_days, new_ease_factor, new_repetitions)
        """
        ef = card.ease_factor
        rep = card.repetitions
        interval = card.interval

        if quality < 3:
            new_rep = 0
            new_interval = 1
            new_ef = max(1.3, ef - 0.2)
        else:
            new_ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            new_ef = max(1.3, new_ef)

            if rep == 0:
                new_interval = 1
            elif rep == 1:
                new_interval = 6
            else:
                new_interval = int(interval * new_ef)

            new_rep = rep + 1

        return new_interval, new_ef, new_rep

    def get_due_cards(self, user_id: int) -> list[SRSCard]:
        """Get all cards due for review.

        Args:
            user_id: The user's ID

        Returns:
            List of SRSCard objects that are due (next_review <= now)
        """
        if user_id not in self._cards:
            return []

        now = datetime.now()
        due = [card for card in self._cards[user_id].values() if card.next_review <= now]
        return sorted(due, key=lambda c: c.next_review)

    def get_overdue_cards(self, user_id: int) -> list[SRSCard]:
        """Get cards that are overdue for review."""
        if user_id not in self._cards:
            return []

        now = datetime.now()
        overdue = [card for card in self._cards[user_id].values() if card.next_review < now]
        return sorted(overdue, key=lambda c: c.next_review)

    def get_mastery_percentage(self, user_id: int) -> float:
        """Calculate overall mastery percentage based on 2-sigma cards.

        A card is considered "mastered" when it has interval > 21 days
        and sigma >= 2.0 (approximately 95% retention).

        Args:
            user_id: The user's ID

        Returns:
            Percentage 0.0-100.0 of cards mastered
        """
        if user_id not in self._cards or not self._cards[user_id]:
            return 0.0

        cards = list(self._cards[user_id].values())
        mastered = sum(1 for c in cards if c.is_mastered())
        return (mastered / len(cards)) * 100.0

    def get_all_cards(self, user_id: int) -> list[SRSCard]:
        """Get all cards for a user."""
        return list(self._cards.get(user_id, {}).values())

    def get_mastered_items(self, user_id: int) -> list[str]:
        """Get list of mastered item IDs."""
        if user_id not in self._cards:
            return []
        return [c.item_id for c in self._cards[user_id].values() if c.is_mastered()]

    def get_failed_items(self, user_id: int) -> list[str]:
        """Get items that user has failed (sigma < 1.0)."""
        if user_id not in self._cards:
            return []
        return [c.item_id for c in self._cards[user_id].values() if c.sigma < 1.0]
