"""MiroFish-style multi-agent consensus forecast (lightweight)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.mirofish_agent import MiroFishResult


async def run_simulation(question: str) -> "MiroFishResult":
    from agents.mirofish_agent import MiroFishAgent

    agent = MiroFishAgent()
    return await agent.predict(question)
