"""Tests for rumahlabuh scheduler and analytics.

Covers:
- SchedulerConfig and WindowConfig
- AnalyticsStore recording and retrieval
- SurveyAnalyzer FYP scoring
- ThreadReevaluator weak thread detection
- SeededThreadGenerator deterministic generation
"""

import json
import time

import pytest

from tools.rumahlabuh_scheduler import (
    AnalyticsStore,
    PostSlot,
    ScheduledDay,
    SchedulerConfig,
    SeededThreadGenerator,
    SurveyAnalyzer,
    SurveyResponse,
    ThreadReevaluator,
    WindowConfig,
    _load_json,
    _save_json,
)

# ── Config tests ──────────────────────────────────────────────────────────────


class TestWindowConfig:
    def test_window_fields(self):
        w = WindowConfig(name="morning", label="Pagi", start_hour=6, end_hour=10, post_count=3)
        assert w.name == "morning"
        assert w.label == "Pagi"
        assert w.start_hour == 6
        assert w.end_hour == 10
        assert w.post_count == 3
        assert w.weight == 1.0  # default

    def test_window_weight_custom(self):
        w = WindowConfig(name="afternoon", label="Siang", start_hour=12, end_hour=17, post_count=4, weight=1.5)
        assert w.weight == 1.5


class TestSchedulerConfig:
    def test_total_posts_per_day(self):
        cfg = SchedulerConfig()
        assert cfg.total_posts_per_day() == 3 + 4 + 2  # morning + afternoon + night

    def test_default_windows(self):
        cfg = SchedulerConfig()
        assert len(cfg.windows) == 3
        assert cfg.windows[0].name == "morning"
        assert cfg.windows[1].name == "afternoon"
        assert cfg.windows[2].name == "night"


# ── PostSlot and ScheduledDay ──────────────────────────────────────────────────


class TestPostSlot:
    def test_post_slot_fields(self):
        slot = PostSlot(
            slot_index=0,
            window_name="morning",
            window_label="Pagi",
            hour=7,
            minute=30,
            post_number=1,
            thread_seed="abc123",
            generated_at=time.time(),
        )
        assert slot.slot_index == 0
        assert slot.window_name == "morning"
        assert slot.hour == 7
        assert slot.minute == 30
        assert slot.post_number == 1
        assert slot.thread_seed == "abc123"


class TestScheduledDay:
    def test_scheduled_day_fields(self):
        slot = PostSlot(
            slot_index=0,
            window_name="morning",
            window_label="Pagi",
            hour=7,
            minute=30,
            post_number=1,
            thread_seed="seed1",
            generated_at=time.time(),
        )
        day = ScheduledDay(
            date_iso="2026-04-23",
            slots=[slot],
            thread_signatures=["sig1"],
        )
        assert day.date_iso == "2026-04-23"
        assert len(day.slots) == 1
        assert day.thread_signatures == ["sig1"]


# ── AnalyticsStore ─────────────────────────────────────────────────────────────


@pytest.fixture
def analytics_store(tmp_path):
    path = tmp_path / "analytics.json"
    store = AnalyticsStore(path)
    yield store
    # cleanup
    if path.exists():
        path.unlink()


@pytest.fixture
def analytics_with_data(tmp_path):
    path = tmp_path / "analytics.json"
    store = AnalyticsStore(path)

    # Add some threads with different engagement scores
    now = time.time()
    store.data["threads"] = [
        {
            "date_iso": "2026-04-20",
            "signature": "sig_high_engagement",
            "technique": "edukasi",
            "pronouns": "gue:lo",
            "engagement_score": 75.0,
            "views": 100,
            "likes": 30,
            "replies": 10,
            "quotes": 5,
            "bookmarks": 10,
            "fyp_worthy": True,
            "scheduled_at": now - 86400,
            "posted_at": now - 43200,
            "survey_completed": True,
        },
        {
            "date_iso": "2026-04-21",
            "signature": "sig_low_engagement",
            "technique": "relatable_story",
            "pronouns": "gue:lo",
            "engagement_score": 15.0,
            "views": 50,
            "likes": 3,
            "replies": 1,
            "quotes": 0,
            "bookmarks": 1,
            "fyp_worthy": False,
            "scheduled_at": now - 172800,
            "posted_at": now - 86400,
            "survey_completed": True,
        },
        {
            "date_iso": "2026-04-22",
            "signature": "sig_no_engagement",
            "technique": "hot_take",
            "pronouns": "gue:lo",
            "engagement_score": 0.0,
            "views": 0,
            "likes": 0,
            "replies": 0,
            "quotes": 0,
            "bookmarks": 0,
            "fyp_worthy": False,
            "scheduled_at": now - 259200,
            "posted_at": 0.0,
            "survey_completed": False,
        },
    ]
    store.save()
    yield store


