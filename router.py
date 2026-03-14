"""Agent router — thin shim that delegates to agents.py.

agents.py is the single source of truth for model registry, keywords,
fallback chains, and thread memory. This file re-exports everything
for any legacy callers that import from router directly.

Verified working models (from live logs 2026-03-09):
  groq/llama-3.3-70b-versatile  ✓
  cerebras/qwen-3-235b-a22b     ✓
  zai/glm-4                     ✓ (via openai-compat endpoint)
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

# ── Re-export everything from agents.py (single source of truth) ────────────
from agents import (
    AGENT_MODELS,
    FALLBACK_CHAIN,
    TASK_KEYWORDS,
    DEFAULT_AGENT,
    ACTIVE_THREADS,
    CONVERSATION_HISTORY,
    DEBATE_PERSONAS,
    DEBATE_PERSONA_MODELS,
    DEBATE_ICONS,
    PERSONALITY_WRAPPER,
    detect_agent,
    get_model,
    get_fallback_chain,
    build_system_prompt,
    list_agents,
    list_all_departments,
    add_to_thread,
    get_thread_context,
    list_threads,
    list_threads_raw,
    clear_thread,
    add_to_conversation,
    get_conversation_history,
    clear_conversation,
    get_conversation_summary_prompt,
)

__all__ = [
    "AGENT_MODELS", "FALLBACK_CHAIN", "TASK_KEYWORDS", "DEFAULT_AGENT",
    "ACTIVE_THREADS", "CONVERSATION_HISTORY",
    "DEBATE_PERSONAS", "DEBATE_PERSONA_MODELS",
    "DEBATE_ICONS", "PERSONALITY_WRAPPER",
    "detect_agent", "get_model", "get_fallback_chain", "build_system_prompt",
    "list_agents", "list_all_departments",
    "add_to_thread", "get_thread_context", "list_threads",
    "list_threads_raw", "clear_thread",
    "add_to_conversation", "get_conversation_history",
    "clear_conversation", "get_conversation_summary_prompt",
]
