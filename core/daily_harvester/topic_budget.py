"""Topic budget detection and allocation for the daily harvester."""

from __future__ import annotations

import json
import logging
import math
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_ROOT = REPO_ROOT / ".wiki" / "knowledge"
TOPIC_WEIGHTS_PATH = WIKI_ROOT / "TOPIC_WEIGHTS.json"

_EXCEPTIONS_NEVER_BELOW_MIN = {"cekwajar", "popw", "babas_bot_ai"}


async def _load_topic_weights() -> dict[str, Any]:
    """Load TOPIC_WEIGHTS.json asynchronously."""
    if not TOPIC_WEIGHTS_PATH.exists():
        return {"topics": {}}
    try:
        import aiofiles

        async with aiofiles.open(TOPIC_WEIGHTS_PATH, encoding="utf-8") as f:
            content = await f.read()
        return json.loads(content)
    except Exception as e:
        logger.warning("Failed to load TOPIC_WEIGHTS.json: %s", e)
        return {"topics": {}}


@lru_cache(maxsize=8)
def _recent_commit_subjects(days: int) -> tuple[str, ...]:
    """Return recent git commit subjects (cached per day-window)."""
    try:
        proc = subprocess.run(
            [
                "git",
                "--no-pager",
                "log",
                f"--since={days} days ago",
                "--pretty=%s",
                "--no-merges",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            logger.debug("git log returned non-zero (%s): %s", proc.returncode, proc.stderr.strip())
            return ()
        lines = [line.strip().lower() for line in proc.stdout.splitlines() if line.strip()]
        return tuple(lines)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("git log analysis unavailable: %s", exc)
        return ()


def _days_since(ts: str) -> float:
    """Days elapsed since an ISO timestamp string."""
    try:
        then = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(then.tzinfo) if then.tzinfo else datetime.now()
        return (now - then).total_seconds() / 86400
    except Exception:
        return 999.0


def _get_git_commit_count(topic: str, days: int = 3) -> int:
    """Count recent commits that mention the topic slug or its tokens."""
    subjects = _recent_commit_subjects(days)
    if not subjects:
        return 0

    normalized_topic = topic.lower().replace("-", "_").strip("_")
    topic_tokens = [t for t in normalized_topic.split("_") if t]
    count = 0
    for subject in subjects:
        if normalized_topic in subject:
            count += 1
            continue
        if topic_tokens and all(token in subject for token in topic_tokens):
            count += 1
    return count


async def detect_active_topics(
    telegram_days: int = 7,
    git_days: int = 3,
) -> dict[str, int]:
    """
    Detect active topics based on Telegram mentions, git commits, wiki updates,
    and TOPIC_WEIGHTS.json state.

    Weight formula:
      mention_count × 2 + commit_count × 3 + (days_since_last_update)^0.5

    Returns a dict of topic -> slots (normalized to 100 total, min 3, max 35 per topic).
    Reserved surprise slots: 5.
    """
    weights_data = await _load_topic_weights()
    topics_state: dict[str, dict[str, Any]] = weights_data.get("topics", {})

    # Build raw scores per topic
    raw_scores: dict[str, float] = {}

    for topic, state in topics_state.items():
        mention_count = int(state.get("mention_count", 1) or 1)
        commit_count = _get_git_commit_count(topic, git_days)
        days_since = _days_since(state.get("last_mentioned", "2026-01-01"))
        decay = state.get("decay_days", 14)
        base_weight = state.get("weight", 5)

        # Apply decay if no recent mention
        if days_since > decay:
            base_weight = base_weight * 0.5

        score = mention_count * 2 + commit_count * 3 + math.sqrt(days_since)
        raw_scores[topic] = score

    # Normalize to 100 total slots
    total_raw = sum(raw_scores.values())
    if total_raw == 0:
        raw_scores = {k: 1.0 for k in topics_state}

    total_raw = sum(raw_scores.values())
    budget: dict[str, int] = {}
    surprise_slots = 5
    remaining = 100 - surprise_slots

    for topic, raw in sorted(raw_scores.items(), key=lambda x: -x[1]):
        fraction = raw / total_raw
        slots = max(3, min(35, round(remaining * fraction)))

        # Exceptions never go below min 3
        for exc in _EXCEPTIONS_NEVER_BELOW_MIN:
            if exc in topic and slots < 3:
                slots = 3

        budget[topic] = slots

    budget["surprise_discoveries"] = surprise_slots

    # Normalize to exact 100 total (fixes rounding errors)
    budget = normalize_budget(budget, total=100)

    logger.info("Topic budget allocated: %s", budget)
    return budget


def normalize_budget(budget: dict[str, int], total: int = 100) -> dict[str, int]:
    """Ensure budget sums to total by scaling proportionally."""
    current = sum(budget.values())
    if current == 0 or current == total:
        return budget

    scale = total / current
    scaled = {k: int(v * scale) for k, v in budget.items()}
    # Adjust for rounding
    diff = total - sum(scaled.values())
    if scaled:
        largest = max(scaled, key=scaled.get)
        scaled[largest] += diff

    return scaled
