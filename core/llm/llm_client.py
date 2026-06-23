"""LLM client facade for core/llm/ — re-exports from root llm_client package."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

from llm_client import (  # noqa: E402
    SYSTEM_PROMPTS,
    TOOL_DEFINITIONS,
    agent_loop,
    analyze_screenshot,
    call_llm,
    chat,
    chunk_output,
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
    "call_llm",
    "chat",
    "chunk_output",
    "init_humanization_layer",
    "llm_client",
    "run_shell_command",
    "verify_api_keys",
]
