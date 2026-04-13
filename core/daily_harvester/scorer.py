"""Scorer — feedback-aware relevance scoring for harvest candidates.

Applies bias adjustments derived from user accept/reject feedback collected
via the Telegram /harvest-review interface.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "harvest"
BIAS_FILE = DATA_DIR / "score_bias.json"

# Default bias adjustments (multiplicative modifiers applied to topic scores)
DEFAULT_BIAS: dict[str, float] = {
    "topic_drift": -0.15,
    "low_quality": -0.20,
    "duplicate": -0.10,
    "not_relevant": -0.25,
    "outdated": -0.10,
    "unreliable_source": -0.20,
    "accepted": 0.05,
}

REASON_CODES = list(DEFAULT_BIAS.keys())


class Scorer:
    """Feedback-aware relevance scorer."""

    def __init__(self) -> None:
        self._bias: dict[str, float] = {}
        self._load_bias_sync()

    def _load_bias_sync(self) -> None:
        """Load bias from file (sync, called on init)."""
        if BIAS_FILE.exists():
            try:
                self._bias = json.loads(BIAS_FILE.read_text())
                logger.info("Scorer bias loaded: %s", self._bias)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not load bias file: %s — using defaults", e)
                self._bias = DEFAULT_BIAS.copy()
        else:
            self._bias = DEFAULT_BIAS.copy()

    async def load_bias(self) -> dict[str, float]:
        """Load bias from file (async)."""
        if BIAS_FILE.exists():
            try:
                async with aiofiles.open(BIAS_FILE, encoding="utf-8") as f:
                    content = await f.read()
                self._bias = json.loads(content)
                logger.info("Scorer bias loaded: %s", self._bias)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not load bias file: %s", e)
                self._bias = DEFAULT_BIAS.copy()
        else:
            self._bias = DEFAULT_BIAS.copy()
        return self._bias

    async def save_bias(self) -> None:
        """Persist current bias to file."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(BIAS_FILE, encoding="utf-8", mode="w") as f:
            await f.write(json.dumps(self._bias, indent=2))

    def get_bias(self) -> dict[str, float]:
        """Return current bias vector."""
        return self._bias.copy()

    async def apply_bias(self, topic: str, base_score: float) -> float:
        """Apply topic-specific bias to a base score.

        If the topic has a history of rejections, bias is negative;
        acceptances push it slightly up.
        """
        await self.load_bias()
        topic_bias = self._bias.get(topic, 0.0)
        adjusted = base_score + topic_bias
        return max(0.0, min(1.0, adjusted))

    async def update_from_feedback(
        self,
        decisions: list[dict[str, str]],
    ) -> dict[str, float]:
        """Update bias vector from a list of feedback decisions.

        Each decision dict: {"reason": str, "decision": str}
        Returns the delta applied to each bias key.
        """
        await self.load_bias()

        # Count feedback by reason
        counts: dict[str, int] = {}
        for d in decisions:
            reason = d.get("reason", "unknown")
            decision = d.get("decision", "")
            if decision == "rejected":
                counts[reason] = counts.get(reason, 0) + 1
            elif decision == "accepted":
                counts["accepted"] = counts.get("accepted", 0) + 1

        if not counts:
            return {}

        # Apply incremental update: each rejection shifts bias by -0.05
        delta: dict[str, float] = {}
        for reason, count in counts.items():
            if reason not in self._bias:
                self._bias[reason] = DEFAULT_BIAS.get(reason, -0.10)
            change = -0.05 * count if reason != "accepted" else 0.02 * count
            self._bias[reason] += change
            # Clamp bias to [-0.5, +0.3]
            self._bias[reason] = max(-0.50, min(0.30, self._bias[reason]))
            delta[reason] = change

        await self.save_bias()

        # Log to scores history
        await self._append_history({"decisions": decisions, "delta": delta, "bias": self._bias.copy()})

        logger.info("Scorer bias updated: %s", {k: f"{v:+.2f}" for k, v in delta.items()})
        return delta

    async def _append_history(self, entry: dict) -> None:
        """Append a scoring update entry to scores_history.jsonl."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        history_file = DATA_DIR / "scores_history.jsonl"
        entry["timestamp"] = datetime.now(timezone.utc).timestamp()
        async with aiofiles.open(history_file, encoding="utf-8", mode="a") as f:
            await f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def score_candidate(
        self,
        candidate: dict,
        topic: str,
        base_score: float | None = None,
    ) -> float:
        """Score a single candidate, applying feedback bias.

        Returns score in [0.0, 1.0].
        """
        if base_score is None:
            base_score = candidate.get("relevance_score", 0.5)
        score = await self.apply_bias(topic, base_score)
        # Boost if source is high-trust
        url = candidate.get("url", "")
        if any(domain in url for domain in ["arxiv.org", "github.com", "wikipedia.org"]):
            score = min(1.0, score + 0.05)
        return round(score, 3)
