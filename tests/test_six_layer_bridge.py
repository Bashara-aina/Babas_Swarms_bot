"""test_six_layer_bridge.py — six_layer bridge: idempotency, all 4 layers called."""
import asyncio
import pytest
from core.memory.bridges.six_layer import SixLayerBridge


@pytest.mark.asyncio
async def test_push_calls_all_four_layers(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    calls = {"chroma": 0, "langmem": 0, "graphrag": 0, "mem0": 0}

    async def fake_chroma(payload, meta): calls["chroma"] += 1
    async def fake_langmem(payload, meta): calls["langmem"] += 1
    async def fake_graphrag(payload, meta): calls["graphrag"] += 1
    async def fake_mem0(payload, meta): calls["mem0"] += 1

    monkeypatch.setattr("core.memory.bridges.six_layer._chroma_add", fake_chroma)
    monkeypatch.setattr("core.memory.bridges.six_layer._langmem_add", fake_langmem)
    monkeypatch.setattr("core.memory.bridges.six_layer._graphrag_add", fake_graphrag)
    monkeypatch.setattr("core.memory.bridges.six_layer._mem0_add", fake_mem0)

    bridge = SixLayerBridge()
    await bridge.state.load()

    payload = {"id": 1, "session_id": "s1", "content": "hello", "type": "feature",
               "tool_name": "Edit", "files_modified": []}
    await bridge.push(1, payload)
    await bridge.push(2, {**payload, "id": 2, "content": "world"})

    assert calls == {"chroma": 2, "langmem": 2, "graphrag": 2, "mem0": 2}


@pytest.mark.asyncio
async def test_push_strips_private_before_layer_calls(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    captured = []
    async def fake_layer(payload, meta): captured.append(payload.get("content"))
    monkeypatch.setattr("core.memory.bridges.six_layer._chroma_add", fake_layer)
    monkeypatch.setattr("core.memory.bridges.six_layer._langmem_add", fake_layer)
    monkeypatch.setattr("core.memory.bridges.six_layer._graphrag_add", fake_layer)
    monkeypatch.setattr("core.memory.bridges.six_layer._mem0_add", fake_layer)

    bridge = SixLayerBridge()
    await bridge.state.load()

    payload = {"id": 1, "session_id": "s1",
               "content": "public <private>SECRET</private> end",
               "type": "feature", "tool_name": "Edit"}
    await bridge.push(1, payload)
    assert all("SECRET" not in (c or "") for c in captured)


@pytest.mark.asyncio
async def test_push_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    calls = []
    async def fake_layer(payload, meta): calls.append(payload.get("content"))
    monkeypatch.setattr("core.memory.bridges.six_layer._chroma_add", fake_layer)
    monkeypatch.setattr("core.memory.bridges.six_layer._langmem_add", fake_layer)
    monkeypatch.setattr("core.memory.bridges.six_layer._graphrag_add", fake_layer)
    monkeypatch.setattr("core.memory.bridges.six_layer._mem0_add", fake_layer)

    bridge = SixLayerBridge()
    await bridge.state.load()

    p = {"id": 7, "session_id": "s1", "content": "x", "type": "feature"}
    await bridge.push(7, p)
    await bridge.push(7, p)  # replay — should be skipped
    # 4 layers × 1 effective push = 4 entries; replay adds 0
    assert len(calls) == 4
