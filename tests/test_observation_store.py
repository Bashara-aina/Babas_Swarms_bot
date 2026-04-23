"""tests/test_observation_store.py — Tests for claude-mem observation store + progressive retrieval."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from core.memory.observation_store import (
    ObservationStore,
    _classify_type,
    _escape_fts_query,
    _should_skip_path,
    _strip_private,
)


@pytest.fixture
async def store(tmp_path, monkeypatch):
    """Fresh in-memory store per test."""
    # Patch DB_PATH to tmp_path so tests are isolated
    from core.memory import observation_store as obs_module
    monkeypatch.setattr(obs_module, "DB_PATH", tmp_path / "test_obs.db")
    s = ObservationStore()
    yield s
    await s.close()


class TestStripPrivate:
    def test_removes_block_tags(self):
        text = "Hello <private>secret data</private> world"
        assert _strip_private(text) == "Hello  world"

    def test_removes_inline_tags(self):
        text = "Hello [private]secret[/private] world"
        assert _strip_private(text) == "Hello  world"

    def test_preserves_normal_text(self):
        text = "This is normal text with no private tags"
        assert _strip_private(text) == text


class TestClassifyType:
    def test_decision_signal(self):
        assert _classify_type("We decided to use SQLite instead of ChromaDB") == "decision"

    def test_bugfix_signal(self):
        assert _classify_type("Fixed the bug in the connection handler") == "bugfix"

    def test_feature_signal(self):
        assert _classify_type("Added new progressive search capability") == "feature"

    def test_refactor_signal(self):
        assert _classify_type("Refactored the module structure for clarity") == "refactor"

    def test_discovery_default(self):
        assert _classify_type("Interesting observation about the behavior") == "discovery"


class TestShouldSkipPath:
    def test_skips_cache_dirs(self):
        assert _should_skip_path("/foo/__pycache__/bar.py") is True
        assert _should_skip_path("/foo/.venv/lib/baz.py") is True

    def test_skips_lock_files(self):
        assert _should_skip_path("/foo/package-lock.json") is True
        assert _should_skip_path("/foo/yarn.lock") is True

    def test_keeps_code_files(self):
        assert _should_skip_path("/foo/bar.py") is False
        assert _should_skip_path("/src/main.ts") is False


class TestEscapeFtsQuery:
    def test_removes_special_chars(self):
        assert _escape_fts_query("hello world") == '"hello" "world"'

    def test_returns_star_for_empty(self):
        assert _escape_fts_query("") == "*"
        assert _escape_fts_query("  ") == "*"

    def test_quotes_each_word(self):
        assert _escape_fts_query("foo bar baz") == '"foo" "bar" "baz"'


@pytest.mark.asyncio
class TestObservationStore:
    async def test_add_and_search_layer1(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        obs_id = await store.add_observation(
            session_id=session_id,
            content="A test observation about progressive disclosure",
            title="Progressive Disclosure Test",
            type_="discovery",
        )
        assert obs_id == 1

        results = await store.search("progressive", limit=5)
        assert len(results) >= 1
        assert results[0]["id"] == obs_id
        assert results[0]["type"] == "discovery"
        assert "title" in results[0]

    async def test_add_and_timeline_layer2(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        await store.add_observation(
            session_id=session_id,
            content="Timeline test observation",
            title="Timeline Test",
            type_="feature",
        )

        tl = await store.timeline("timeline", limit=5)
        assert len(tl) >= 1
        assert "subtitle" in tl[0]

    async def test_get_observations_layer3(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        obs_id = await store.add_observation(
            session_id=session_id,
            content="Full details observation",
            title="Full Details Test",
            type_="decision",
            narrative="Detailed narrative text here",
            facts="key fact 1, key fact 2",
            tags=["important", "reviewed"],
            files_modified=["core/foo.py", "core/bar.py"],
        )

        full = await store.get_observations([obs_id])
        assert len(full) == 1
        assert full[0]["narrative"] == "Detailed narrative text here"
        assert full[0]["facts"] == "key fact 1, key fact 2"
        assert full[0]["tags"] == ["important", "reviewed"]
        assert full[0]["files_modified"] == ["core/foo.py", "core/bar.py"]

    async def test_session_summary_upsert(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        await store.add_session_summary(
            session_id=session_id,
            request="Test request",
            learned="Learned something",
            completed="Did a thing",
        )

        ss = await store.get_session_summary(session_id)
        assert ss is not None
        assert ss["request"] == "Test request"
        assert ss["learned"] == "Learned something"

        # Upsert replaces
        await store.add_session_summary(
            session_id=session_id,
            request="Test request",
            learned="Updated learning",
            completed="Did more",
        )
        ss2 = await store.get_session_summary(session_id)
        assert ss2["learned"] == "Updated learning"

    async def test_get_session_observations(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        await store.add_observation(session_id=session_id, content="Obs 1", title="First", type_="discovery")
        await store.add_observation(session_id=session_id, content="Obs 2", title="Second", type_="decision")

        obs = await store.get_session_observations(session_id)
        assert len(obs) == 2
        assert obs[0]["type"] == "discovery"
        assert obs[1]["type"] == "decision"

    async def test_stats(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        await store.add_observation(session_id=session_id, content="D1", title="T1", type_="discovery")
        await store.add_observation(session_id=session_id, content="D2", title="T2", type_="decision")

        stats = await store.get_stats()
        assert stats["total"] == 2
        assert stats["discovery"] == 1
        assert stats["decision"] == 1

    async def test_type_filter(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        await store.add_observation(session_id=session_id, content="Disc content", title="Disc", type_="discovery")
        await store.add_observation(session_id=session_id, content="Dec content", title="Dec", type_="decision")

        disc = await store.search("content", type_filter="discovery", limit=5)
        assert all(r["type"] == "discovery" for r in disc)

    async def test_private_tags_stripped_at_write(self, store):
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        obs_id = await store.add_observation(
            session_id=session_id,
            content="Hello <private>SECRET</private> world",
            title="Privacy test",
        )

        full = await store.get_observations([obs_id])
        assert "<private>" not in full[0]["narrative"]
        assert "SECRET" not in full[0]["narrative"]
