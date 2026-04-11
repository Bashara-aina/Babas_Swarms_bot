"""LLM client — backwards-compatibility shim.

All actual implementation has moved to llm_client/ package.
This file re-exports from the package for backwards compatibility.
"""

from llm_client import (
    SYSTEM_PROMPTS,
    TOOL_DEFINITIONS,
    agent_loop,
    analyze_screenshot,
    chunk_output,
    chat,
    init_humanization_layer,
    llm_client,
    run_shell_command,
    verify_api_keys,
)

__all__ = [
    "SYSTEM_PROMPTS",
    "TOOL_DEFINITIONS",
    "agent_loop",
    "analyze_screenshot",
    "chunk_output",
    "chat",
    "init_humanization_layer",
    "llm_client",
    "run_shell_command",
    "verify_api_keys",
]
