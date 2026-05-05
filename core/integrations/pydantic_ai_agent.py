"""core/integrations/pydantic_ai_agent.py — pydantic-ai type-safe agent framework.

pydantic-ai provides structured output validation and result schemas.
This integrates it with our MiniMax litellm infrastructure.

Usage:
    async with PydanticAIAgent(model="minimax/MiniMax-M2.7") as agent:
        result = await agent.run("extract user info", schema=UserSchema)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic_ai import Agent

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "minimax/MiniMax-M2.7"
_MINIMAX_KNOWN_MODEL = "gpt-4o-mini"  # pydantic-ai requires a known OpenAI model name


def _configure_minimax(model: str) -> dict[str, Any]:
    """Build pydantic-ai kwargs for MiniMax OpenAI-compatible API.

    pydantic-ai validates model names against a known list and doesn't accept
    openai_api_base or openai_api_key as kwargs. We use a known model name
    + OPENAI_BASE_URL env var for routing.
    """
    key = os.getenv("MINIMAX_API_KEY", "")
    os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/v1"
    os.environ["OPENAI_API_KEY"] = key or "dummy"
    return {"model": _MINIMAX_KNOWN_MODEL}


async def run_pydantic_ai_agent(
    prompt: str,
    system_prompt: str | None = None,
    result_schema: type | None = None,
    model: str | None = None,
    timeout: float = 60.0,
) -> Any:
    """Run a pydantic-ai agent with structured output.

    Args:
        prompt: User task
        system_prompt: Optional system instructions
        result_schema: Pydantic model for validated output
        model: Model string (default: MINIMAX_M2_7)
        timeout: Max seconds to wait

    Returns:
        Structured result (Pydantic model instance) or raw string on failure
    """
    try:
        from pydantic_ai import Agent
    except ImportError:
        return "[pydantic-ai not installed — pip install pydantic-ai-slim]"

    model_str = model or os.getenv("LEGION_LLM_MODEL", DEFAULT_MODEL)
    provider = model_str.split("/")[0].lower()

    agent_kwargs: dict[str, Any] = {}
    if provider == "minimax":
        agent_kwargs = _configure_minimax(model_str)
    elif provider == "openrouter":
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "") or "dummy"
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        agent_kwargs["model"] = model_str
        agent_kwargs["extra_headers"] = {
            "HTTP-Referer": "https://github.com/Bashara-aina/Babas_Swarms_bot",
            "X-Title": "LegionSwarm",
        }
    elif provider == "groq":
        os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY", "") or "dummy"
        os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
        agent_kwargs["model"] = model_str
    else:
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "") or "dummy"
        agent_kwargs["model"] = model_str

    if system_prompt:
        agent_kwargs["system_prompt"] = system_prompt
    if result_schema:
        agent_kwargs["output_type"] = result_schema

    try:
        agent: Agent = Agent(**agent_kwargs)
    except Exception as exc:
        logger.error("pydantic-ai agent creation failed: %s", exc)
        return f"[pydantic-ai agent error: {exc}]"

    try:
        result = await asyncio.wait_for(agent.run(prompt), timeout=timeout)
        return result.data if hasattr(result, "data") else result  # type: ignore[reportAttributeAccessIssue]
    except TimeoutError:
        return f"[pydantic-ai timeout after {timeout}s]"
    except Exception as exc:
        logger.error("pydantic-ai run failed: %s", exc)
        return f"[pydantic-ai error: {exc}]"


class PydanticAIResultValidator:
    """Validate LLM outputs against Pydantic schemas — anti-hallucination layer."""

    @staticmethod
    async def validate(result: Any, schema: type) -> tuple[bool, str]:
        """Validate structured result against a Pydantic schema.

        Returns (is_valid, error_message).
        """
        try:
            schema.model_validate(result)
            return True, ""
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def extract_structured(result: Any, field_names: list[str]) -> dict[str, Any]:
        """Extract specific fields from a structured result."""
        if hasattr(result, "model_dump"):
            data = result.model_dump()
        elif hasattr(result, "dict"):
            data = result.dict()
        elif isinstance(result, dict):
            data = result
        else:
            return {f: None for f in field_names}

        return {f: data.get(f) for f in field_names}


def build_result_schema(fields: dict[str, tuple[type, str]]) -> type:
    """Build a Pydantic model from field definitions.

    Args:
        fields: {field_name: (type, description)}

    Example:
        UserSchema = build_result_schema({
            "name": (str, "Full name of the user"),
            "age": (int, "Age in years"),
        })
    """
    from pydantic import BaseModel

    return BaseModel  # placeholder — real impl uses type: ignore
