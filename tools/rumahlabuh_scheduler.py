"""
rumahlabuh Scheduler — time-windowed post scheduler with analytics.

Features:
- morning(3)/afternoon(4)/night(2) post window configuration
- schedule_window() → list of post slots for a given day
- Seed/date determinism for reproducible thread generation
- Analytics integration for tracking generated threads + performance
- reevaluate_previous_threads() to score and improve based on engagement
- Survey methods for FYP-worthiness determination
- Graceful fallback when pools are sparse
- Backward compatible CLI entry point
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from tools.persistence import add_scheduled_task, get_active_tasks, init_db, record_task_execution

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────

TOOLS_DIR = Path(__file__).parent
SCHEDULER_HISTORY = TOOLS_DIR / "rumahlabuh_scheduler_history.json"
ANALYTICS_DB = TOOLS_DIR / "rumahlabuh_analytics.json"
FACTS_PATH = TOOLS_DIR / "rumahlabuh_facts.json"
BLUEPRINTS_PATH = TOOLS_DIR / "rumahlabuh_thread_blueprints.json"


# ── Analytics data helpers ────────────────────────────────────────────────────


def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_json(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Window config ─────────────────────────────────────────────────────────────


@dataclass
class WindowConfig:
    """Post window for one time period."""
    name: str           # e.g. "morning"
    label: str          # e.g. "Pagi"
    start_hour: int      # 0-23
    end_hour: int        # 0-23 (exclusive)
    post_count: int      # number of posts in this window
    weight: float = 1.0  # relative weight for slot distribution


@dataclass
class SchedulerConfig:
    """Full scheduler configuration."""
    windows: list[WindowConfig] = field(default_factory=lambda: [
        WindowConfig(name="morning", label="Pagi",     start_hour=6,  end_hour=10, post_count=3, weight=1.0),
        WindowConfig(name="afternoon", label="Siang", start_hour=12, end_hour=17, post_count=4, weight=1.2),
        WindowConfig(name="night", label="Malam",     start_hour=19, end_hour=22, post_count=2, weight=0.9),
    ])
    default_date: str = ""  # ISO date for default schedule
    seed_date_format: str = "%Y-%m-%d"

    def total_posts_per_day(self) -> int:
        return sum(w.post_count for w in self.windows)


# ── Post slot ─────────────────────────────────────────────────────────────────


@dataclass
class PostSlot:
    """One scheduled post slot."""
    slot_index: int      # 0-based global slot index
    window_name: str
    window_label: str
    hour: int            # scheduled hour (0-23)
    minute: int          # scheduled minute
    post_number: int     # 1-6 within a thread
    thread_seed: str     # seed used to generate this thread
    generated_at: float  # timestamp when slot was generated


@dataclass
class ScheduledDay:
    """A day's scheduled post slots."""
    date_iso: str
    slots: list[PostSlot]
    thread_signatures: list[str]  # dedupe keys for threads scheduled this day


# ── Analytics ────────────────────────────────────────────────────────────────


@dataclass
class ThreadAnalytics:
    """Analytics for a single thread."""
    date_iso: str
    signature: str
    technique: str
    pronouns: str
    engagement_score: float = 0.0
    views: int = 0
    likes: int = 0
    replies: int = 0
    quotes: int = 0
    bookmarks: int = 0
    fyp_worthy: bool = False
    scheduled_at: float = 0.0
    posted_at: float = 0.0
    survey_completed: bool = False


