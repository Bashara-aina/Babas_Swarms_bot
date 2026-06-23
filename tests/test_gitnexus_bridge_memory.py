"""test_gitnexus_bridge_memory.py — gitnexus memory bridge: code-tool filter, MERGE calls."""
import pytest
from core.memory.bridges.gitnexus import GitNexusBridge


_CODE_TOOLS = ["Edit", "Write", "MultiEdit", "NotebookEdit"]
_NON_CODE = ["Read", "Bash", "Grep", "Glob"]


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", _CODE_TOOLS)
async def test_push_calls_cypher_for_code_tools(monkeypatch, tmp_path, tool):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    calls = []
    async def fake_cypher(query, params=None):
        calls.append((query, params))
    monkeypatch.setattr("core.memory.bridges.gitnexus._cypher", fake_cypher)

    bridge = GitNexusBridge()
    await bridge.state.load()

    await bridge.push(
        1,
        {"id": 1, "session_id": "s", "tool_name": tool,
         "files_modified": ["src/foo.py"]},
    )
    assert len(calls) >= 1
    joined = " ".join(q for q, _ in calls)
    assert "MERGE" in joined


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", _NON_CODE)
async def test_push_skips_non_code_tools(monkeypatch, tmp_path, tool):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    calls = []
    async def fake_cypher(query, params=None):
        calls.append((query, params))
    monkeypatch.setattr("core.memory.bridges.gitnexus._cypher", fake_cypher)

    bridge = GitNexusBridge()
    await bridge.state.load()

    await bridge.push(
        1,
        {"id": 1, "session_id": "s", "tool_name": tool, "files_modified": []},
    )
    assert calls == []


_NOISE_PATHS = [".obsidian/x.md", ".wiki/y.md", "data/observations.db", "x/__pycache__/a.pyc"]


@pytest.mark.asyncio
@pytest.mark.parametrize("path", _NOISE_PATHS)
async def test_push_skips_noise_paths(monkeypatch, tmp_path, path):
    monkeypatch.setattr("core.memory.bridges._base.STATE_DB", tmp_path / "bs.db")
    calls = []
    async def fake_cypher(query, params=None):
        calls.append((query, params))
    monkeypatch.setattr("core.memory.bridges.gitnexus._cypher", fake_cypher)

    bridge = GitNexusBridge()
    await bridge.state.load()

    await bridge.push(
        1,
        {"id": 1, "session_id": "s", "tool_name": "Edit", "files_modified": [path]},
    )
    assert calls == []
