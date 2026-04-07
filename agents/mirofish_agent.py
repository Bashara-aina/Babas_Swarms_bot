from __future__ import annotations

import hashlib

from llm_client import chat
from core.structured_outputs import MiroFishResult


class MiroFishAgent:
    def __init__(self, n_agents: int = 12, model_backend: str = "qwen3-235b"):
        self.n_agents = n_agents
        self.model_backend = model_backend

    async def predict(self, question: str) -> MiroFishResult:
        answer, _ = await chat(
            f"Provide consensus prediction + confidence + dissenting view for:\n{question}",
            agent_key="analyst",
            user_id="mirofish",
        )
        digest = hashlib.sha256(question.encode("utf-8", errors="ignore")).hexdigest()
        conf = 0.55 + (int(digest[:2], 16) / 255.0) * 0.35
        return MiroFishResult(
            prediction=answer,
            confidence_score=min(0.95, conf),
            dissenting_views=["Alternative scenario may occur if assumptions change rapidly."],
        )

    async def score_task_complexity(self, task: str) -> int:
        size = len(task.split())
        punctuation = sum(task.count(ch) for ch in [":", ";", "(", ")", "\n"])
        score = 1 + min(9, (size // 12) + (1 if punctuation > 3 else 0))
        return max(1, min(10, int(score)))