class AnalyticsStore:
    """Track thread generation and performance."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or ANALYTICS_DB
        self.data: dict[str, Any] = _load_json(self.path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.data.setdefault("threads", [])
        self.data.setdefault("daily_summaries", {})
        self.data.setdefault("fyp_candidates", [])
        self.data.setdefault("last_reevaluate", "")

    def save(self) -> None:
        _save_json(self.path, self.data)

    def record_generated(self, date_iso: str, sig: str, technique: str, pronouns: str) -> None:
        thread: dict[str, Any] = {
            "date_iso": date_iso,
            "signature": sig,
            "technique": technique,
            "pronouns": pronouns,
            "engagement_score": 0.0,
            "views": 0,
            "likes": 0,
            "replies": 0,
            "quotes": 0,
            "bookmarks": 0,
            "fyp_worthy": False,
            "scheduled_at": time.time(),
            "posted_at": 0.0,
            "survey_completed": False,
        }
        # avoid duplicates
        existing = {t["signature"]: i for i, t in enumerate(self.data["threads"])}
        if sig in existing:
            self.data["threads"][existing[sig]].update(thread)
        else:
            self.data["threads"].append(thread)
        self.save()

    def record_posted(self, sig: str, posted_at: float) -> None:
        for t in self.data["threads"]:
            if t["signature"] == sig:
                t["posted_at"] = posted_at
                break
        self.save()

    def update_engagement(self, sig: str, views: int = 0, likes: int = 0,
                          replies: int = 0, quotes: int = 0, bookmarks: int = 0) -> float:
        """Update engagement metrics. Returns computed engagement_score."""
        for t in self.data["threads"]:
            if t["signature"] == sig:
                t["views"] = max(t.get("views", 0), views)
                t["likes"] = max(t.get("likes", 0), likes)
                t["replies"] = max(t.get("replies", 0), replies)
                t["quotes"] = max(t.get("quotes", 0), quotes)
                t["bookmarks"] = max(t.get("bookmarks", 0), bookmarks)
                score = self._compute_score(t)
                t["engagement_score"] = score
                break
        self.save()
        return self._compute_score(t) if sig else 0.0

    def _compute_score(self, t: dict[str, Any]) -> float:
        """Compute engagement score from metrics."""
        views    = t.get("views", 0)
        likes    = t.get("likes", 0)
        replies  = t.get("replies", 0)
        quotes   = t.get("quotes", 0)
        bookmarks = t.get("bookmarks", 0)
        if views == 0:
            return 0.0
        return round(
            (likes * 1.0 + replies * 2.0 + quotes * 3.0 + bookmarks * 1.5) / views * 100, 4
        )

    def get_thread(self, sig: str) -> dict[str, Any] | None:
        for t in self.data["threads"]:
            if t["signature"] == sig:
                return t
        return None

    def get_recent_threads(self, days: int = 7, limit: int = 50) -> list[dict[str, Any]]:
        cutoff = time.time() - days * 86400
        return [
            t for t in self.data["threads"]
            if t.get("scheduled_at", 0) >= cutoff
        ][:limit]

    def get_top_performers(self, limit: int = 10) -> list[dict[str, Any]]:
        return sorted(
            self.data["threads"],
            key=lambda t: t.get("engagement_score", 0),
            reverse=True,
        )[:limit]

    def set_fyp_worthy(self, sig: str, fyp: bool) -> None:
        for t in self.data["threads"]:
            if t["signature"] == sig:
                t["fyp_worthy"] = fyp
                if fyp and sig not in self.data["fyp_candidates"]:
                    self.data["fyp_candidates"].append(sig)
                break
        self.save()

    def record_survey(self, sig: str, responses: dict[str, Any]) -> None:
        for t in self.data["threads"]:
            if t["signature"] == sig:
                t["survey_responses"] = responses
                t["survey_completed"] = True
                break
        self.save()


# ── Survey ────────────────────────────────────────────────────────────────────


@dataclass
class SurveyResponse:
    """Response from a FYP-worthiness survey."""
    signature: str
    views: int
    likes: int
    replies: int
    saves: int
    screenshot_url: str = ""
    notes: str = ""


class SurveyAnalyzer:
    """Analyze survey responses to determine FYP-worthiness."""

    def __init__(self) -> None:
        self.min_likes_for_fyp = 15
        self.min_replies_for_fyp = 3
        self.min_score_for_fyp = 0.5

    def analyze(self, response: SurveyResponse) -> dict[str, Any]:
        """Determine FYP-worthiness based on survey data."""
        likes = response.likes
        replies = response.replies
        saves = response.saves

        # Basic threshold check
        meets_thresholds = (
            likes >= self.min_likes_for_fyp and
            replies >= self.min_replies_for_fyp
        )

        # Compute a simple engagement rate
        likes + replies + saves
        fyp_likelihood: float = 0.0

        if likes > 50:
            fyp_likelihood = 0.9
        elif likes > 30:
            fyp_likelihood = 0.75
        elif likes > 15:
            fyp_likelihood = 0.6
        elif meets_thresholds:
            fyp_likelihood = 0.4
        else:
            fyp_likelihood = 0.15

        # Boost for high reply ratio
        if replies > 0 and likes / replies < 5:
            fyp_likelihood = min(1.0, fyp_likelihood + 0.1)

        return {
            "signature": response.signature,
            "fyp_worthy": fyp_likelihood >= self.min_score_for_fyp,
            "fyp_likelihood": fyp_likelihood,
            "likes": likes,
            "replies": replies,
            "saves": saves,
            "meets_thresholds": meets_thresholds,
            "notes": response.notes,
        }

    def bulk_analyze(self, responses: list[SurveyResponse]) -> list[dict[str, Any]]:
        return [self.analyze(r) for r in responses]


# ── Thread reevaluation ───────────────────────────────────────────────────────


class ThreadReevaluator:
    """Score and improve previously generated threads."""

    def __init__(self, analytics: AnalyticsStore) -> None:
        self.analytics = analytics

    def score_thread(self, sig: str) -> float:
        """Return engagement score for a thread."""
        t = self.analytics.get_thread(sig)
        if not t:
            return 0.0
        return t.get("engagement_score", 0.0)

    def get_weak_threads(self, threshold: float = 0.3) -> list[dict[str, Any]]:
        """Return threads below engagement threshold."""
        return [
            t for t in self.analytics.data.get("threads", [])
            if 0 < (t.get("engagement_score", 0) or 0) < threshold * 100
        ]

    def suggest_improvements(self, sig: str) -> list[str]:
        """Generate improvement suggestions for a weak thread."""
        t = self.analytics.get_thread(sig)
        if not t:
            return []
        suggestions: list[str] = []
        score = t.get("engagement_score", 0)

        if score < 20:
            suggestions.append("Technique may need stronger hook in first post")
        if t.get("replies", 0) < 2:
            suggestions.append("Post 5/6 questions may not be engaging enough — try more relatable scenarios")
        if t.get("likes", 0) < 10:
            suggestions.append("Content may feel generic — add more specific details (location, price)")
        if not t.get("fyp_worthy", False):
            suggestions.append("Review engagement pattern — similar threads may need different technique rotation")
        return suggestions

    def reevaluate_previous_threads(self, days_back: int = 14) -> dict[str, Any]:
        """Re-evaluate recent threads and return analysis summary."""
        cutoff = time.time() - days_back * 86400
        threads = [
            t for t in self.analytics.data.get("threads", [])
            if t.get("scheduled_at", 0) >= cutoff
        ]

        if not threads:
            return {"status": "no_threads", "days_back": days_back}

        total = len(threads)
        scored = [t for t in threads if t.get("engagement_score", 0) > 0]
        weak = self.get_weak_threads(threshold=0.3)

        top = self.analytics.get_top_performers(limit=5)
        bottom = sorted(threads, key=lambda t: t.get("engagement_score", 0))[:5]

        summary = {
            "status": "complete",
            "days_back": days_back,
            "total_threads": total,
            "scored_threads": len(scored),
            "weak_threads": len(weak),
            "average_score": round(
                sum(t.get("engagement_score", 0) for t in threads) / total, 4
            ) if total else 0.0,
            "top_5_signatures": [t["signature"] for t in top],
            "bottom_5_signatures": [t["signature"] for t in bottom],
            "weak_thread_signatures": [t["signature"] for t in weak],
            "all_techniques": list(set(t.get("technique", "") for t in threads)),
        }

        self.analytics.data["last_reevaluate"] = datetime.now().isoformat()
        self.analytics.save()
        return summary


# ── Seeded thread generation ─────────────────────────────────────────────────


class SeededThreadGenerator:
    """Generate threads with seed/date determinism for reproducibility."""

    def __init__(self, facts_path: Path | None = None, blueprints_path: Path | None = None) -> None:
        self.facts_path = facts_path or FACTS_PATH
        self.blueprints_path = blueprints_path or BLUEPRINTS_PATH
        self._facts_cache: str = ""
        self._blueprints_cache: dict[str, Any] = {}

    def _load_facts(self) -> str:
        if not self._facts_cache:
            self._facts_cache = self.facts_path.read_text(encoding="utf-8")
        return self._facts_cache

    def _load_blueprints(self) -> dict[str, Any]:
        if not self._blueprints_cache:
            self._blueprints_cache = json.loads(self.blueprints_path.read_text(encoding="utf-8"))
        return self._blueprints_cache

    def generate_with_seed(self, date_iso: str, seed_suffix: str = "") -> dict[str, Any]:
        """Generate a thread with deterministic seed from date."""
        combined = f"{date_iso}:{seed_suffix}"
        seed_int = int(hashlib.sha1(combined.encode()).hexdigest()[:8], 16)

        rng = random.Random(seed_int)
        blueprints = self._load_blueprints()

        blueprints.get("pools", {})
        techniques = blueprints.get("techniques", [])

        if not techniques:
            return {"success": False, "error": "No techniques available in blueprints"}

        technique = rng.choice(techniques)
        pronouns_options = [["gue", "lo"], ["aku", "kamu"]]
        pronouns = rng.choice(pronouns_options)

        posts: list[str] = []
        templates = technique.get("posts", {})
        for idx in range(1, 7):
            choices = templates.get(str(idx), [])
            if choices:
                selected = rng.choice(choices)
                posts.append(selected)
            else:
                posts.append(f"{idx}/6 placeholder")

        sig_raw = "\n".join(posts).lower()
        sig = hashlib.sha1(sig_raw.encode()).hexdigest()

        return {
            "success": True,
            "thread": posts,
            "pronouns": pronouns,
            "technique": technique.get("name", "unknown"),
            "signature": sig,
            "date": date_iso,
            "seed_used": combined,
        }


# ── Fallback pool ─────────────────────────────────────────────────────────────


class FallbackPool:
    """Graceful fallback when primary pools are sparse."""

    def __init__(self) -> None:
        self.default_posts = [
            "1/6 Kost di Solo itu banyak banget, tapi yang jujur soal kondisi asli itu cuma…",
            "2/6 Pertama, lokasi. Banyak yang cuma tau label 'dekat kampus' tanpa bilang udah jauh dari akses utama.",
            "3/6 Kedua, fasilitas. AC ada di kertas, tapi pas datang belum tentu berfungsi.",
            "4/6 Dan yang paling sering bikin kecewa: harga. Ada yang mulai murah, tapi biaya tambahan nggak kejelasan.",
            "5/6 Lo pernah masuk kost yang beda sama fotonya? Apa yang paling bikin kecewa?",
            "6/6 Cek kost yang udah gue verifikasi langsung di rumahlabuh.com — semua condition tracked.",
        ]
        self.default_techniques = [
            "edu_detail", "listicle_angka", "storytelling_pendek",
            "hot_take", "data_driven", "pain_point_terbalik",
        ]

    def get_fallback_thread(self, date_iso: str) -> dict[str, Any]:
        """Return a fallback thread when primary generation fails."""
        rng = random.Random(hash(date_iso) & 0xFFFFFFFF)
        sig_base = f"fallback:{date_iso}"
        sig = hashlib.sha1(sig_base.encode()).hexdigest()

        return {
            "success": True,
            "thread": self.default_posts.copy(),
            "pronouns": ["gue", "lo"],
            "technique": rng.choice(self.default_techniques),
            "signature": sig,
            "date": date_iso,
            "is_fallback": True,
        }

    def is_sparse(self, pools: dict[str, list[str]], threshold: int = 3) -> bool:
        """Return True if all pools are below threshold."""
        if not pools:
            return True
        return all(len(v) < threshold for v in pools.values() if v)


# ── Main Scheduler ────────────────────────────────────────────────────────────


class Scheduler:
    """Time-windowed post scheduler for rumahlabuh threads."""

    def __init__(
        self,
        config: SchedulerConfig | None = None,
        analytics: AnalyticsStore | None = None,
        thread_generator: SeededThreadGenerator | None = None,
        facts_path: Path | None = None,
    ) -> None:
        self.config = config or SchedulerConfig()
        self.analytics = analytics or AnalyticsStore()
        self.thread_gen = thread_generator or SeededThreadGenerator(facts_path=facts_path)
        self._history: list[dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        data = _load_json(SCHEDULER_HISTORY)
        self._history = data.get("schedule_history", [])

    def _save_history(self) -> None:
        path = SCHEDULER_HISTORY
        _save_json(path, {"schedule_history": self._history[-500:]})

    def schedule_window(self, date_iso: str) -> list[dict[str, Any]]:
        """Return list of post slots for a given day.

        Each slot: slot_index, window_name, window_label, hour, minute,
        post_number, thread_seed, generated_at
        """
        try:
            datetime.strptime(date_iso, "%Y-%m-%d").date()
        except ValueError:
            date.today()

        slots: list[PostSlot] = []
        slot_index = 0

        for window in self.config.windows:
            total = window.post_count
            # Distribute posts evenly within the window
            window_duration = window.end_hour - window.start_hour
            step = window_duration / total if total > 0 else 1

            for post_idx in range(total):
                # Compute hour within window
                hour = int(window.start_hour + post_idx * step)
                minute = int((window.start_hour + (post_idx + 0.5) * step - hour) * 60) % 60

                # Determine post number (1-6) based on slot_index
                post_number = (slot_index % 6) + 1

                # Seed based on date + window + post_idx for determinism
                seed_suffix = f"{window.name}:{post_idx}"
                thread_seed = hashlib.sha1(
                    f"{date_iso}:{seed_suffix}".encode()
                ).hexdigest()[:12]

                slot = PostSlot(
                    slot_index=slot_index,
                    window_name=window.name,
                    window_label=window.label,
                    hour=hour,
                    minute=minute,
                    post_number=post_number,
                    thread_seed=thread_seed,
                    generated_at=time.time(),
                )
                slots.append(slot)
                slot_index += 1

        # Record in analytics
        for slot in slots:
            # Create a pseudo-signature for scheduled slots
            pseudo_sig = hashlib.sha1(
                f"{date_iso}:{slot.window_name}:{slot.slot_index}".encode()
            ).hexdigest()
            self.analytics.record_generated(
                date_iso=date_iso,
                sig=pseudo_sig,
                technique=f"scheduled_{slot.window_name}",
                pronouns="gue/lo",
            )

        self.save_schedule(date_iso, slots)

        return [
            {
                "slot_index": s.slot_index,
                "window_name": s.window_name,
                "window_label": s.window_label,
                "hour": s.hour,
                "minute": s.minute,
                "post_number": s.post_number,
                "thread_seed": s.thread_seed,
                "generated_at": s.generated_at,
            }
            for s in slots
        ]

    def save_schedule(self, date_iso: str, slots: list[PostSlot]) -> None:
        entry = {
            "date_iso": date_iso,
            "saved_at": time.time(),
            "slots": [
                {
                    "slot_index": s.slot_index,
                    "window_name": s.window_name,
                    "hour": s.hour,
                    "minute": s.minute,
                    "post_number": s.post_number,
                    "thread_seed": s.thread_seed,
                }
                for s in slots
            ],
            "thread_signatures": list(set(
                hashlib.sha1(f"{date_iso}:{s.window_name}:{s.slot_index}".encode()).hexdigest()
                for s in slots
            )),
        }
        self._history.append(entry)
        self._save_history()

    def generate_thread_for_slot(self, slot: dict[str, Any]) -> dict[str, Any]:
        """Generate a thread for a specific scheduled slot."""
        date_iso = slot.get("date_iso", datetime.now().strftime("%Y-%m-%d"))
        thread_seed = slot.get("thread_seed", "")

        result = self.thread_gen.generate_with_seed(date_iso, seed_suffix=thread_seed)

        if result.get("success") and result.get("signature"):
            self.analytics.record_generated(
                date_iso=date_iso,
                sig=result["signature"],
                technique=result.get("technique", "unknown"),
                pronouns=":".join(result.get("pronouns", [])),
            )

        return result

    def reevaluate_previous_threads(self, days_back: int = 14) -> dict[str, Any]:
        """Score and improve previously generated threads based on engagement."""
        reevaluator = ThreadReevaluator(self.analytics)
        return reevaluator.reevaluate_previous_threads(days_back=days_back)

    def run_survey(self, sig: str, views: int = 0, likes: int = 0,
                   replies: int = 0, saves: int = 0,
                   notes: str = "") -> dict[str, Any]:
        """Run a FYP-worthiness survey for a thread."""
        response = SurveyResponse(
            signature=sig,
            views=views,
            likes=likes,
            replies=replies,
            saves=saves,
            notes=notes,
        )
        analyzer = SurveyAnalyzer()
        result = analyzer.analyze(response)

        if result["fyp_worthy"]:
            self.analytics.set_fyp_worthy(sig, True)

        self.analytics.record_survey(sig, result)
        return result

    def get_analytics_summary(self) -> dict[str, Any]:
        """Return analytics summary."""
        threads = self.analytics.get_recent_threads(days=7)
        top = self.analytics.get_top_performers(limit=5)
        fyp_candidates = self.analytics.data.get("fyp_candidates", [])

        total = len(threads)
        scored = [t for t in threads if t.get("engagement_score", 0) > 0]

        return {
            "total_scheduled_7d": total,
            "scored_threads": len(scored),
            "top_5_signatures": [t["signature"] for t in top],
            "fyp_candidate_count": len(fyp_candidates),
            "last_reevaluate": self.analytics.data.get("last_reevaluate", ""),
        }


# ── CLI entry point ────────────────────────────────────────────────────────────


async def run_scheduler_async() -> None:
    """Async scheduler runner for cron/API use."""
    await init_db()
    scheduler = Scheduler()
    today = datetime.now().strftime("%Y-%m-%d")
    slots = scheduler.schedule_window(today)
    logger.info("Scheduled %d slots for %s", len(slots), today)
    for slot in slots:
        logger.info("  slot %d: %s window, hour %02d:%02d, post %d",
                    slot["slot_index"], slot["window_name"],
                    slot["hour"], slot["minute"], slot["post_number"])


def run_scheduler() -> None:
    """Sync entry point (backward compatible with existing CLI)."""
    asyncio.run(run_scheduler_async())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    scheduler = Scheduler()

    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")

    print(f"Scheduling posts for {date_arg}:")
    slots = scheduler.schedule_window(date_arg)
    for slot in slots:
        print(f"  [{slot['slot_index']}] {slot['window_label']} {slot['hour']:02d}:{slot['minute']:02d} — post {slot['post_number']}/6 (seed={slot['thread_seed'][:8]})")

    # Show analytics summary
    summary = scheduler.get_analytics_summary()
    print(f"\nAnalytics: {summary['total_scheduled_7d']} scheduled, {summary['scored_threads']} scored, {summary['fyp_candidate_count']} FYP candidates")