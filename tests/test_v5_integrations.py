from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.structured_outputs import AgentResponse


@pytest.mark.asyncio
async def test_openai_agents_bridge_handoff() -> None:
    with patch("core.openai_agents_bridge.chat", new=AsyncMock(return_value=("ok", "mock/model"))):
        from core.openai_agents_bridge import run_with_handoffs

        result = await run_with_handoffs("Say hello", start_agent="general")
        assert result.topology_used == "openai_agents_handoff"
        assert isinstance(result.success, bool)


@pytest.mark.asyncio
@pytest.mark.parametrize("topology", ["sequential", "mixture", "graph", "spreadsheet"])
async def test_swarm_topology(topology: str) -> None:
    with patch("core.swarm_topologies.chat", new=AsyncMock(return_value=("ok", "mock/model"))):
        from core.swarm_topologies import run_topology

        result = await run_topology("Summarize this task", topology=topology, agent_names=["general"])
        assert result.topology_used in {"sequential", "mixture", "graph", "spreadsheet", "concurrent", "auto"}


@pytest.mark.asyncio
async def test_owl_agent_init() -> None:
    with patch("agents.owl_agent.chat", new=AsyncMock(return_value=("owl", "mock/model"))):
        from agents.owl_agent import run_owl_task

        result = await run_owl_task("Quick reasoning test")
        assert isinstance(result, str)


@pytest.mark.asyncio
async def test_ag2_research_pipeline() -> None:
    with patch("agents.ag2_pipeline.chat", new=AsyncMock(return_value=("turn", "mock/model"))):
        from agents.ag2_pipeline import run_ag2_conversation

        result = await run_ag2_conversation("Research test", max_turns=2)
        assert len(result.turns) > 0


@pytest.mark.asyncio
async def test_code_exec_agent_sandbox() -> None:
    from agents.code_agent import _run_python_safely

    result = await _run_python_safely("print('ok')")
    assert "ok" in result.stdout


def test_agent_response_model() -> None:
    with pytest.raises(Exception):
        AgentResponse(answer="x", confidence=1.5)


def test_agentops_track_agent_decorator() -> None:
    from core.observability import track_agent

    @track_agent("x")
    async def _fn() -> dict[str, int]:
        return {"tokens_used": 1}

    assert _fn is not None


@pytest.mark.asyncio
async def test_mirofish_complexity_score_range() -> None:
    from agents.mirofish_agent import MiroFishAgent

    score = await MiroFishAgent().score_task_complexity("do a complex thing")
    assert 1 <= score <= 10


def test_models_yaml_gemma4_entry() -> None:
    import yaml

    with open("config/models.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    gemma = cfg["models"]["gemma4-local"]
    assert int(gemma["context_window"]) == 8192


def test_agent_registry_has_all_v5_agents() -> None:
    import router as agents

    for key in ["owl", "code_exec", "predictor", "ag2_researcher", "ag2_critic", "ag2_synthesizer"]:
        assert key in agents.AGENT_MODELS
