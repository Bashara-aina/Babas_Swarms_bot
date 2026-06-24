"""MiroFish-style simulation with trigger detection and LLM scenario extraction."""

from __future__ import annotations

import os

TRIGGER_PHRASES = (
    "simulate",
    "predict",
    "what if",
    "how would",
    "should i",
    "pros and cons",
    "market reaction",
    "what happens if",
    "how will",
    "what do you think about launching",
)


def should_trigger_simulation(user_message: str) -> bool:
    m = (user_message or "").lower()
    return any(p in m for p in TRIGGER_PHRASES)


async def extract_scenario(user_message: str) -> str:
    from llm_client import wiki_raw_completion

    raw = await wiki_raw_completion(
        f"Extract the core scenario to simulate in 1–2 sentences. Message:\n{user_message[:2000]}",
        model=os.getenv("LEGION_SIM_SCENARIO_MODEL", "opencode-go/minimax-m3"),
        max_tokens=120,
    )
    return (raw or user_message).strip()


async def run_simulation_agent(user_message: str, *, context: str = "") -> str:
    from tools.simulation_tool import run_simulation

    scenario = await extract_scenario(user_message)
    res = await run_simulation(scenario + (f"\n\nContext: {context}" if context else ""))
    diss = "\n".join(res.dissenting_views)
    return (
        f"**Prediction**\n{res.prediction}\n\n"
        f"**Confidence** {res.confidence_score:.2f}\n\n"
        f"**Dissent**\n{diss}"
    )
