# /home/newadmin/swarm-bot/optimization/feedback_learner.py
"""Continuous learning from user feedback.

Stores thumbs-up/down ratings for agent responses.
Uses feedback to:
  1. Adjust agent selection heuristics (in-memory weight adjustment).
  2. Warm/evict semantic cache entries based on rating.
  3. Surface worst-performing agents in /stats report.

Backends: Redis (preferred) or in-memory dict (fallback).
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)

# Rating constants
POSITIVE = 1
NEGATIVE = -1


@dataclass
class FeedbackEntry:
    timestamp: float
    agent: str
    task_hash: str        # sha256[:16] of task text
    task_preview: str     # first 80 chars
    rating: int           # +1 or -1
    comment: str = ""


class FeedbackLearner:
    """Collect ratings, adjust agent weights, report trends.

    Thread-safe via asyncio (no sync mutation outside async context).
    """

    def __init__(self) -> None:
        self._redis: object = None
        # in-memory fallback: {agent: {"pos": int, "neg": int}}
        self._scores: dict[str, dict[str, int]] = defaultdict(lambda: {"pos": 0, "neg": 0})
        # recent entries (capped at 500)
        self._recent: list[FeedbackEntry] = []
        # pending: maps short ID → (agent, task) for Telegram /feedback flow
        self._pending: dict[str, tuple[str, str]] = {}
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis as redis_lib
            import os
            r = redis_lib.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True,
                socket_connect_timeout=2,
            )
            r.ping()
            self._redis = r
            logger.info("FeedbackLearner connected to Redis")
        except Exception:
            logger.info("FeedbackLearner: Redis unavailable, using in-memory")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_response(self, agent: str, task: str) -> str:
        """Register a completed response and return a short feedback ID.

        Call after every agent response so the user can rate it.
        Returns a 6-char alphanumeric ID.
        """
        import hashlib, random, string
        fid = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self._pending[fid] = (agent, task)
        # expire after 10 minutes (cleaned up lazily)
        return fid

    def record(
        self,
        fid: str,
        rating: int,
        comment: str = "",
    ) -> Optional[str]:
        """Record a rating for a pending feedback ID.

        Args:
            fid: ID returned by register_response().
            rating: POSITIVE (+1) or NEGATIVE (-1).
            comment: Optional free-text from user.

        Returns:
            Human-readable confirmation string, or error message.
        """
        if fid not in self._pending:
            return f"Unknown feedback ID: {fid}"

        agent, task = self._pending.pop(fid)

        import hashlib
        task_hash = hashlib.sha256(task.encode()).hexdigest()[:16]
        entry = FeedbackEntry(
            timestamp=time.time(),
            agent=agent,
            task_hash=task_hash,
            task_preview=task[:80],
            rating=rating,
            comment=comment,
        )
        self._store(entry)
        self._update_cache(agent, task, rating)

        label = "positive" if rating == POSITIVE else "negative"
        logger.info("Feedback %s for agent=%s task_hash=%s", label, agent, task_hash)
        return f"Thanks! Recorded {label} feedback for <code>{agent}</code>."

    def record_by_agent(self, agent: str, task: str, rating: int, comment: str = "") -> None:
        """Direct record without going through the pending ID flow (internal use)."""
        import hashlib
        task_hash = hashlib.sha256(task.encode()).hexdigest()[:16]
        entry = FeedbackEntry(
            timestamp=time.time(),
            agent=agent,
            task_hash=task_hash,
            task_preview=task[:80],
            rating=rating,
            comment=comment,
        )
        self._store(entry)
        self._update_cache(agent, task, rating)

    def get_agent_score(self, agent: str) -> dict[str, int | float]:
        """Return pos/neg counts and satisfaction rate for an agent."""
        scores = self._load_scores(agent)
        total = scores["pos"] + scores["neg"]
        rate = (scores["pos"] / total * 100) if total else 0.0
        return {"pos": scores["pos"], "neg": scores["neg"], "total": total, "rate": round(rate, 1)}

    def agent_weights(self) -> dict[str, float]:
        """Return a weight multiplier (0.5–1.5) per agent based on feedback.

        Used by model_router to bias agent selection.
        Higher = preferred, lower = avoid.
        """
        weights: dict[str, float] = {}
        for agent in self._all_agents():
            score = self.get_agent_score(agent)
            if score["total"] < 5:
                weights[agent] = 1.0   # not enough data
                continue
            rate = score["rate"] / 100.0
            # scale: 0% → 0.5, 50% → 1.0, 100% → 1.5
            weights[agent] = 0.5 + rate
        return weights

    def summary_report(self) -> str:
        """Return HTML-formatted feedback summary for /stats."""
        lines = ["<b>Agent Feedback Summary</b>\n"]
        any_data = False
        for agent in self._all_agents():
            score = self.get_agent_score(agent)
            if score["total"] == 0:
                continue
            any_data = True
            bar = "▓" * int(score["rate"] / 10) + "░" * (10 - int(score["rate"] / 10))
            lines.append(
                f"  <code>{agent:10}</code> {bar} {score['rate']}%"
                f" (+{score['pos']}/-{score['neg']})"
            )
        if not any_data:
            return "No feedback recorded yet."
        return "\n".join(lines)

    def recent_negatives(self, limit: int = 5) -> list[FeedbackEntry]:
        """Return most recent negative feedback entries."""
        negs = [e for e in self._recent if e.rating == NEGATIVE]
        return negs[-limit:]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _store(self, entry: FeedbackEntry) -> None:
        """Persist entry and update scores."""
        agent = entry.agent
        key_prefix = f"swarm:feedback:{agent}"

        if self._redis:
            field = "pos" if entry.rating == POSITIVE else "neg"
            self._redis.hincrby(f"{key_prefix}:scores", field, 1)
            # Store entry in list (cap at 500 per agent)
            entry_json = json.dumps(asdict(entry))
            self._redis.lpush(f"{key_prefix}:entries", entry_json)
            self._redis.ltrim(f"{key_prefix}:entries", 0, 499)
        else:
            field = "pos" if entry.rating == POSITIVE else "neg"
            self._scores[agent][field] += 1

        # Always keep in _recent
        self._recent.append(entry)
        if len(self._recent) > 500:
            self._recent = self._recent[-500:]

    def _load_scores(self, agent: str) -> dict[str, int]:
        if self._redis:
            raw = self._redis.hgetall(f"swarm:feedback:{agent}:scores")
            return {
                "pos": int(raw.get("pos", 0)),
                "neg": int(raw.get("neg", 0)),
            }
        return {"pos": self._scores[agent]["pos"], "neg": self._scores[agent]["neg"]}

    def _update_cache(self, agent: str, task: str, rating: int) -> None:
        """Evict cache entry if feedback is negative."""
        if rating == NEGATIVE:
            try:
                from memory.semantic_cache import get_cache
                cache = get_cache()
                # Evict by overwriting with a sentinel — simplest approach
                # since SemanticCache doesn't expose a delete API
                cache.set(task, agent, "__EVICTED__")
                logger.debug("Evicted cache for agent=%s due to negative feedback", agent)
            except Exception:
                pass

    def _all_agents(self) -> list[str]:
        try:
            from agents import AGENT_MODELS
            return list(AGENT_MODELS.keys())
        except Exception:
            return ["vision", "coding", "debug", "math", "architect", "mentor", "analyst"]


# Singleton
_learner: FeedbackLearner | None = None


def get_learner() -> FeedbackLearner:
    """Return global FeedbackLearner singleton."""
    global _learner
    if _learner is None:
        _learner = FeedbackLearner()
    return _learner
