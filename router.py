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
import importlib.util
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Re-export everything from agents.py (single source of truth) ────────────
_agents_file = Path(__file__).with_name("agents.py")
_spec = importlib.util.spec_from_file_location("agents_single_source", _agents_file)
if _spec is None or _spec.loader is None:
  raise ImportError(f"Unable to load agents module from {_agents_file}")

_agents_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_agents_module)

AGENT_MODELS = _agents_module.AGENT_MODELS
FALLBACK_CHAIN = _agents_module.FALLBACK_CHAIN
TASK_KEYWORDS = _agents_module.TASK_KEYWORDS
DEFAULT_AGENT = _agents_module.DEFAULT_AGENT
ACTIVE_THREADS = _agents_module.ACTIVE_THREADS
CONVERSATION_HISTORY = _agents_module.CONVERSATION_HISTORY
DEBATE_PERSONAS = _agents_module.DEBATE_PERSONAS
DEBATE_PERSONA_MODELS = _agents_module.DEBATE_PERSONA_MODELS
DEBATE_ICONS = _agents_module.DEBATE_ICONS
PERSONALITY_WRAPPER = _agents_module.PERSONALITY_WRAPPER

detect_agent = _agents_module.detect_agent
get_model = _agents_module.get_model
get_fallback_chain = _agents_module.get_fallback_chain
build_system_prompt = _agents_module.build_system_prompt
list_agents = _agents_module.list_agents
list_all_departments = _agents_module.list_all_departments
add_to_thread = _agents_module.add_to_thread
get_thread_context = _agents_module.get_thread_context
list_threads = _agents_module.list_threads
list_threads_raw = _agents_module.list_threads_raw
clear_thread = _agents_module.clear_thread
add_to_conversation = _agents_module.add_to_conversation
get_conversation_history = _agents_module.get_conversation_history
clear_conversation = _agents_module.clear_conversation
get_conversation_summary_prompt = _agents_module.get_conversation_summary_prompt

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
