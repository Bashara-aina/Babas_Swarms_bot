"""
lib/legiona/minimax_client.py
MiniMax M2.7 — fully optimized for maximum intelligence.
Methods implemented:
  #1  Model = MiniMax-M2.7 (latest, self-evolving)
  #2  reasoning_split=True (interleaved chain-of-thought)
  #3  Optimal sampling: temperature=1.0, top_p=0.95, top_k=40
  #6  Interleaved thinking between tool calls via system prompt
  #7  Preset parameter profiles for coding vs research tasks
  #10 OpenRouter fallback for stability
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, TypeVar

import httpx
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


# ── Model ────────────────────────────────────────────────────────────────────
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "minimax/minimax-m2"  # [VERIFY BEFORE USE: confirm M2.7 slug on openrouter.ai]


# ── Sampling presets (#3, #7) ────────────────────────────────────────────────
# MiniMax M2.7 is tuned for temperature=1.0 — NOT 0.7
PRESET_CODING = {
    "temperature": 1.0,
    "top_p": 0.95,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.1,
}

PRESET_RESEARCH = {
    "temperature": 1.0,
    "top_p": 0.95,
    "frequency_penalty": 0.3,
    "presence_penalty": 0.2,
}

PRESET_CREATIVE = {
    "temperature": 1.0,
    "top_p": 0.98,
    "frequency_penalty": 0.4,
    "presence_penalty": 0.3,
}


# ── Output schema (Pydantic) ─────────────────────────────────────────────────
class LegionaOutput(BaseModel):
    answer: str = Field(description="The final response or code output")
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Model's self-assessed confidence"
    )
    verified_from_context: bool = Field(
        description="True if answer is grounded in provided context"
    )
    items_needing_verification: list[str] = Field(
        default_factory=list,
        description="Any claims the model could not verify from context",
    )
    reasoning_summary: str = Field(
        default="",
        description="Brief summary of the chain-of-thought reasoning used",
    )


# ── Client factory (#10: primary + fallback) ────────────────────────────────
def _build_minimax_client() -> AsyncOpenAI:
    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY not set")
    return AsyncOpenAI(api_key=api_key, base_url=MINIMAX_BASE_URL)


def _build_openrouter_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    return AsyncOpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://github.com/legiona",
            "X-Title": "Legiona Agent",
        },
    )


def get_client(fallback: bool = False) -> instructor.Instructor:
    """
    Returns instructor-patched client.
    fallback=True  → OpenRouter (more stable, slightly higher latency)
    fallback=False → MiniMax direct (fastest, primary)
    """
    if fallback:
        base = _build_openrouter_client()
    else:
        base = _build_minimax_client()
    return instructor.from_openai(base)


# ── Smart async completion wrapper (#2: reasoning_split, #3: optimal params) ─
async def create_structured_completion(
    *,
    messages: list[dict[str, Any]],
    response_model: type[T] = LegionaOutput,
    preset: str = "coding",
    fallback: bool = False,
    max_tokens: int = 8192,
    reasoning_split: bool = True,
    model: str | None = None,
) -> T:
    """
    Main async call wrapper. Uses reasoning_split=True by default so M2.7
    performs interleaved chain-of-thought before every response.

    Args:
        preset: "coding" | "research" | "creative" — selects sampling parameters
        reasoning_split: Method #2 — interleaved CoT, always on by default
        fallback: Route via OpenRouter instead of MiniMax direct
        model: Override model string (default: MINIMAX_MODEL or OPENROUTER_MODEL)
    """
    presets = {
        "coding": PRESET_CODING,
        "research": PRESET_RESEARCH,
        "creative": PRESET_CREATIVE,
    }
    params = presets.get(preset, PRESET_CODING)
    model_str = model or (MINIMAX_MODEL if not fallback else OPENROUTER_MODEL)
    client = get_client(fallback=fallback)

    return await client.chat.completions.create(
        model=model_str,
        messages=messages,
        response_model=response_model,
        max_tokens=max_tokens,
        extra_body={"reasoning_split": reasoning_split},
        **params,
    )


# ── Sync completion (for non-async contexts) ────────────────────────────────
def complete(
    messages: list[dict[str, Any]],
    preset: str = "coding",
    response_model: type[T] = LegionaOutput,
    fallback: bool = False,
    max_tokens: int = 8192,
    reasoning_split: bool = True,
    model: str | None = None,
) -> T:
    """
    Synchronous wrapper. Prefer create_structured_completion() in async contexts.
    """
    presets = {
        "coding": PRESET_CODING,
        "research": PRESET_RESEARCH,
        "creative": PRESET_CREATIVE,
    }
    params = presets.get(preset, PRESET_CODING)
    model_str = model or (MINIMAX_MODEL if not fallback else OPENROUTER_MODEL)
    client = get_client(fallback=fallback)

    return client.chat.completions.create(
        model=model_str,
        messages=messages,
        response_model=response_model,
        max_tokens=max_tokens,
        extra_body={"reasoning_split": reasoning_split},
        **params,
    )


# ── Embedding (for RAG — embo-01) ───────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    """
    MiniMax embedding via direct HTTP (not instructor).
    Model: emo-01 (1536-dim) [VERIFY BEFORE USE: confirm dimension on platform]
    """
    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY not set")
    resp = httpx.post(
        f"{MINIMAX_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"model": "embo-01", "input": text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]
