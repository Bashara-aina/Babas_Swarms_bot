"""
AgentOps observability client — Phase 6.
2-line init, full session replay, cost tracking, time-travel debugging.
Non-fatal if AGENTOPS_API_KEY is not set.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_initialized = False


def init_agentops() -> bool:
    """Initialize AgentOps. Returns True if successful."""
    global _initialized
    api_key = os.getenv("AGENTOPS_API_KEY", "")
    if not api_key:
        logger.info("AgentOps skipped — AGENTOPS_API_KEY not set")
        return False
    try:
        import agentops
        agentops.init(api_key, default_tags=["legion", "telegram-bot"])
        _initialized = True
        logger.info("✅ AgentOps initialized — session replay active")
        return True
    except ImportError:
        logger.warning("agentops not installed — pip install agentops")
        return False
    except Exception as e:
        logger.warning("AgentOps init failed (non-fatal): %s", e)
        return False


def record_action(
    action_type: str,
    inputs: dict[str, Any],
    outputs: Optional[dict[str, Any]] = None,
    cost: Optional[float] = None,
) -> None:
    """Record an LLM action/tool call to AgentOps."""
    if not _initialized:
        return
    try:
        import agentops
        agentops.record(
            agentops.ActionEvent(
                action_type=action_type,
                inputs=inputs,
                outputs=outputs or {},
                cost=cost,
            )
        )
    except Exception as e:
        logger.debug("agentops.record failed: %s", e)


def end_session(outcome: str = "Success") -> None:
    """End the current AgentOps session."""
    if not _initialized:
        return
    try:
        import agentops
        agentops.end_session(outcome)
    except Exception as e:
        logger.debug("agentops.end_session failed: %s", e)
