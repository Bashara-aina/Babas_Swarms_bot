"""End-to-end pipeline tests for rumahlabuh thread generation.

Tests the full flow:
1. Thread generation via BlueprintGenerator
2. Validation via ThreadValidator
3. History tracking via HistoryStore
4. Fresh generation via generate_fresh_thread()
"""

import pytest
from pathlib import Path

from tools.rumahlabuh_thread_generator import (
    BlueprintGenerator,
    ThreadValidator,
    HistoryStore,
    generate_fresh_thread,
    load_config,
    load_facts,
)


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def facts_text():
    return load_facts()


@pytest.fixture
def generator(config, facts_text):
    return BlueprintGenerator(config, facts_text)


@pytest.fixture
def validator(config):
    return ThreadValidator(config)


@pytest.fixture
def temp_history(tmp_path):
    history_path = tmp_path / "test_history.json"
    store = HistoryStore(history_path)
    yield store


class TestGenerateFreshThread:
    def test_generate_fresh_thread_returns_valid_structure(self):
        result = generate_fresh_thread(seed=42, save_history=False)

        assert result.get("success") is True
        assert "thread" in result
        assert len(result["thread"]) == 6
        assert "pronouns" in result
        assert "technique" in result
        assert "signature" in result

    def test_generate_fresh_thread_with_seed_is_deterministic(self):
        result_a = generate_fresh_thread(seed=12345, save_history=False)
        result_b = generate_fresh_thread(seed=12345, save_history=False)

        assert result_a["success"] is True
        assert result_b["success"] is True
        assert result_a["thread"] == result_b["thread"]
        assert result_a["signature"] == result_b["signature"]

    def test_generate_fresh_thread_each_has_unique_signature(self):
        threads = {}
        for seed in range(100, 105):
            result = generate_fresh_thread(seed=seed, save_history=False)
            assert result["success"] is True
            sig = result["signature"]
            assert sig not in threads, f"Duplicate signature: {sig}"
            threads[sig] = result["thread"]

    def test_generate_fresh_thread_uses_informal_pronouns(self):
        result = generate_fresh_thread(seed=200, save_history=False)
        assert result["success"] is True
        pronouns = result.get("pronouns", [])
        assert len(pronouns) > 0
        # Verify pronouns are informal/semi-formal pairs
        informal = {"gue", "lo", "aku", "kamu"}
        for p in pronouns:
            assert p in informal, f"Pronoun '{p}' not in expected informal set"


class TestGeneratorAndValidatorIntegration:
    def test_generated_thread_passes_validation(self, generator, validator):
        result = generator.generate(seed=9999)
        assert result.get("success") is True

        thread = result["thread"]
        errors = validator.validate(thread)

        critical = [e for e in errors if "question" in e.lower() or "numbering" in e.lower() or "count" in e.lower()]
        assert len(critical) == 0, f"Critical errors in thread: {critical}"

    def test_generator_marks_thread_as_used(self, generator, config, facts_text):
        result = generator.generate(seed=8888)
        assert result.get("success") is True

        sig = result["signature"]
        technique = result.get("technique", "unknown")

        # Verify it was added to used list
        generator.mark_used(result)
        # HistoryStore stores signatures in items list
        items = generator.history.data.get("items", [])
        sigs_in_history = [item["signature"] for item in items]
        assert sig in sigs_in_history, f"Signature {sig[:8]} not marked as used"

    def test_generator_respects_blueprint_pool(self, generator):
        # Generate multiple threads and verify they come from blueprints
        threads = []
        for seed in range(7000, 7010):
            result = generator.generate(seed=seed)
            if result.get("success"):
                threads.append(result["thread"])

        assert len(threads) > 0
        # Each thread should have 6 posts with proper numbering
        for thread in threads:
            assert len(thread) == 6
            for i, post in enumerate(thread, start=1):
                assert post.startswith(f"{i}/6"), f"Post {i} missing prefix: {post}"


class TestHistoryStoreIntegration:
    def test_history_store_records_signatures(self, temp_history):
        from datetime import date

        today = date(2026, 4, 23)
        temp_history.append("sig_test_1", "edukasi", today)
        temp_history.append("sig_test_2", "relatable_story", today)

        assert temp_history.was_signature_used_recently("sig_test_1", within_days=60, today=today) is True
        assert temp_history.was_signature_used_recently("sig_test_2", within_days=60, today=today) is True
        assert temp_history.was_signature_used_recently("sig_unknown", within_days=60, today=today) is False

    def test_signature_collision_detection(self, temp_history):
        from datetime import date

        today = date(2026, 4, 23)
        sig = "collision_test_sig"
        temp_history.append(sig, "edukasi", today)

        # Same signature should be detected as recent duplicate
        result = temp_history.was_signature_used_recently(sig, within_days=60, today=today)
        assert result is True


class TestEndToEndWithSeeds:
    def test_multiple_seeds_produce_different_content(self):
        seeds = [1001, 1002, 1003]
        threads = []

        for seed in seeds:
            result = generate_fresh_thread(seed=seed, save_history=False)
            assert result["success"] is True
            threads.append(result["thread"])

        # At least some threads should differ (not all identical)
        # With different seeds, probability of all being identical is negligible
        thread_texts = ["".join(t) for t in threads]
        assert len(set(thread_texts)) > 1, "All threads were identical despite different seeds"

    def test_same_seed_produces_identical_output(self):
        seed = 7777
        result_a = generate_fresh_thread(seed=seed, save_history=False)
        result_b = generate_fresh_thread(seed=seed, save_history=False)

        assert result_a["thread"] == result_b["thread"]
        assert result_a["signature"] == result_b["signature"]
        assert result_a["technique"] == result_b["technique"]


class TestValidatorEdgeCases:
    def test_validator_rejects_problematic_threads(self, validator):
        # Thread with no question in post 5
        bad_thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 No question here",
            "6/6 rumahlabuh.com?",
        ]
        errors = validator.validate(bad_thread)
        assert "Post 5 must contain question" in errors

    def test_validator_accepts_clean_thread(self, validator):
        clean_thread = [
            "1/6 Gue pernah ngegas pas nyari kost karena fotonya beda jauh dari realita.",
            "2/6 Banyak yang skip cek detail dulu, baru sadar pas udah masuk.",
            "3/6 Checklist yang sering gue skip: tanya aturan deposit dari awal.",
            "4/6 Yang bikin beda itu usually hal kecil yang orang lain lewatin.",
            "5/6 Lo lebih suka cek kamar sendiri atau tanya ke penghuni dulu?",
            "6/6 Buat yang lagi nyari kost di Solo, bisa cek opsi di rumahlabuh.com. Tinggal bandingin lokasi, budget, dan fasilitas?",
        ]
        errors = validator.validate(clean_thread)
        critical = [e for e in errors if "question" in e.lower()]
        assert len(critical) == 0