class TestAnalyticsStoreSchema:
    def test_ensure_schema_creates_defaults(self, analytics_store):
        assert "threads" in analytics_store.data
        assert "daily_summaries" in analytics_store.data
        assert "fyp_candidates" in analytics_store.data
        assert "last_reevaluate" in analytics_store.data


class TestAnalyticsStoreRecording:
    def test_record_generated_adds_thread(self, analytics_store):
        analytics_store.record_generated(
            date_iso="2026-04-23",
            sig="sig_new_1",
            technique="edukasi",
            pronouns="gue:lo",
        )
        assert len(analytics_store.data["threads"]) == 1
        assert analytics_store.data["threads"][0]["signature"] == "sig_new_1"
        assert analytics_store.data["threads"][0]["technique"] == "edukasi"

    def test_record_generated_updates_existing(self, analytics_store):
        analytics_store.record_generated(
            date_iso="2026-04-23",
            sig="sig_dup",
            technique="edukasi",
            pronouns="gue:lo",
        )
        analytics_store.record_generated(
            date_iso="2026-04-23",
            sig="sig_dup",
            technique="relatable_story",
            pronouns="gue:lo",
        )
        # Should still be 1 (updated, not appended)
        assert len(analytics_store.data["threads"]) == 1
        assert analytics_store.data["threads"][0]["technique"] == "relatable_story"

    def test_record_posted_sets_timestamp(self, analytics_store):
        analytics_store.record_generated(
            date_iso="2026-04-23",
            sig="sig_posted",
            technique="edukasi",
            pronouns="gue:lo",
        )
        now = time.time()
        analytics_store.record_posted("sig_posted", posted_at=now)
        thread = analytics_store.get_thread("sig_posted")
        assert thread is not None
        assert thread["posted_at"] == now


class TestAnalyticsStoreRetrieval:
    def test_get_thread_by_signature(self, analytics_with_data):
        thread = analytics_with_data.get_thread("sig_high_engagement")
        assert thread is not None
        assert thread["signature"] == "sig_high_engagement"
        assert thread["engagement_score"] == 75.0

    def test_get_thread_not_found(self, analytics_with_data):
        thread = analytics_with_data.get_thread("sig_nonexistent")
        assert thread is None

    def test_get_recent_threads(self, analytics_with_data):
        recent = analytics_with_data.get_recent_threads(days=7)
        assert len(recent) == 3

    def test_get_top_performers(self, analytics_with_data):
        top = analytics_with_data.get_top_performers(limit=2)
        assert len(top) == 2
        assert top[0]["signature"] == "sig_high_engagement"
        assert top[0]["engagement_score"] >= top[1]["engagement_score"]


class TestEngagementScore:
    def test_compute_engagement_score(self, analytics_store):
        thread = {
            "views": 100,
            "likes": 20,
            "replies": 5,
            "quotes": 2,
            "bookmarks": 10,
        }
        score = analytics_store._compute_score(thread)
        expected = round((20 * 1.0 + 5 * 2.0 + 2 * 3.0 + 10 * 1.5) / 100 * 100, 4)
        assert score == expected

    def test_compute_engagement_zero_views(self, analytics_store):
        thread = {"views": 0, "likes": 10}
        score = analytics_store._compute_score(thread)
        assert score == 0.0


class TestFYPWorthy:
    def test_set_fyp_worthy(self, analytics_store):
        analytics_store.record_generated(
            date_iso="2026-04-23",
            sig="sig_fyp_test",
            technique="edukasi",
            pronouns="gue:lo",
        )
        analytics_store.set_fyp_worthy("sig_fyp_test", fyp=True)
        thread = analytics_store.get_thread("sig_fyp_test")
        assert thread["fyp_worthy"] is True
        assert "sig_fyp_test" in analytics_store.data["fyp_candidates"]


# ── SurveyAnalyzer ─────────────────────────────────────────────────────────────


