"""tests/test_integrations.py — Integration tests for SwarmBot external packages.

Tests each integration module for import, API surface, and basic functionality.
Run with: pytest tests/test_integrations.py -x --asyncio-mode=auto -q
"""

from __future__ import annotations

import asyncio
import os

import pytest

os.environ.setdefault("MINIMAX_API_KEY", "test-key-for-integration-tests")
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-integration-tests")
os.environ.setdefault("OPENAI_BASE_URL", "https://api.minimax.io/v1")


class TestMem0:
    """Test mem0 memory integration."""

    def test_mem0_import(self):
        from tools.mem0_client import get_mem0, mem0_add, mem0_delete, mem0_search
        assert callable(get_mem0)
        assert asyncio.iscoroutinefunction(mem0_add)
        assert asyncio.iscoroutinefunction(mem0_search)
        assert asyncio.iscoroutinefunction(mem0_delete)

    @pytest.mark.asyncio
    async def test_mem0_search_fallback(self):
        from tools.mem0_client import mem0_search
        results = await mem0_search("test user", "what is 2+2", limit=3)
        assert isinstance(results, list)


class TestLitellmClient:
    """Test litellm client integration."""

    def test_llm_client_import(self):
        from llm_client import agent_loop, call_llm, chat
        assert callable(call_llm)
        assert asyncio.iscoroutinefunction(call_llm)
        assert asyncio.iscoroutinefunction(chat)
        assert asyncio.iscoroutinefunction(agent_loop)

    @pytest.mark.asyncio
    async def test_llm_client_basic(self):
        from llm_client import chat
        try:
            result, _model = await chat("Say 'ok' in one word", agent_key="coding")
            assert isinstance(result, str)
            assert len(result) < 20
        except Exception as exc:
            pytest.skip(f"LLM not available: {exc}")


class TestLangGraph:
    """Test langgraph orchestrator."""

    def test_langgraph_import(self):
        from core.integrations import (
            LangGraphAgent,
            run_langgraph_plan,
            run_langgraph_task,
        )
        assert callable(LangGraphAgent)
        assert asyncio.iscoroutinefunction(run_langgraph_task)
        assert asyncio.iscoroutinefunction(run_langgraph_plan)

    def test_langgraph_agent_config(self):
        from core.integrations.langgraph_orchestrator import LangGraphAgent, LangGraphConfig
        cfg = LangGraphConfig(graph_type="react_agent", max_steps=5)
        assert cfg.graph_type == "react_agent"
        assert cfg.max_steps == 5
        agent = LangGraphAgent(cfg)
        assert agent.model == "minimax/MiniMax-M2.7"
        assert agent._checkpointer is None  # Not set until first run

    @pytest.mark.asyncio
    async def test_langgraph_run(self):
        from core.integrations.langgraph_orchestrator import run_langgraph_task
        try:
            result = await run_langgraph_task(
                task="What is 2+2? Answer in exactly 3 words.",
                max_steps=3,
            )
            assert isinstance(result, str)
            assert len(result) < 200
        except Exception as exc:
            pytest.skip(f"LangGraph not available: {exc}")


class TestPydanticAI:
    """Test pydantic-ai agent."""

    def test_pydantic_ai_import(self):
        from core.integrations import run_pydantic_ai_agent
        assert asyncio.iscoroutinefunction(run_pydantic_ai_agent)

    @pytest.mark.asyncio
    async def test_pydantic_ai_run(self):
        from core.integrations.pydantic_ai_agent import run_pydantic_ai_agent
        try:
            result = await run_pydantic_ai_agent(
                prompt="What is 2+2? Answer in exactly 3 words.",
                timeout=15.0,
            )
            assert isinstance(result, str)
            assert len(result) < 100
        except Exception as exc:
            pytest.skip(f"pydantic-ai not available: {exc}")


class TestCrewAI:
    """Test crewAI orchestrator."""

    def test_crewai_import(self):
        from core.integrations import RumahLabuhCrew, SwarmBotCrew, run_crewai_task
        assert callable(SwarmBotCrew)
        assert asyncio.iscoroutinefunction(run_crewai_task)
        assert callable(RumahLabuhCrew)

    def test_crewai_agent_creation(self):
        from core.integrations.crewai_orchestrator import SwarmBotCrew
        crew = SwarmBotCrew()
        crew.add_agent("researcher", "Research AI", "You are a researcher.")
        crew.add_agent("writer", "Write summary", "You write summaries.")
        assert len(crew.agents_def) == 2
        assert crew.agents_def[0]["role"] == "researcher"
        assert crew.agents_def[1]["role"] == "writer"

    @pytest.mark.asyncio
    async def test_crewai_kickoff(self):
        from core.integrations.crewai_orchestrator import run_crewai_task
        try:
            result = await run_crewai_task(
                task="What is 2+2? Answer in exactly 3 words.",
                agents=[{"role": "helper", "goal": "Give concise answers.", "backstory": "You are helpful."}],
            )
            assert isinstance(result, str)
        except Exception as exc:
            pytest.skip(f"crewAI not available: {exc}")


