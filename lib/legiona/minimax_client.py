"""Reusable MiniMax client helpers with Instructor + Pydantic validation."""

from __future__ import annotations

import os
from typing import Any, Literal, TypeVar

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

# MiniMax base URL — [VERIFY BEFORE USE: confirm endpoint]
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
# Default model — [VERIFY BEFORE USE: confirm model name]
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")


class LegionaOutput(BaseModel):
    """Default structured response schema for Legiona completions."""

    answer: str = Field(..., description="Main response content.")
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Self-assessed confidence.")
    verified_from_context: bool = Field(..., description="Whether response is grounded in available context.")
    items_needing_verification: list[str] = Field(default_factory=list, description="Claims requiring verification.")


def _build_minimax_client() -> AsyncOpenAI:
    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY not set")
    return AsyncOpenAI(api_key=api_key, base_url=MINIMAX_BASE_URL)


def get_client() -> Any:
    """Return instructor-patched MiniMax client (OpenAI-compatible)."""
    return instructor.from_openai(_build_minimax_client())


async def create_structured_completion(
    *,
    messages: list[dict[str, Any]],
    response_model: type[T] = LegionaOutput,
    model: str = MINIMAX_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> T:
    """Create a structured completion from MiniMax using Instructor."""
    client = get_client()
    return await client.chat.completions.create(
        model=model,
        messages=messages,
        response_model=response_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
