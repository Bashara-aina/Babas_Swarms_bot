
import pytest

from core.legion_callback_bridge import LEGION_DIRECTIVE_RE, LegionCallbackBridge, SpawnTracker


def test_spawn_tracker_depth_limit():
    tracker = SpawnTracker(max_depth=3)
    assert tracker.can_spawn() is True
    tracker.record_spawn("task1", depth=0)
    tracker.record_spawn("task2", depth=1)
    tracker.record_spawn("task3", depth=2)
    assert tracker.can_spawn(depth=3) is False

def test_directive_regex():
    m = LEGION_DIRECTIVE_RE.search("done! @legion please notify user")
    assert m is not None
    assert "notify user" in m.group(1)

def test_directive_regex_none():
    m = LEGION_DIRECTIVE_RE.search("no legion directive here")
    assert m is None

@pytest.mark.asyncio
async def test_bridge_spawn_depth_limit():
    bridge = LegionCallbackBridge(tracker=SpawnTracker(max_depth=1))
    # At depth=1, can no longer spawn
    result = await bridge.spawn_opencode_from_legion("test task", depth=1)
    assert result["spawned"] is False
    assert "max depth" in result.get("reason", "")