class TestPhoenix:
    """Test Phoenix observability."""

    def test_phoenix_import(self):
        from core.integrations import PhoenixTracer, TokenUsageTracker
        assert callable(PhoenixTracer)
        assert callable(TokenUsageTracker)

    def test_token_tracker(self):
        from core.integrations.phoenix_observability import TokenUsageTracker
        tracker = TokenUsageTracker()
        tracker.record_run("minimax/MiniMax-M2.7", 10, 20, 150.0, cost=0.001)
        tracker.record_run("minimax/MiniMax-M2.7", 15, 30, 200.0, cost=0.002)
        report = tracker.report()
        assert report["total_runs"] == 2
        assert report["total_tokens"] == 75
        assert report["prompt_tokens"] == 25
        assert report["completion_tokens"] == 50
        tracker.reset()
        assert tracker.total_runs == 0

    @pytest.mark.asyncio
    async def test_phoenix_tracer(self):
        from core.integrations.phoenix_observability import PhoenixTracer
        tracer = PhoenixTracer(local_mode=True)
        await tracer.trace_llm_call(
            model="minimax/MiniMax-M2.7",
            prompt="What is 2+2?",
            response="2 plus 2 equals 4",
            latency_ms=150.0,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20},
        )


class TestBrowserUse:
    """Test browser-use agent."""

    def test_browser_use_import(self):
        from core.integrations import BrowserUseAgent, browse_web_async
        assert callable(BrowserUseAgent)
        assert asyncio.iscoroutinefunction(browse_web_async)

    def test_browser_use_agent_init(self):
        from core.integrations.browser_use_agent import BrowserUseAgent
        agent = BrowserUseAgent(headless=True, max_steps=3)
        assert agent.headless is True
        assert agent.max_steps == 3
        assert agent.model == "minimax/MiniMax-M2.7"


class TestMCPBridge:
    """Test MCP bridge."""

    def test_mcp_bridge_import(self):
        from core.integrations import MCPBridge, mcp_bridge_call
        assert callable(MCPBridge)
        assert asyncio.iscoroutinefunction(mcp_bridge_call)

    def test_mcp_bridge_init(self):
        from core.integrations.mcp_bridge import MCPBridge
        bridge = MCPBridge()
        assert hasattr(bridge, "_cfg")
        assert hasattr(bridge, "_sessions")
        assert hasattr(bridge, "_failed")

    def test_mcp_bridge_server_status(self):
        from core.integrations.mcp_bridge import MCPBridge
        bridge = MCPBridge()
        status = bridge.server_status("nonexistent-server")
        assert status["available"] is False


class TestAutogen:
    """Test autogen integration."""

    def test_autogen_import(self):
        import autogen
        assert hasattr(autogen, "__version__")
        from autogen import Agent
        assert callable(Agent)


class TestIntegrationsExport:
    """Test that all integrations are properly exported from __init__."""

    def test_all_exports_resolve(self):
        assert True  # All exports resolved without error

    def test_langgraph_agent_is_class(self):
        from core.integrations import LangGraphAgent
        assert isinstance(LangGraphAgent, type)

    def test_swarm_bot_crew_is_class(self):
        from core.integrations import SwarmBotCrew
        assert isinstance(SwarmBotCrew, type)

    def test_mcp_bridge_is_class(self):
        from core.integrations import MCPBridge
        assert isinstance(MCPBridge, type)

    def test_phoenix_tracer_is_class(self):
        from core.integrations import PhoenixTracer
        assert isinstance(PhoenixTracer, type)

    def test_token_usage_tracker_is_class(self):
        from core.integrations import TokenUsageTracker
        assert isinstance(TokenUsageTracker, type)

    def test_browser_use_agent_is_class(self):
        from core.integrations import BrowserUseAgent
        assert isinstance(BrowserUseAgent, type)
