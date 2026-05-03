"""Scorer — feedback-aware relevance scoring for harvest candidates.

Applies bias adjustments derived from user accept/reject feedback collected
via the Telegram /harvest-review interface.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
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

    async def load_harvest_feedback(
        self,
        log_path: Path | None = None,
        lookback_days: int = 30,
    ) -> dict[str, float]:
        """Read harvest-log.md, extract accept/reject patterns, return bias deltas.

        Parses each YAML+JSON log session entry from the last {lookback_days} days.
        For each accepted candidate: boost its topic/tag bias slightly.
        For each rejected candidate: penalize its topic/tag more strongly.
        Returns a dict of {topic_tag: delta} representing the net adjustment
        to apply to the current bias vector.
        """
        import re
        from datetime import datetime, timedelta

        if log_path is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            log_path = repo_root / ".wiki" / "legion" / "harvester" / "harvest-log.md"

        if not log_path.exists():
            logger.info("No harvest log found at %s — skipping feedback load", log_path)
            return {}

        try:
            content = log_path.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("Could not read harvest log: %s", e)
            return {}

        # Split into individual entries separated by --- markers
        # Each entry starts with --- then YAML frontmatter then JSON block
        cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
        topic_scores: dict[str, float] = {}  # topic → cumulative delta
        topic_counts: dict[str, int] = {}    # topic → count for weighting

        # Match JSON blocks that follow YAML frontmatter
        json_blocks = re.findall(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
        for block in json_blocks:
            block = block.strip()
            if not block:
                continue
            try:
                entry = json.loads(block)
            except json.JSONDecodeError:
                continue

            # Parse date from frontmatter or entry
            entry_date_str = entry.get("date", "")
            try:
                entry_date = datetime.fromisoformat(entry_date_str).replace(tzinfo=UTC)
            except (ValueError, TypeError):
                continue

            if entry_date < cutoff:
                continue

            for candidate in entry.get("candidates_reviewed", []):
                decision = candidate.get("decision", "")
                tags = candidate.get("tags", [])
                topic = candidate.get("topic", "")
                reason = candidate.get("reason", "")

                # Use topic, first tag, or reason as the bias key
                key = topic or (tags[0] if tags else reason or "unknown")

                if decision == "accepted":
                    delta = 0.02
                elif decision == "rejected":
                    delta = -0.05
                else:
                    continue

                topic_scores[key] = topic_scores.get(key, 0.0) + delta
                topic_counts[key] = topic_counts.get(key, 0) + 1

        if not topic_scores:
            logger.info("No harvest feedback entries found in last %d days", lookback_days)
            return {}

        # Clamp deltas and return only non-zero ones
        result = {}
        for key, raw_delta in topic_scores.items():
            count = topic_counts[key]
            # Scale delta by inverse count (many small adjustments vs. few strong ones)
            adjusted = raw_delta * (1.0 / (1.0 + 0.1 * count))
            clamped = max(-0.3, min(0.3, adjusted))
            if abs(clamped) >= 0.01:
                result[key] = clamped

        logger.info(
            "Loaded harvest feedback: %d topics adjusted over %d days",
            len(result),
            lookback_days,
        )
        return result

    async def apply_loaded_feedback(self, deltas: dict[str, float]) -> None:
        """Apply pre-computed bias deltas to the current bias vector."""
        await self.load_bias()
        for key, delta in deltas.items():
            self._bias[key] = self._bias.get(key, 0.0) + delta
            self._bias[key] = max(-0.5, min(0.3, self._bias[key]))
        await self.save_bias()
        logger.info("Applied harvest feedback deltas: %s", {k: f"{v:+.2f}" for k, v in deltas.items()})

    async def _append_history(self, entry: dict) -> None:
        """Append a scoring update entry to scores_history.jsonl."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        history_file = DATA_DIR / "scores_history.jsonl"
        entry["timestamp"] = datetime.now(UTC).timestamp()
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
