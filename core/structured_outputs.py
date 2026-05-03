from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class AgentTrace(BaseModel):
    agent: str
    model: str = ""
    step: str = ""
    latency_ms: float = 0.0
    tokens_used: int = 0


class AgentResponse(BaseModel):
    answer: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    reasoning_steps: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    model_used: str = ""
    latency_ms: float = 0.0


class SubTask(BaseModel):
    id: str
    agent: str
    task: str


class SwarmResult(BaseModel):
    final_output: str
    agent_traces: list[AgentTrace] = Field(default_factory=list)
    topology_used: str = "sequential"
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    success: bool = True
    error: str | None = None


class TaskPlan(BaseModel):
    subtasks: list[SubTask] = Field(default_factory=list)
    dependency_graph: dict[str, list[str]] = Field(default_factory=dict)
    estimated_complexity: int = Field(default=5, ge=1, le=10)
    recommended_topology: str = "auto"

    @model_validator(mode="after")
    def _normalize(self) -> TaskPlan:
        self.estimated_complexity = max(1, min(10, int(self.estimated_complexity)))
        return self


class CodeResult(BaseModel):
    code: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: float = 0.0


class ConversationTurn(BaseModel):
    speaker: str
    content: str


class ConversationResult(BaseModel):
    output: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0


class MiroFishResult(BaseModel):
    prediction: str
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    dissenting_views: list[str] = Field(default_factory=list)


def coerce_agent_response(payload: Any, default_model: str = "") -> AgentResponse:
    if isinstance(payload, AgentResponse):
        return payload
    if isinstance(payload, dict):
        if "answer" not in payload and "content" in payload:
            payload = {**payload, "answer": str(payload.get("content", ""))}
        return AgentResponse(**payload)
    return AgentResponse(answer=str(payload or ""), model_used=default_model)
