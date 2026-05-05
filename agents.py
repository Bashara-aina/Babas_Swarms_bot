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
    _LEGACY_AGENT_MODELS,
    AGENT_REGISTRY,
    DEBATE_ICONS,
    DEBATE_PERSONA_MODELS,
    DEBATE_PERSONAS,
    DEFAULT_AGENT,
    FALLBACK_CHAIN,
    LEGACY_TASK_KEYWORDS,
    PERSONA_WRAPPER,
    TASK_KEYWORDS,
    detect_agent,
    get_fallback_chain,
    get_model,
)
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
from core.conversation_interface import (
    detect_agent as detect_agent,
)
from core.conversation_interface import (
    get_fallback_chain as get_fallback_chain,
)

logger = logging.getLogger(__name__)

# ── Re-export from core.agent_registry (single source of truth) ───────────────
AGENT_MODELS = _LEGACY_AGENT_MODELS.copy()

PERSONALITY_WRAPPER = PERSONA_WRAPPER


def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
    """Legacy compat stub — prepends personality wrapper to a role prompt.

    Real implementation lives in ``agents/__init__.py`` (the package).
    This stub satisfies the ``router.py`` re-export path.
    """
    wrapper = PERSONA_WRAPPER.strip() if PERSONA_WRAPPER else ""
    return f"{wrapper}\n\n{role_prompt}" if wrapper else role_prompt


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
    "ACTIVE_THREADS",
    "AGENT_MODELS",
    "AGENT_REGISTRY",
    "CONVERSATION_HISTORY",
    "DEBATE_ICONS",
    "DEBATE_PERSONAS",
    "DEBATE_PERSONA_MODELS",
    "DEFAULT_AGENT",
    "FALLBACK_CHAIN",
    "PERSONALITY_WRAPPER",
    "TASK_KEYWORDS",
    "add_to_conversation",
    "add_to_thread",
    "build_system_prompt",
    "clear_conversation",
    "clear_thread",
    "detect_agent",
    "ensure_gemma4_local_available",
    "get_conversation_history",
    "get_conversation_summary_prompt",
    "get_fallback_chain",
    "get_model",
    "get_thread_context",
    "list_agents",
    "list_all_departments",
    "list_threads",
    "list_threads_raw",
]
