"""Tests for AgentMessageBus — pub/sub and message querying."""
import asyncio
import pytest
from swarms_bot.orchestrator.agent_messaging import AgentMessageBus, MessageType


class TestAgentMessageBus:
    @pytest.fixture
    def bus(self):
        return AgentMessageBus(run_id="test-run")

    @pytest.mark.asyncio
    async def test_publish_and_get(self, bus):
        await bus.publish("agent_a", MessageType.TASK_RESULT, "done", recipient="broadcast")
        msgs = await bus.get_messages(sender="agent_a")
        assert len(msgs) == 1
        assert msgs[0].content == "done"

    @pytest.mark.asyncio
    async def test_filter_by_type(self, bus):
        await bus.publish("a", MessageType.TASK_RESULT, "result")
        await bus.publish("a", MessageType.ERROR, "error")
        results = await bus.get_messages(msg_type=MessageType.TASK_RESULT)
        assert len(results) == 1
        assert results[0].msg_type == MessageType.TASK_RESULT

    @pytest.mark.asyncio
    async def test_subscribe_receives_broadcast(self, bus):
        q = bus.subscribe("agent_b")
        await bus.publish("agent_a", MessageType.STATUS_UPDATE, "running", recipient="broadcast")
        msg = await asyncio.wait_for(q.get(), timeout=1.0)
        assert msg.content == "running"

    @pytest.mark.asyncio
    async def test_subscribe_receives_direct(self, bus):
        q = bus.subscribe("agent_c")
        await bus.publish("agent_a", MessageType.TASK_RESULT, "direct msg", recipient="agent_c")
        msg = await asyncio.wait_for(q.get(), timeout=1.0)
        assert msg.content == "direct msg"

    @pytest.mark.asyncio
    async def test_context_for_agent(self, bus):
        await bus.publish("planner", MessageType.PLAN, "Step 1: design", recipient="coding")
        ctx = bus.get_context_for_agent("coding")
        assert "Step 1: design" in ctx

    @pytest.mark.asyncio
    async def test_message_count(self, bus):
        await bus.publish("a", MessageType.STATUS_UPDATE, "1")
        await bus.publish("a", MessageType.STATUS_UPDATE, "2")
        assert bus.message_count == 2
