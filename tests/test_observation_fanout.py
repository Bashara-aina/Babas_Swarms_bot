"""test_observation_fanout.py — add_observation triggers fire-and-forget fan-out."""
import asyncio
import pytest
from core.memory.observation_store import get_observation_store


@pytest.mark.asyncio
async def test_add_observation_calls_bridges(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")

    bridge_calls = {"six_layer": 0, "hermes": 0, "gitnexus": 0}

    class StubBridge:
        def __init__(self, name):
            self.name = name
            from core.memory.bridges._base import BridgeState
            self.state = BridgeState(name=name)
        async def push(self, obs_id, payload):
            bridge_calls[self.name] += 1
            await self.state.advance_to(obs_id)
        async def health(self):
            return {"ok": True, "name": self.name}

    monkeypatch.setattr("core.memory.bridges.get_bridges",
                        lambda: [StubBridge("six_layer"),
                                 StubBridge("hermes"),
                                 StubBridge("gitnexus")])

    store = get_observation_store()
    obs_id = await store.add_observation(
        session_id="fanout-test",
        content="trigger fanout",
        title="fanout test",
    )
    assert obs_id > 0

    for _ in range(20):
        if all(v > 0 for v in bridge_calls.values()):
            break
        await asyncio.sleep(0.1)

    assert bridge_calls["six_layer"] >= 1
    assert bridge_calls["hermes"] >= 1
    assert bridge_calls["gitnexus"] >= 1


@pytest.mark.asyncio
async def test_fanout_does_not_block_add(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")

    class SlowBridge:
        name = "slow"
        from core.memory.bridges._base import BridgeState
        state = BridgeState(name="slow")
        async def push(self, obs_id, payload):
            await asyncio.sleep(2.0)
        async def health(self): return {"ok": True}

    monkeypatch.setattr("core.memory.bridges.get_bridges", lambda: [SlowBridge()])

    store = get_observation_store()
    start = asyncio.get_event_loop().time()
    obs_id = await store.add_observation(session_id="nonblock", content="x")
    elapsed = asyncio.get_event_loop().time() - start
    assert obs_id > 0
    assert elapsed < 0.5
