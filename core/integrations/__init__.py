"""External tool integrations: LangGraph, pydantic-ai, crewAI, MCP, Phoenix, browser-use, langmem, graphrag, prefect."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = [
    # browser-use
    "BrowserUseAgent",
    # LangGraph
    "LangGraphAgent",
    # MCP bridge
    "MCPBridge",
    # Phoenix / observability
    "PhoenixTracer",
    "PrefectPipeline",
    "RumahLabuhCrew",
    # ruvector (placeholder)
    "RuvectorCognitionKernel",
    # second-brain (placeholder)
    "SecondBrainIndexer",
    # crewAI
    "SwarmBotCrew",
    # graphrag
    "SwarmBotGraphRAG",
    # langmem
    "SwarmBotMemoryManager",
    "TokenUsageTracker",
    "agent_task",
    "browse_web_async",
    "create_manage_memory_tool",
    "create_swarmbot_deployment",
    "create_tdd_enforcer",
    "create_wiki_memory_pipeline",
    # superpowers / TDD enforcement
    "enforce_tdd",
    "get_langmem_manager",
    "get_langmem_searcher",
    "get_ruvector_kernel",
    "index_wiki_knowledge_graph",
    "mcp_bridge_call",
    "pre_feed_context",
    "query_wiki_graph",
    "run_crewai_task",
    "run_langgraph_plan",
    "run_langgraph_task",
    # pydantic-ai
    "run_pydantic_ai_agent",
    "run_tdd_check",
    "run_with_prefect",
    # prefect
    "swarmbot_flow",
    "validate_agent_code",
    "wrap_langmem_context",
]


def __getattr__(name: str):
    if name == "LangGraphAgent":
        from .langgraph_orchestrator import LangGraphAgent
        return LangGraphAgent
    if name == "run_langgraph_task":
        from .langgraph_orchestrator import run_langgraph_task
        return run_langgraph_task
    if name == "run_langgraph_plan":
        from .langgraph_orchestrator import run_langgraph_plan
        return run_langgraph_plan
    if name == "run_pydantic_ai_agent":
        from .pydantic_ai_agent import run_pydantic_ai_agent
        return run_pydantic_ai_agent
    if name == "SwarmBotCrew":
        from .crewai_orchestrator import SwarmBotCrew
        return SwarmBotCrew
    if name == "run_crewai_task":
        from .crewai_orchestrator import run_crewai_task
        return run_crewai_task
    if name == "RumahLabuhCrew":
        from .crewai_orchestrator import RumahLabuhCrew
        return RumahLabuhCrew
    if name == "MCPBridge":
        from .mcp_bridge import MCPBridge
        return MCPBridge
    if name == "mcp_bridge_call":
        from .mcp_bridge import mcp_bridge_call
        return mcp_bridge_call
    if name == "PhoenixTracer":
        from .phoenix_observability import PhoenixTracer
        return PhoenixTracer
    if name == "TokenUsageTracker":
        from .phoenix_observability import TokenUsageTracker
        return TokenUsageTracker
    if name == "get_token_tracker":
        from .phoenix_observability import get_token_tracker
        return get_token_tracker
    if name == "BrowserUseAgent":
        from .browser_use_agent import BrowserUseAgent
        return BrowserUseAgent
    if name == "browse_web_async":
        from .browser_use_agent import browse_web_async
        return browse_web_async
    if name == "SwarmBotMemoryManager":
        from .langmem_integration import SwarmBotMemoryManager
        return SwarmBotMemoryManager
    if name == "get_langmem_searcher":
        from .langmem_integration import get_langmem_searcher
        return get_langmem_searcher
    if name == "get_langmem_manager":
        from .langmem_integration import get_langmem_manager
        return get_langmem_manager
    if name == "create_manage_memory_tool":
        from .langmem_integration import create_manage_memory_tool
        return create_manage_memory_tool
    if name == "wrap_langmem_context":
        from .langmem_integration import wrap_langmem_context
        return wrap_langmem_context
    if name == "SwarmBotGraphRAG":
        from .graphrag_integration import SwarmBotGraphRAG
        return SwarmBotGraphRAG
    if name == "index_wiki_knowledge_graph":
        from .graphrag_integration import index_wiki_knowledge_graph
        return index_wiki_knowledge_graph
    if name == "query_wiki_graph":
        from .graphrag_integration import query_wiki_graph
        return query_wiki_graph
    if name == "swarmbot_flow":
        from .prefect_integration import swarmbot_flow
        return swarmbot_flow
    if name == "agent_task":
        from .prefect_integration import agent_task
        return agent_task
    if name == "run_with_prefect":
        from .prefect_integration import run_with_prefect
        return run_with_prefect
    if name == "PrefectPipeline":
        from .prefect_integration import PrefectPipeline
        return PrefectPipeline
    if name == "create_swarmbot_deployment":
        from .prefect_integration import create_swarmbot_deployment
        return create_swarmbot_deployment
    if name == "RuvectorCognitionKernel":
        from .ruvector_integration import RuvectorCognitionKernel
        return RuvectorCognitionKernel
    if name == "get_ruvector_kernel":
        from .ruvector_integration import get_ruvector_kernel
        return get_ruvector_kernel
    if name == "SecondBrainIndexer":
        from .second_brain_integration import SecondBrainIndexer
        return SecondBrainIndexer
    if name == "pre_feed_context":
        from .second_brain_integration import pre_feed_context
        return pre_feed_context
    if name == "create_wiki_memory_pipeline":
        from .second_brain_integration import create_wiki_memory_pipeline
        return create_wiki_memory_pipeline
    if name == "enforce_tdd":
        from .superpowers_integration import enforce_tdd
        return enforce_tdd
    if name == "run_tdd_check":
        from .superpowers_integration import run_tdd_check
        return run_tdd_check
    if name == "validate_agent_code":
        from .superpowers_integration import validate_agent_code
        return validate_agent_code
    if name == "create_tdd_enforcer":
        from .superpowers_integration import create_tdd_enforcer
        return create_tdd_enforcer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
