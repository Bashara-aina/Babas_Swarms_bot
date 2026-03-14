"""Tests for DAGPlanner — goal decomposition and DAG structure."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from swarms_bot.orchestrator.dag_planner import DAGPlanner, TaskDAG, DAGNode


class TestDAGNode:
    def test_ready_with_no_deps(self):
        dag = TaskDAG(goal="test")
        dag.add_node(DAGNode(id="t1", title="A", description="task", agent="general"))
        ready = dag.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].id == "t1"

    def test_blocked_by_pending_dep(self):
        dag = TaskDAG(goal="test")
        dag.add_node(DAGNode(id="t1", title="A", description="", agent="general"))
        dag.add_node(DAGNode(id="t2", title="B", description="", agent="coding", depends_on=["t1"]))
        ready = dag.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].id == "t1"

    def test_unblocked_when_dep_done(self):
        dag = TaskDAG(goal="test")
        dag.add_node(DAGNode(id="t1", title="A", description="", agent="general", status="done"))
        dag.add_node(DAGNode(id="t2", title="B", description="", agent="coding", depends_on=["t1"]))
        ready = dag.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].id == "t2"

    def test_is_complete(self):
        dag = TaskDAG(goal="test")
        dag.add_node(DAGNode(id="t1", title="A", description="", agent="general", status="done"))
        dag.add_node(DAGNode(id="t2", title="B", description="", agent="coding", status="failed"))
        assert dag.is_complete()

    def test_summary_format(self):
        dag = TaskDAG(goal="build app")
        dag.add_node(DAGNode(id="t1", title="A", description="", agent="general", status="done"))
        dag.add_node(DAGNode(id="t2", title="B", description="", agent="coding", status="failed"))
        summary = dag.summary()
        assert "1/2" in summary
        assert "1 failed" in summary

    def test_to_text_plan(self):
        dag = TaskDAG(goal="my goal")
        dag.add_node(DAGNode(id="t1", title="Design", description="", agent="architect"))
        plan = dag.to_text_plan()
        assert "my goal" in plan
        assert "t1" in plan
        assert "architect" in plan


class TestDAGPlannerParsing:
    def test_parse_valid_json(self):
        planner = DAGPlanner()
        raw = '[{"id": "t1", "title": "Do X", "description": "desc", "agent": "coding", "depends_on": [], "priority": 1}]'
        result = planner._parse_json(raw)
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_parse_json_with_markdown_fences(self):
        planner = DAGPlanner()
        raw = '```json\n[{"id": "t1", "title": "Do X", "description": "d", "agent": "coding", "depends_on": [], "priority": 1}]\n```'
        result = planner._parse_json(raw)
        assert result[0]["id"] == "t1"

    @pytest.mark.asyncio
    async def test_decompose_fallback_on_llm_failure(self):
        planner = DAGPlanner()
        with patch("litellm.acompletion", side_effect=Exception("LLM error")):
            dag = await planner.decompose("write a script")
        assert len(dag.nodes) == 1
        assert dag.nodes["t1"].agent == "general"

    @pytest.mark.asyncio
    async def test_decompose_with_mock_llm(self):
        planner = DAGPlanner()
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = '[{"id": "t1", "title": "Plan", "description": "design", "agent": "architect", "depends_on": [], "priority": 1}, {"id": "t2", "title": "Code", "description": "implement", "agent": "coding", "depends_on": ["t1"], "priority": 2}]'
        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            dag = await planner.decompose("build a web app")
        assert len(dag.nodes) == 2
        assert dag.nodes["t2"].depends_on == ["t1"]
