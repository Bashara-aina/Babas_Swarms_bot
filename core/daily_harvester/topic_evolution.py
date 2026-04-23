"""TopicEvolution — detect new topics, decay weights, hibernate dormant ones."""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_EXCEPTIONS_NEVER_BELOW_MIN = {"cekwajar", "popw", "babas_bot_ai"}
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOPIC_WEIGHTS_PATH = REPO_ROOT / ".wiki" / "knowledge" / "TOPIC_WEIGHTS.json"


class TopicEvolution:
    """Handles topic lifecycle: new topic detection, weight decay, hibernate decisions."""

    @staticmethod
    def detect_new_topic(mentions: list[str], days_span: int = 7) -> list[str]:
        """
        Detect emerging topics from a list of mention strings.
        Returns new topics not currently in TOPIC_WEIGHTS.json.
        """
        _ = days_span
        existing: set[str] = set()
        try:
            if TOPIC_WEIGHTS_PATH.exists():
                payload = json.loads(TOPIC_WEIGHTS_PATH.read_text(encoding="utf-8"))
                existing = {str(k).lower() for k in (payload.get("topics", {}) or {}).keys()}
        except (OSError, ValueError) as exc:
            logger.debug("Failed reading topic weights for cross-reference: %s", exc)

        gram_counts: Counter[str] = Counter()
        for mention in mentions:
            words = re.findall(r"[a-z0-9]+", mention.lower())
            if len(words) < 2:
                continue
            for i in range(len(words) - 1):
                bigram = f"{words[i]}_{words[i + 1]}"
                if len(bigram) > 5:
                    gram_counts[bigram] += 1
            for i in range(len(words) - 2):
                trigram = f"{words[i]}_{words[i + 1]}_{words[i + 2]}"
                if len(trigram) > 8:
                    gram_counts[trigram] += 1

        discovered = [
            gram
            for gram, count in gram_counts.most_common()
            if count >= 2 and gram not in existing
        ]
        return discovered[:5]

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
