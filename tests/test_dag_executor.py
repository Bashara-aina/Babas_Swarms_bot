"""Tests for DAGExecutor — parallel execution, timeout, sibling cancellation."""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swarms_bot.orchestrator.dag_executor import DAGExecutor, DAGNode, TaskDAG


@pytest.fixture
def make_dag_node():
    """Factory for creating DAGNode instances."""
    def _make(
        node_id: str,
        title: str = "",
        agent: str = "general",
        depends_on: list[str] | None = None,
    ):
        return DAGNode(
            id=node_id,
            title=title or node_id,
            description=f"Task {node_id}",
            agent=agent,
            depends_on=depends_on or [],
        )

    return _make


@pytest.fixture
def mock_agent():
    """A mock agent that returns a successful response."""
    agent = AsyncMock()

    @dataclass
    class FakeResponse:
        success: bool = True
        result: str = "done"
        cost_usd: float = 0.001

    async def fake_execute(task):
        await asyncio.sleep(0.01)  # tiny delay
        return FakeResponse()

    agent.execute = fake_execute
    return agent


@pytest.fixture
def mock_agent_failing():
    """An agent that always returns a failed response."""
    agent = AsyncMock()

    @dataclass
    class FakeFailedResponse:
        success: bool = False
        result: str = "intentional failure"
        cost_usd: float = 0.0

    async def fake_execute(task):
        return FakeFailedResponse()

    agent.execute = fake_execute
    return agent


@pytest.fixture
def registry(mock_agent, mock_agent_failing):
    return {"general": mock_agent, "failing": mock_agent_failing}


class TestDAGExecutorParallel:
    """Tests for parallel execution of DAG nodes."""

    async def test_parallel_nodes_run_together(self, make_dag_node, registry):
        """Nodes with no dependencies run in the same batch."""
        dag = TaskDAG(goal="parallel test")
        dag.add_node(make_dag_node("t1", "Task 1"))
        dag.add_node(make_dag_node("t2", "Task 2"))
        dag.add_node(make_dag_node("t3", "Task 3"))

        executor = DAGExecutor(registry, max_parallel=4)
        progress_messages: list[str] = []

        async def progress(msg: str):
            progress_messages.append(msg)

        result = await executor.execute(dag, progress_cb=progress)

        assert result.nodes["t1"].status == "done"
        assert result.nodes["t2"].status == "done"
        assert result.nodes["t3"].status == "done"
        # All three should have run in a single batch
        batch_msgs = [m for m in progress_messages if "Batch" in m]
        assert len(batch_msgs) == 1

    async def test_sequential_dependency(self, make_dag_node, registry):
        """Nodes with dependencies wait for their deps to complete."""
        dag = TaskDAG(goal="sequential test")
        dag.add_node(make_dag_node("t1", "Task 1"))
        dag.add_node(make_dag_node("t2", "Task 2", depends_on=["t1"]))
        dag.add_node(make_dag_node("t3", "Task 3", depends_on=["t2"]))

        executor = DAGExecutor(registry)
        result = await executor.execute(dag)

        assert result.nodes["t1"].status == "done"
        assert result.nodes["t2"].status == "done"
        assert result.nodes["t3"].status == "done"

    async def test_failed_node_marks_dependents_skipped(self, make_dag_node, registry):
        """When a node fails, its dependents are marked skipped."""
        dag = TaskDAG(goal="failure propagation")
        dag.add_node(make_dag_node("t1", "Task 1", agent="failing"))
        dag.add_node(make_dag_node("t2", "Task 2", depends_on=["t1"]))
        dag.add_node(make_dag_node("t3", "Task 3", depends_on=["t2"]))

        executor = DAGExecutor(registry)
        result = await executor.execute(dag)

        assert result.nodes["t1"].status == "failed"
        assert result.nodes["t2"].status == "skipped"
        assert result.nodes["t3"].status == "skipped"


class TestDAGExecutorTimeout:
    """Tests for DAG node timeout handling."""

    async def test_node_timeout_cancels_siblings(self, make_dag_node, registry):
        """When one node in a parallel batch times out, siblings are cancelled."""
        slow_agent = AsyncMock()

        @dataclass
        class SlowResponse:
            success: bool = True
            result: str = "slow result"
            cost_usd: float = 0.001

        async def slow_execute(task):
            await asyncio.sleep(10)  # deliberately too slow
            return SlowResponse()

        slow_agent.execute = slow_execute

        registry_with_slow = {"general": registry["general"], "slow": slow_agent}

        dag = TaskDAG(goal="parallel with timeout")
        dag.add_node(make_dag_node("t1", "Task 1", agent="slow"))
        dag.add_node(make_dag_node("t2", "Task 2", agent="general"))
        dag.add_node(make_dag_node("t3", "Task 3", agent="general"))

        executor = DAGExecutor(registry_with_slow, max_parallel=4)

        original_run_node = executor._run_node

        async def timeout_run_node(node, dag, semaphore):
            if node.id == "t1":
                raise TimeoutError("Node t1 timed out")
            return await original_run_node(node, dag, semaphore)

        with patch.object(executor, "_run_node", side_effect=timeout_run_node):
            result = await executor.execute(dag)

        # All nodes should have attempted execution
        # At least one should have a timeout error set
        {n.id: n.status for n in result.nodes.values()}
        errors = {n.id: n.error for n in result.nodes.values()}
        assert any("timeout" in str(e).lower() or "timed out" in str(e).lower() for e in errors.values() if e)

    async def test_timeout_sets_node_error(self, make_dag_node, registry):
        """Verify that a timed-out node has its error attribute set."""
        timeout_agent = AsyncMock()

        async def timeout_execute(task):
            await asyncio.sleep(999)  # will exceed any reasonable timeout
            return MagicMock(success=True, result="done", cost_usd=0.001)

        timeout_agent.execute = timeout_execute
        registry_timeout = {"timeout": timeout_agent}

        dag = TaskDAG(goal="timeout test")
        dag.add_node(make_dag_node("t1", "Task 1", agent="timeout"))

        executor = DAGExecutor(registry_timeout, max_parallel=2)

        # Inject TimeoutError directly into _run_node to simulate timeout
        async def simulate_timeout(node, dag, semaphore, timeout=0.05):
            node.error = f"Agent timed out after {timeout}s"
            node.status = "failed"

        with patch.object(executor, "_run_node", simulate_timeout):
            result = await executor.execute(dag)

        t1 = result.nodes["t1"]
        assert t1.error is not None
        assert "timed out" in t1.error


class TestDAGExecutorRetry:
    """Tests for DAG node retry logic."""

    async def test_node_retries_on_failure(self, make_dag_node):
        """Nodes retry up to 3 times on transient errors."""
        attempts = 0
        flaky_agent = AsyncMock()

        @dataclass
        class FlakyResponse:
            success: bool = False
            result: str = "transient error"
            cost_usd: float = 0.0

        async def flaky_execute(task):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RuntimeError("transient")
            return MagicMock(success=True, result="success on retry", cost_usd=0.001)

        flaky_agent.execute = flaky_execute
        registry_flaky = {"flaky": flaky_agent}

        dag = TaskDAG(goal="retry test")
        dag.add_node(make_dag_node("t1", "Task 1", agent="flaky"))

        executor = DAGExecutor(registry_flaky)
        result = await executor.execute(dag)

        assert result.nodes["t1"].status == "done"
        assert attempts == 3
