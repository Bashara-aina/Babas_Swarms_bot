from __future__ import annotations

import logging
import time
from typing import Any

from core.structured_outputs import AgentResponse, SwarmResult
from llm_client import chat

logger = logging.getLogger(__name__)

_AGENT_CHAIN = ["general", "coding", "debug", "architect"]


def _safe_answer(payload: Any) -> str:
    if isinstance(payload, AgentResponse):
        return payload.answer
    if isinstance(payload, dict):
        return str(payload.get("answer") or payload.get("content") or "")
    return str(payload or "")


async def run_with_handoffs(task: str, start_agent: str = "general") -> SwarmResult:
    started = time.perf_counter()
    if start_agent in _AGENT_CHAIN:
        chain = [start_agent] + [a for a in _AGENT_CHAIN if a != start_agent]
    else:
        chain = list(_AGENT_CHAIN)

    traces = []
    current = task
    final_output = ""

    for agent in chain:
        step_start = time.perf_counter()
        try:
            response, model = await chat(current, agent_key=agent, user_id="sdk")
            final_output = response
            traces.append(
                {
                    "agent": agent,
                    "model": model,
                    "step": f"handoff:{agent}",
                    "latency_ms": (time.perf_counter() - step_start) * 1000.0,
                    "tokens_used": 0,
                }
            )
            current = (
                f"Previous agent ({agent}) output:\n{response}\n\n"
                "Refine this further and return only improved final output."
            )
        except Exception as exc:
            logger.warning("handoff step failed for %s: %s", agent, exc)
            traces.append(
                {
                    "agent": agent,
                    "model": "",
                    "step": f"handoff-error:{agent}",
                    "latency_ms": (time.perf_counter() - step_start) * 1000.0,
                    "tokens_used": 0,
                }
            )

    return SwarmResult(
        final_output=final_output,
        topology_used="openai_agents_handoff",
        agent_traces=traces,
        total_tokens=0,
        total_latency_ms=(time.perf_counter() - started) * 1000.0,
        success=bool(final_output),
        error=None if final_output else "no output from handoff chain",
    )
