"""test_hermes_bridge.py — hermes bridge: offline resilience, key naming."""
import asyncio
import pytest
from core.memory.bridges.hermes import HermesBridge


@pytest.mark.asyncio
async def test_push_calls_memory_save_with_obs_key(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    saved = []
    async def fake_memory_save(key, value, decay_rate=0.1):
        saved.append({"key": key, "value": value, "decay_rate": decay_rate})
    monkeypatch.setattr("core.memory.bridges.hermes._memory_save", fake_memory_save)

    bridge = HermesBridge()
    await bridge.state.load()

    await bridge.push(42, {"id": 42, "session_id": "s1", "content": "hi"})
    assert saved[0]["key"] == "obs:42"
    assert saved[0]["decay_rate"] == 0.1


@pytest.mark.asyncio
async def test_push_swallows_hermes_offline(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    async def fake_memory_save(key, value, decay_rate=0.1):
        raise ConnectionError("hermes offline")
    monkeypatch.setattr("core.memory.bridges.hermes._memory_save", fake_memory_save)

    bridge = HermesBridge()
    await bridge.state.load()
    # Must not raise
    await bridge.push(1, {"id": 1, "session_id": "s", "content": "x"})


@pytest.mark.asyncio
async def test_push_strips_private(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    captured = []
    async def fake_memory_save(key, value, decay_rate=0.1):
        captured.append(value.get("content"))
    monkeypatch.setattr("core.memory.bridges.hermes._memory_save", fake_memory_save)

    bridge = HermesBridge()
    await bridge.state.load()

    await bridge.push(
        1, {"id": 1, "session_id": "s", "content": "visible <private>HIDDEN</private> tail"}
    )
    assert "HIDDEN" not in captured[0]
