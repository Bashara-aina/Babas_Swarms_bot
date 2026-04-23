from __future__ import annotations

import asyncio
import time

from core.structured_outputs import ConversationResult, ConversationTurn
from llm_client import chat


async def run_ag2_conversation(task: str, max_turns: int = 10) -> ConversationResult:
    started = time.perf_counter()
    turns: list[ConversationTurn] = []
    roles = ["researcher", "debug", "architect"]
    context = task

    for i in range(max(2, min(max_turns, 10))):
        role = roles[i % len(roles)]
        answer, _ = await chat(context, agent_key=role, user_id="ag2")
        turns.append(ConversationTurn(speaker=role, content=answer[:3000]))
        context = f"Previous message by {role}:\n{answer}\n\nRespond with critique + improvements."

    final = turns[-1].content if turns else ""
    return ConversationResult(
        output=final,
        turns=turns,
        tokens_used=0,
        latency_ms=(time.perf_counter() - started) * 1000.0,
    )


class ResearchSwarm:
    async def run(self, task: str, max_turns: int = 6) -> ConversationResult:
        return await run_ag2_conversation(task, max_turns=max_turns)
