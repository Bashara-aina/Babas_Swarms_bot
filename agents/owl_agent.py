from __future__ import annotations

import logging
from llm_client import chat

logger = logging.getLogger(__name__)


async def run_owl_task(task: str, user_role: str = "User", assistant_role: str = "Assistant") -> str:
    prompt = (
        f"You are OWL specialist mode. User role: {user_role}. Assistant role: {assistant_role}.\n"
        "Solve this complex task with strong reasoning and practical output:\n"
        f"{task}"
    )
    for agent in ("analyst", "architect", "general"):
        try:
            result, _ = await chat(prompt, agent_key=agent, user_id="owl")
            if result:
                return result
        except Exception as exc:
            logger.warning("OWL fallback %s failed: %s", agent, exc)
    return "OWL agent unavailable right now."
