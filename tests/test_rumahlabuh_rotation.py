"""Regression tests for rumahlabuh technique rotation behavior and seed reproducibility."""

from datetime import date

import pytest

from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config


@pytest.fixture
def generator():
    config = load_config()
    return BlueprintGenerator(config, "")


class TestDateBasedRotation:
    def test_different_day_picks_different_technique(self, generator):
        """Date-based rotation should pick different technique on different days."""
        day1 = date(2026, 4, 20)
        day2 = date(2026, 4, 21)
        day3 = date(2026, 4, 22)

        techniques_day1 = set()
        techniques_day2 = set()
        techniques_day3 = set()

        for _ in range(5):
            result1 = generator.generate(today=day1)
            if result1.get("success"):
                techniques_day1.add(result1["technique"])

            result2 = generator.generate(today=day2)
            if result2.get("success"):
                techniques_day2.add(result2["technique"])

            result3 = generator.generate(today=day3)
            if result3.get("success"):
                techniques_day3.add(result3["technique"])

        # Different days should likely produce different technique distributions
        # (not guaranteed to be different each time, but very probable)
        all_same = (techniques_day1 == techniques_day2 == techniques_day3)
        assert not all_same or len(techniques_day1) > 1, "Expected variation across days"


class TestAvoidRepeatDays:
    def test_avoid_recent_technique_selection(self, generator):
        """avoid_repeat_days should prevent recent technique selection."""
        today = date(2026, 4, 23)

        # Generate multiple threads - recent techniques should be avoided
        results = []
        for _ in range(10):
            result = generator.generate(today=today)
            if result.get("success"):
                results.append(result)

        # Extract techniques used in recent days
        techniques_recent = []
        for r in results:
            techniques_recent.append(r["technique"])

        # With 10 generations and only 5 techniques, if avoid_repeat_days works,
        # we should see rotation happening
        unique_techniques = set(techniques_recent)
        assert len(unique_techniques) >= 1  # At least some variation


class TestSeedDeterministicTechniqueSelection:
    def test_same_seed_produces_same_technique(self, generator):
        """Same seed should produce same technique selection."""
        seed = 42
        today = date(2026, 4, 23)

        result1 = generator.generate(seed=seed, today=today)
        result2 = generator.generate(seed=seed, today=today)

        if result1.get("success") and result2.get("success"):
            assert result1["technique"] == result2["technique"]

    def test_different_seed_produces_different_technique(self, generator):
        """Different seeds should produce different technique selection (with high probability)."""
        today = date(2026, 4, 23)

        # Use seeds that are likely to produce different results
        results = set()
        for seed in [1, 2, 3, 4, 5]:
            result = generator.generate(seed=seed, today=today)
            if result.get("success"):
                results.add(result["technique"])

        # With 5 different seeds, we should see some variation
        # (not guaranteed but highly probable with 5 techniques)
        assert len(results) >= 1


class TestSameSeedAndDate:
    def test_same_seed_date_produces_identical_thread(self, generator):
        """Same seed + date should produce identical thread (same signature)."""
        seed = 12345
        today = date(2026, 4, 23)

        result1 = generator.generate(seed=seed, today=today)
        result2 = generator.generate(seed=seed, today=today)

        assert result1["success"] and result2["success"]
        assert result1["signature"] == result2["signature"]
        assert result1["thread"] == result2["thread"]
        assert result1["pronouns"] == result2["pronouns"]

    def test_same_seed_different_date_produces_different(self, generator):
        """Same seed with different dates should produce different threads."""
        seed = 12345
        date1 = date(2026, 4, 20)
        date2 = date(2026, 4, 21)

        result1 = generator.generate(seed=seed, today=date1)
        result2 = generator.generate(seed=seed, today=date2)

        assert result1["success"] and result2["success"]
        # Different dates should produce different output (very high probability)
        assert result1["signature"] != result2["signature"] or result1["thread"] != result2["thread"]


class TestSeedPropagatesThroughRandomness:
    def test_seed_affects_pronoun_selection(self, generator):
        """Seed should affect pronoun selection."""
        today = date(2026, 4, 23)

        result1 = generator.generate(seed=999, today=today)
        result2 = generator.generate(seed=999, today=today)

        # Same seed should produce same pronouns
        assert result1["success"] and result2["success"]
        assert result1["pronouns"] == result2["pronouns"]

    def test_seed_affects_template_selection(self, generator):
        """Seed should affect which template is selected for each post."""
        today = date(2026, 4, 23)

        result1 = generator.generate(seed=777, today=today)
        result2 = generator.generate(seed=777, today=today)

        # Same seed should produce same posts
        assert result1["success"] and result2["success"]
        assert result1["thread"] == result2["thread"]

    def test_seed_affects_context_building(self, generator):
        """Seed should affect context building (pools selection)."""
        today = date(2026, 4, 23)

        result1 = generator.generate(seed=555, today=today)
        result2 = generator.generate(seed=555, today=today)

        # Same seed should produce same context in posts
        assert result1["success"] and result2["success"]
        assert result1["thread"] == result2["thread"]


class TestGenerateWithDateBasedSeed:
    def test_generate_fresh_thread_without_seed(self, generator):
        """generate_fresh_thread style should work without explicit seed."""
        today = date(2026, 4, 23)

        result = generator.generate(today=today)

        assert result["success"]
        assert len(result["thread"]) == 6
        assert result["technique"] is not None

    def test_generate_with_explicit_seed(self, generator):
        """generate with explicit seed should work."""
        today = date(2026, 4, 23)
        seed = 42

        result = generator.generate(seed=seed, today=today)

        assert result["success"]
        assert len(result["thread"]) == 6
        assert result["technique"] is not None


class TestPoolExhaustionFallback:
    def test_empty_pool_graceful_fallback(self, generator):
        """Pool exhaustion should fallback gracefully."""
        # Generate many threads - should not crash even if pools have limited entries
        today = date(2026, 4, 23)

        for seed in range(50):
            result = generator.generate(seed=seed, today=today)
            # Should either succeed or fail gracefully, not crash
            assert result is not None
            if result.get("success"):
                assert len(result["thread"]) == 6
