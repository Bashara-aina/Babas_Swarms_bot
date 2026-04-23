import pytest

from core.gitnexus_bridge import _looks_valid_mcp_payload, build_gitnexus_prompt_context


def test_mcp_payload_filtering():
    assert _looks_valid_mcp_payload("Result: symbol references found")
    assert not _looks_valid_mcp_payload("Error: MCP server 'gitnexus' is disabled in config.")


@pytest.mark.asyncio
async def test_build_gitnexus_prompt_context(monkeypatch):
    async def _fake_query(*_args, **_kwargs):
        return "Top symbols:\n- core/opencode_bridge.py"

    monkeypatch.setattr("core.gitnexus_bridge.query_gitnexus", _fake_query)
    block = await build_gitnexus_prompt_context("opencode bridge")
    assert block.startswith("## GITNEXUS GRAPH CONTEXT")
    assert "opencode_bridge.py" in block


@pytest.mark.asyncio
async def test_build_gitnexus_prompt_context_empty(monkeypatch):
    async def _fake_query(*_args, **_kwargs):
        return ""

    monkeypatch.setattr("core.gitnexus_bridge.query_gitnexus", _fake_query)
    block = await build_gitnexus_prompt_context("missing")
    assert block == ""
