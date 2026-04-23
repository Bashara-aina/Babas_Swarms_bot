"""Regression tests for rumahlabuh duplicate prevention via HistoryStore."""

import pytest
import json
from pathlib import Path
from datetime import date, timedelta

from tools.rumahlabuh_thread_generator import HistoryStore


@pytest.fixture
def temp_history_path(tmp_path):
    return tmp_path / "test_history.json"


@pytest.fixture
def history_store(temp_history_path):
    return HistoryStore(temp_history_path)


class TestWasSignatureUsedRecently:
    def test_returns_true_for_recent_duplicate(self, history_store, temp_history_path):
        sig = "abc123signature"
        today = date(2026, 4, 23)

        # Append the signature
        history_store.append(sig, "test_technique", today)

        # Should return True - recent duplicate exists
        result = history_store.was_signature_used_recently(sig, within_days=60, today=today)
        assert result is True

    def test_returns_false_when_not_used(self, history_store, today=None):
        if today is None:
            today = date(2026, 4, 23)
        result = history_store.was_signature_used_recently("unused_signature", within_days=60, today=today)
        assert result is False

    def test_returns_false_after_window_expires(self, history_store, temp_history_path):
        sig = "old_signature"
        old_date = date(2026, 2, 1)
        today = date(2026, 4, 23)

        # Append with old date
        history_store.append(sig, "test_technique", old_date)

        # Window is 60 days, but old_date is more than 60 days before today
        result = history_store.was_signature_used_recently(sig, within_days=60, today=today)
        assert result is False

    def test_returns_true_within_window(self, history_store, temp_history_path):
        sig = "recent_signature"
        recent_date = date(2026, 4, 1)  # Within 60 days of 4/23
        today = date(2026, 4, 23)

        # Append with recent date
        history_store.append(sig, "test_technique", recent_date)

        # Should be within 60-day window
        result = history_store.was_signature_used_recently(sig, within_days=60, today=today)
        assert result is True


class TestAppend:
    def test_append_adds_entry_correctly(self, history_store, temp_history_path):
        sig = "new_signature"
        technique = "edukasi"
        today = date(2026, 4, 23)

        history_store.append(sig, technique, today)

        # Reload from disk to verify persistence
        with open(temp_history_path, "r") as f:
            data = json.load(f)

        items = data.get("items", [])
        assert len(items) == 1
        assert items[0]["signature"] == sig
        assert items[0]["technique"] == technique
        assert items[0]["date"] == "2026-04-23"


class TestLastTechniques:
    def test_returns_recent_techniques(self, history_store):
        today = date(2026, 4, 23)

        history_store.append("sig1", "edukasi", today)
        history_store.append("sig2", "relatable_story", today)
        history_store.append("sig3", "hot_take", date(2026, 4, 20))

        techniques = history_store.last_techniques(within_days=7, today=today)
        assert "edukasi" in techniques
        assert "relatable_story" in techniques
        assert "hot_take" in techniques

    def test_returns_empty_after_window(self, history_store):
        today = date(2026, 4, 23)

        # Add old entries
        history_store.append("sig1", "edukasi", date(2026, 1, 1))
        history_store.append("sig2", "relatable_story", date(2026, 2, 1))

        techniques = history_store.last_techniques(within_days=7, today=today)
        assert len(techniques) == 0


class Test500ItemCap:
    def test_500_item_cap_works(self, history_store):
        today = date(2026, 4, 23)

        # Add more than 500 entries
        for i in range(510):
            history_store.append(f"sig_{i}", f"technique_{i % 5}", today)

        # Should only keep last 500
        items = history_store.data.get("items", [])
        assert len(items) == 500

        # Oldest entries should be dropped
        assert not any(item["signature"] == "sig_0" for item in items)
        # Newest entries should be present
        assert any(item["signature"] == "sig_509" for item in items)


class TestSaveLoadCycle:
    def test_save_load_cycle_works(self, history_store, temp_history_path):
        today = date(2026, 4, 23)

        # Add some data
        history_store.append("sig1", "edukasi", today)
        history_store.append("sig2", "relatable_story", today)

        # Save happens automatically via append
        assert temp_history_path.exists()

        # Create new instance with same path - should load existing data
        new_store = HistoryStore(temp_history_path)
        assert len(new_store.data.get("items", [])) == 2

        techniques = new_store.last_techniques(within_days=7, today=today)
        assert "edukasi" in techniques
        assert "relatable_story" in techniques


class TestDeterministicSignatureGeneration:
    """Tests that signature generation is deterministic for duplicate detection."""

    def test_same_content_same_signature(self):
        from tools.rumahlabuh_thread_generator import _signature

        thread = [
            "1/6 gue suka kost",
            "2/6 lo pernah?",
            "3/6 normal",
            "4/6 normal",
            "5/6 pertanyaan?",
            "6/6结束",
        ]

        sig1 = _signature(thread)
        sig2 = _signature(thread)

        assert sig1 == sig2

    def test_different_content_different_signature(self):
        from tools.rumahlabuh_thread_generator import _signature

        thread1 = ["1/6 first", "2/6 second", "3/6 third", "4/6 fourth", "5/6 fifth", "6/6 sixth"]
        thread2 = ["1/6 different", "2/6 second", "3/6 third", "4/6 fourth", "5/6 fifth", "6/6 sixth"]

        sig1 = _signature(thread1)
        sig2 = _signature(thread2)

        assert sig1 != sig2

    def test_signature_normalizes_whitespace(self):
        from tools.rumahlabuh_thread_generator import _signature

        thread1 = ["1/6  extra   spaces", "2/6 normal", "3/6 third", "4/6 fourth", "5/6 fifth", "6/6 sixth"]
        thread2 = ["1/6 extra spaces", "2/6 normal", "3/6 third", "4/6 fourth", "5/6 fifth", "6/6 sixth"]

        sig1 = _signature(thread1)
        sig2 = _signature(thread2)

        assert sig1 == sig2
