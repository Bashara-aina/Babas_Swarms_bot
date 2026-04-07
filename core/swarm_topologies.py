from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from llm_client import chat
from core.structured_outputs import SwarmResult

logger = logging.getLogger(__name__)

TOPOLOGIES = {
    "spreadsheet": "spreadsheet",
    "mixture": "mixture",
    "graph": "graph",
    "sequential": "sequential",
    "concurrent": "concurrent",
    "debate": "debate",
    "auto": "auto",
}


async def _run_sequential(task: str, agent_names: list[str]) -> tuple[str, list[dict[str, Any]]]:
    traces: list[dict[str, Any]] = []
    current = task
    final = ""
    for agent in agent_names:
        started = time.perf_counter()
        output, model = await chat(current, agent_key=agent, user_id="swarm")
        traces.append(
            {
                "agent": agent,
                "model": model,
                "step": "sequential",
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "tokens_used": 0,
            }
        )
        final = output
        current = f"Task: {task}\n\nPrior result by {agent}:\n{output}\n\nImprove this answer."
    return final, traces


async def _run_concurrent(task: str, agent_names: list[str]) -> tuple[str, list[dict[str, Any]]]:
    async def _call(agent: str) -> tuple[str, str, float]:
        started = time.perf_counter()
        output, model = await chat(task, agent_key=agent, user_id="swarm")
        return output, model, (time.perf_counter() - started) * 1000.0

    calls = await asyncio.gather(*[_call(a) for a in agent_names], return_exceptions=True)
    traces: list[dict[str, Any]] = []
    outputs: list[str] = []
    for agent, item in zip(agent_names, calls):
        if isinstance(item, Exception):
            logger.warning("concurrent step failed for %s: %s", agent, item)
            continue
        out, model, latency = item
        outputs.append(f"[{agent}] {out}")
        traces.append(
            {
                "agent": agent,
                "model": model,
                "step": "concurrent",
                "latency_ms": latency,
                "tokens_used": 0,
            }
        )
    merged = "\n\n".join(outputs)
    if not merged:
        return "", traces
    synthesis, _ = await chat(
        f"Synthesize this multi-agent output into one final answer:\n\n{merged}",
        agent_key="architect",
        user_id="swarm",
    )
    return synthesis, traces


async def run_topology(task: str, topology: str, agent_names: list[str]) -> SwarmResult:
    started = time.perf_counter()
    selected = topology if topology in TOPOLOGIES else "sequential"
    agents = agent_names or ["general", "coding", "debug", "architect"]

    try:
        if selected in {"spreadsheet", "mixture", "graph", "sequential", "debate"}:
            final, traces = await _run_sequential(task, agents)
        elif selected in {"concurrent", "auto"}:
            final, traces = await _run_concurrent(task, agents)
        else:
            final, traces = await _run_sequential(task, agents)

        return SwarmResult(
            final_output=final,
            agent_traces=traces,
            topology_used=selected,
            total_tokens=0,
            total_latency_ms=(time.perf_counter() - started) * 1000.0,
            success=bool(final),
            error=None if final else "empty swarm output",
        )
    except Exception as exc:
        logger.warning("topology %s failed; fallback to sequential: %s", selected, exc)
        try:
            final, traces = await _run_sequential(task, agents)
            return SwarmResult(
                final_output=final,
                agent_traces=traces,
                topology_used="sequential",
                total_tokens=0,
                total_latency_ms=(time.perf_counter() - started) * 1000.0,
                success=bool(final),
                error=None if final else str(exc),
            )
        except Exception as fallback_exc:
            return SwarmResult(
                final_output="",
                topology_used="sequential",
                total_tokens=0,
                total_latency_ms=(time.perf_counter() - started) * 1000.0,
                success=False,
                error=str(fallback_exc),
            )
