import asyncio

import pytest

from core.joint_memory import joint_get_recent, joint_save, joint_search


@pytest.mark.asyncio
async def test_joint_save_and_search():
    id1 = await joint_save("opencode test content", "opencode", tags=["test"])
    assert id1 > 0
    results = await joint_search("opencode test", sources=None)
    assert any(r["source"] == "opencode" for r in results)

@pytest.mark.asyncio
async def test_joint_get_recent():
    await joint_save("session 1", "opencode", tags=["test"])
    await joint_save("session 2", "claude-code", tags=["test"])
    recent = await joint_get_recent(days=7, sources=None)
    assert len(recent) >= 2
