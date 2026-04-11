"""Agent registry — backwards-compatibility shim.

All agent registry data (AGENT_MODELS, FALLBACK_CHAIN, TASK_KEYWORDS,
PERSONALITY_WRAPPER, DEBATE_PERSONAS, etc.) now lives in:
  - config/departments.yaml  (76 agents across 9 departments)
  - config/personality.yaml  (personality wrapper + debate personas)
  - core/agent_registry.py   (registry loader + lookup helpers)

This file re-exports everything from core.agent_registry for backwards
compat with existing callers (router.py, handlers/, etc.).
"""

from __future__ import annotations

import logging

from core.agent_registry import (
    AGENT_REGISTRY,
    DEFAULT_AGENT,
    FALLBACK_CHAIN,
    LEGACY_TASK_KEYWORDS,
    PERSONA_WRAPPER,
    TASK_KEYWORDS,
    _LEGACY_AGENT_MODELS,
    detect_agent,
    get_fallback_chain,
    get_model,
)

logger = logging.getLogger(__name__)

# ── Re-export from core.agent_registry (single source of truth) ───────────────
# AGENT_MODELS: {agent_key: primary_model} — mirrors old agents.py AGENT_MODELS
AGENT_MODELS = _LEGACY_AGENT_MODELS.copy()

# Alias for backwards compat
PERSONALITY_WRAPPER = PERSONA_WRAPPER

# Pull DEBATE_* from core.agent_registry (loaded from personality.yaml there)
from core.agent_registry import DEBATE_PERSONAS, DEBATE_PERSONA_MODELS, DEBATE_ICONS

# ── Conversation interface (shared state with llm_client/router) ───────────────
# All conversation state and thread memory now live in core.conversation_interface
from core.conversation_interface import (
    ACTIVE_THREADS,
    CONVERSATION_HISTORY,
    add_to_conversation,
    add_to_thread,
    clear_conversation,
    clear_thread,
    get_conversation_history,
    get_conversation_summary_prompt,
    get_thread_context,
    list_threads,
    list_threads_raw,
)

# Re-export for backwards compat (detect_agent/get_fallback_chain are from core.agent_registry)
from core.conversation_interface import detect_agent as detect_agent
from core.conversation_interface import get_fallback_chain as get_fallback_chain

# ── Build system prompt ────────────────────────────────────────────────────────


def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
    parts = [PERSONALITY_WRAPPER.strip()]
    if user_id:
        ctx = get_conversation_summary_prompt(user_id)
        if ctx:
            parts.append(ctx)
    parts.append(role_prompt)
    return "\n\n".join(parts)


# ── List agents/departments ───────────────────────────────────────────────────


def list_agents() -> str:
    """List all agents (delegates to core.agent_registry)."""
    from core.agent_registry import list_agents as _list

    return _list()


def list_all_departments() -> list[str]:
    """List all departments."""
    from core.agent_registry import list_all_departments as _list_depts

    return _list_depts()


# Ensure gemma4 local availability
def ensure_gemma4_local_available() -> bool:
    import subprocess

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if "gemma4:e4b" in result.stdout:
            return True
        subprocess.run(["ollama", "pull", "gemma4:e4b"], check=False, timeout=1800)
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        return "gemma4:e4b" in result.stdout
    except Exception as exc:
        logger.warning("gemma4 local availability check failed: %s", exc)
        return False


# ── Backwards compat: also expose via 'agents' module import ──────────────────
# Legacy callers may do "from agents import detect_agent" etc.
__all__ = [
    "AGENT_MODELS",
    "AGENT_REGISTRY",
    "FALLBACK_CHAIN",
    "TASK_KEYWORDS",
    "DEFAULT_AGENT",
    "ACTIVE_THREADS",
    "CONVERSATION_HISTORY",
    "DEBATE_PERSONAS",
    "DEBATE_PERSONA_MODELS",
    "DEBATE_ICONS",
    "PERSONALITY_WRAPPER",
    "detect_agent",
    "get_model",
    "get_fallback_chain",
    "build_system_prompt",
    "list_agents",
    "list_all_departments",
    "add_to_thread",
    "get_thread_context",
    "list_threads",
    "list_threads_raw",
    "clear_thread",
    "add_to_conversation",
    "get_conversation_history",
    "clear_conversation",
    "get_conversation_summary_prompt",
    "ensure_gemma4_local_available",
]
