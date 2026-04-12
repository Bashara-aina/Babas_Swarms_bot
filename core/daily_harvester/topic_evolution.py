"""TopicEvolution — detect new topics, decay weights, hibernate dormant ones."""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# Planned feature flags
FEATURE_TOPIC_WEIGHTS_ENABLED = False  # Planned: v2.0

_EXCEPTIONS_NEVER_BELOW_MIN = {"cekwajar", "popw", "babas_bot_ai"}


class TopicEvolution:
    """Handles topic lifecycle: new topic detection, weight decay, hibernate decisions."""

    @staticmethod
    def detect_new_topic(mentions: list[str], days_span: int = 7) -> list[str]:
        """
        Detect emerging topics from a list of mention strings.
        Returns new topics not currently in TOPIC_WEIGHTS.json.
        """
        if not FEATURE_TOPIC_WEIGHTS_ENABLED:
            logger.debug("Topic weights feature is planned for v2.0 — not yet available.")
        # TODO: cross-reference with existing TOPIC_WEIGHTS.json
        # For now, return empty — real implementation needs topic classifier
        new_topics: list[str] = []
        seen: set[str] = set()

        for mention in mentions:
            words = mention.lower().split()
            # Very simple bigram/trigram extraction for candidate topics
            for i in range(len(words) - 1):
                bigram = f"{words[i]}_{words[i + 1]}"
                if bigram not in seen and len(bigram) > 5:
                    seen.add(bigram)
                    new_topics.append(bigram)

        return new_topics[:5]

    @staticmethod
    def decay_topic_weight(topic: str, days_since_mention: int) -> float:
        """
        Apply decay to a topic weight given days since last mention.

        Rules:
        - 14 days no mention → weight halved
        - 30 days → weight at minimum (3 slots)
        - 60 days → hibernate (weight → 0)

        Exceptions (never below min): cekwajar, popw, babas_bot_ai
        """
        if days_since_mention < 14:
            return 1.0  # no decay

        # Check exceptions
        is_exception = any(exc in topic.lower() for exc in _EXCEPTIONS_NEVER_BELOW_MIN)

        if days_since_mention >= 60:
            return 0.0  # hibernate

        if days_since_mention >= 30:
            return 0.15 if is_exception else 0.0  # minimum viable

        # 14-29 days: exponential decay
        decay_rate = 0.95  # ~5% decay per day
        decay_factor = math.pow(decay_rate, days_since_mention - 14)
        return max(0.1, decay_factor)

    @staticmethod
    def should_hibernate(topic: str, days_since_mention: int) -> bool:
        """
        Return True if a topic should be hibernated.

        Rules:
        - 60+ days no mention → hibernate
        - Exceptions (cekwajar, popw, babas_bot_ai) → never hibernate
        """
        if days_since_mention < 60:
            return False

        # Check exceptions
        for exc in _EXCEPTIONS_NEVER_BELOW_MIN:
            if exc in topic.lower():
                return False

        return True