class TestSurveyAnalyzer:
    def test_survey_analyzer_default_thresholds(self):
        analyzer = SurveyAnalyzer()
        assert analyzer.min_likes_for_fyp == 15
        assert analyzer.min_replies_for_fyp == 3
        assert analyzer.min_score_for_fyp == 0.5

    def test_survey_analyze_fyp_worthy(self):
        analyzer = SurveyAnalyzer()
        response = SurveyResponse(
            signature="sig_fyp",
            views=100,
            likes=20,
            replies=5,
            saves=10,
        )
        result = analyzer.analyze(response)
        assert result["fyp_worthy"] is True
        assert result["meets_thresholds"] is True

    def test_survey_analyze_below_thresholds(self):
        analyzer = SurveyAnalyzer()
        response = SurveyResponse(
            signature="sig_low",
            views=50,
            likes=5,
            replies=1,
            saves=0,
        )
        result = analyzer.analyze(response)
        assert result["meets_thresholds"] is False

    def test_survey_bulk_analyze(self):
        analyzer = SurveyAnalyzer()
        responses = [
            SurveyResponse("sig1", views=100, likes=20, replies=5, saves=10),
            SurveyResponse("sig2", views=50, likes=5, replies=1, saves=0),
        ]
        results = analyzer.bulk_analyze(responses)
        assert len(results) == 2
        assert results[0]["fyp_worthy"] is True
        assert results[1]["fyp_worthy"] is False


# ── ThreadReevaluator ───────────────────────────────────────────────────────────


class TestThreadReevaluator:
    def test_score_thread(self, analytics_with_data):
        reeval = ThreadReevaluator(analytics_with_data)
        score = reeval.score_thread("sig_high_engagement")
        assert score == 75.0

    def test_get_weak_threads(self, analytics_with_data):
        reeval = ThreadReevaluator(analytics_with_data)
        weak = reeval.get_weak_threads(threshold=0.3)
        assert len(weak) == 1
        assert weak[0]["signature"] == "sig_low_engagement"

    def test_get_weak_threads_none_below_threshold(self):
        store = AnalyticsStore()
        reeval = ThreadReevaluator(store)
        weak = reeval.get_weak_threads(threshold=0.3)
        # No threads = empty list
        assert len(weak) == 0


# ── SeededThreadGenerator ──────────────────────────────────────────────────────


@pytest.fixture
def seeded_gen(tmp_path):
    facts_path = tmp_path / "facts.txt"
    facts_path.write_text("Some factual content about kost searching.", encoding="utf-8")

    blueprints_path = tmp_path / "blueprints.json"
    blueprints_path.write_text(json.dumps({
        "techniques": [
            {
                "name": "edukasi",
                "posts": {
                    "1": ["1/6 gue pernah ngegas pas nyari kost", "1/6 lo pernah nyari kost"],
                    "2": ["2/6 foto keliatan rapi", "2/6 realitanya beda"],
                    "3": ["3/6 checklist yang sering gue skip", "3/6 deposit dan akses"],
                    "4": ["4/6 hal kecil yang orang lain lewatin", "4/6 detail yang bikin beda"],
                    "5": ["5/6 lo lebih suka apa?", "5/6 tanya ke penghuni dulu?"],
                    "6": ["6/6 cek opsi di rumahlabuh.com?", "6/6 bandingin lokasi dan budget?"],
                }
            }
        ],
        "pools": {},
    }), encoding="utf-8")

    return SeededThreadGenerator(facts_path=facts_path, blueprints_path=blueprints_path)


class TestSeededThreadGenerator:
    def test_generate_with_seed_is_deterministic(self, seeded_gen):
        result_a = seeded_gen.generate_with_seed("2026-04-23", seed_suffix="run1")
        result_b = seeded_gen.generate_with_seed("2026-04-23", seed_suffix="run1")

        assert result_a["success"] is True
        assert result_b["success"] is True
        assert result_a["thread"] == result_b["thread"]

    def test_generate_with_seed_produces_6_posts(self, seeded_gen):
        result = seeded_gen.generate_with_seed("2026-04-23", seed_suffix="test")
        assert result["success"] is True
        assert len(result["thread"]) == 6

    def test_different_seed_suffix_produces_different_thread(self, seeded_gen):
        result_a = seeded_gen.generate_with_seed("2026-04-23", seed_suffix="alpha")
        result_b = seeded_gen.generate_with_seed("2026-04-23", seed_suffix="beta")

        assert result_a["success"] is True
        assert result_b["success"] is True
        # Different suffixes should produce different threads (very high probability)
        assert result_a["thread"] != result_b["thread"]

    def test_generate_with_seed_has_signature(self, seeded_gen):
        result = seeded_gen.generate_with_seed("2026-04-23", seed_suffix="sig_test")
        assert result["success"] is True
        assert "signature" in result
        assert len(result["signature"]) > 0


# ── JSON helpers ───────────────────────────────────────────────────────────────


class TestJSONHelpers:
    def test_load_json_missing_file(self, tmp_path):
        result = _load_json(tmp_path / "nonexistent.json")
        assert result == {}

    def test_save_and_load_json(self, tmp_path):
        path = tmp_path / "test_save.json"
        data = {"key": "value", "number": 42}
        _save_json(path, data)

        loaded = _load_json(path)
        assert loaded == data
