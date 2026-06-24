"""Agent router — imports from canonical core modules.

Re-exports everything legacy callers need from a single location.
"""

from __future__ import annotations

import logging

from core.agent_registry import (
    _LEGACY_AGENT_MODELS as _LEGACY_AGENT_MODELS,
)
from core.agent_registry import (
    PERSONA_WRAPPER as PERSONALITY_WRAPPER,
)
from core.agent_registry import (
    TASK_KEYWORDS as TASK_KEYWORDS,
)
from core.agent_registry import (
    detect_agent as detect_agent,
)
from core.agent_registry import (
    get_fallback_chain as get_fallback_chain,
)
from core.agent_registry import (
    get_model as get_model,
)
from core.agent_registry import (
    get_thread_context as get_thread_context,
)
from core.agent_registry import (
    list_agents as list_agents,
)

logger = logging.getLogger(__name__)

# ── Re-exports ───────────────────────────────────────────────────────────────
AGENT_MODELS = _LEGACY_AGENT_MODELS.copy()
DEFAULT_AGENT = "general"

# Debate personas — from agents package (only source)
try:
    from agents import (
        DEBATE_ICONS as DEBATE_ICONS,
    )
    from agents import (
        DEBATE_PERSONA_MODELS as DEBATE_PERSONA_MODELS,
    )
    from agents import (
        DEBATE_PERSONAS as DEBATE_PERSONAS,
    )
    from agents import build_system_prompt as build_system_prompt
except ImportError:
    DEBATE_ICONS: dict = {}
    DEBATE_PERSONA_MODELS: dict = {}
    DEBATE_PERSONAS: dict = {}

    def build_system_prompt(role_prompt: str, user_id: str = "") -> str:
        wrapper = PERSONALITY_WRAPPER.strip() if PERSONALITY_WRAPPER else ""
        return f"{wrapper}\n\n{role_prompt}" if wrapper else role_prompt
