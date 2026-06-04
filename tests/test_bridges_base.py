"""test_bridges_base.py — BridgeState idempotency + ObservationBridge protocol."""
import asyncio
import pytest
from core.memory.bridges._base import BridgeState, ObservationBridge


@pytest.mark.asyncio
async def test_bridge_state_initializes_with_zero(tmp_path, monkeypatch):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    state = BridgeState("test-bridge")
    await state.load()
    assert state.last_pushed_id == 0


@pytest.mark.asyncio
async def test_bridge_state_advances_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    s1 = BridgeState("test-bridge")
    await s1.load()
    await s1.advance_to(42)
    s2 = BridgeState("test-bridge")
    await s2.load()
    assert s2.last_pushed_id == 42


@pytest.mark.asyncio
async def test_bridge_state_does_not_regress(tmp_path, monkeypatch):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    s = BridgeState("test-bridge")
    await s.load()
    await s.advance_to(100)
    await s.advance_to(50)  # should be no-op
    assert s.last_pushed_id == 100


def test_observation_bridge_protocol():
    class FakeBridge:
        name = "fake"
        async def push(self, obs_id, obs_payload): return None
        async def health(self): return {"ok": True}
    fb: ObservationBridge = FakeBridge()
    assert fb.name == "fake"
