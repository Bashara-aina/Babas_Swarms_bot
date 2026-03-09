"""LLM client — direct litellm calls with cloud-only fallback chain.

Replaces open-interpreter / interpreter_bridge. No Ollama. No local models.
Fallback order: Cerebras → Groq → Gemini → OpenRouter (all free tiers).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional

import litellm
from litellm import acompletion

from agents import detect_agent, get_fallback_chain, add_to_thread

logger = logging.getLogger(__name__)

# Suppress litellm's noisy success logs
litellm.suppress_debug_info = True

# ── System prompts per agent ────────────────────────────────────────────────
SYSTEM_PROMPTS: dict[str, str] = {
    "vision": (
        "You analyze screenshots and visual interfaces on a Linux desktop. "
        "Describe what you see clearly: UI elements, text, errors, layout. "
        "Then suggest the most useful next action. Be concise and specific."
    ),
    "coding": (
        "You are an expert software engineer. Write clean, working code. "
        "For shell tasks, provide exact commands. Explain what each block does. "
        "Prefer minimal solutions. Always include error handling."
    ),
    "debug": (
        "You are a debugging expert for Python, PyTorch, and Linux systems. "
        "1. Identify the root cause in ONE sentence. "
        "2. Give the minimal targeted fix (code or command). "
        "3. Explain WHY it failed. "
        "4. Add a preventive guard for the future."
    ),
    "math": (
        "You are a mathematics expert specializing in ML/deep learning. "
        "Show step-by-step derivations. Verify numerics with Python/NumPy. "
        "For tensors, always show shapes. For gradients, show chain rule."
    ),
    "architect": (
        "You are a system architect. Design scalable, maintainable solutions. "
        "Focus on structure, data flow, and component boundaries. "
        "For ML systems: data pipeline → training loop → evaluation → deployment. "
        "Use ASCII diagrams when helpful."
    ),
    "analyst": (
        "You are a data analyst for ML training metrics and system performance. "
        "Identify trends and anomalies. Write Python for visualizations. "
        "Alert on: NaN/Inf values, loss spikes > 2×, GPU util < 50%."
    ),
    "general": (
        "You are a smart, concise AI assistant running on a Linux server. "
        "Answer clearly and directly. For technical tasks, show exact commands. "
        "For complex topics, structure your response with clear sections."
    ),
}

# ── Rate limit tracking ─────────────────────────────────────────────────────
_rate_limited: dict[str, float] = {}  # provider → timestamp
_COOLDOWN = 90  # seconds


def _is_rate_limited(model: str) -> bool:
    provider = model.split("/")[0]
    if provider not in _rate_limited:
        return False
    return (time.time() - _rate_limited[provider]) < _COOLDOWN


def _mark_rate_limited(model: str) -> None:
    provider = model.split("/")[0]
    _rate_limited[provider] = time.time()
    logger.warning("Rate limited: %s (cooling %ds)", provider, _COOLDOWN)


def _get_api_key(model: str) -> Optional[str]:
    """Return the API key for a model's provider, or None if missing."""
    provider = model.split("/")[0].lower()
    key_map = {
        "cerebras":   "CEREBRAS_API_KEY",
        "groq":       "GROQ_API_KEY",
        "gemini":     "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai":        "ZAI_API_KEY",
    }
    env_var = key_map.get(provider)
    if not env_var:
        return None
    return os.getenv(env_var) or None


# ── Core LLM call ───────────────────────────────────────────────────────────

async def _call_model(
    model: str,
    messages: list[dict],
    max_tokens: int = 2048,
) -> str:
    """Make a single async litellm completion call."""
    provider = model.split("/")[0].lower()

    # Build kwargs — litellm accepts api_key + optional api_base
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    api_key = _get_api_key(model)
    if not api_key:
        raise ValueError(f"No API key for provider '{provider}' — set {provider.upper()}_API_KEY in .env")

    # Special case: ZAI uses OpenAI-compatible endpoint with custom base
    if provider == "zai":
        model_name = "/".join(model.split("/")[1:])
        kwargs["model"] = f"openai/{model_name}"
        kwargs["api_base"] = "https://open.bigmodel.cn/api/paas/v4"
        kwargs["api_key"] = api_key
    else:
        kwargs["api_key"] = api_key
        # OpenRouter requires extra headers for routing
        if provider == "openrouter":
            kwargs["extra_headers"] = {
                "HTTP-Referer": "https://github.com/babas-swarms",
                "X-Title": "BabasSwarms",
            }

    response = await acompletion(**kwargs)
    content = response.choices[0].message.content or ""
    return content.strip()


async def chat(
    task: str,
    agent_key: Optional[str] = None,
    thread_id: Optional[str] = None,
    image_url: Optional[str] = None,
) -> tuple[str, str]:
    """Send a task to the best available cloud model.

    Returns:
        (response_text, model_used)
    """
    if agent_key is None:
        agent_key = detect_agent(task)

    chain = get_fallback_chain(agent_key)
    system_prompt = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["general"])

    # Build message list
    user_content: list | str
    if image_url:
        user_content = [
            {"type": "text", "text": task},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    else:
        user_content = task

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    last_error: Exception = Exception("No models available")

    for model in chain:
        if _is_rate_limited(model):
            logger.debug("Skipping rate-limited model: %s", model)
            continue

        try:
            logger.info("Trying model: %s (agent=%s)", model, agent_key)
            result = await _call_model(model, messages)

            if thread_id:
                add_to_thread(thread_id, agent_key, task, result)

            logger.info("Success: %s", model)
            return result, model

        except litellm.RateLimitError:
            _mark_rate_limited(model)
            logger.warning("Rate limit hit: %s — trying next", model)
            continue

        except litellm.AuthenticationError:
            logger.error("Auth error for %s — check your API key", model)
            last_error = Exception(f"Auth error for {model} — verify your API key in .env")
            continue

        except ValueError as e:
            # Missing API key
            logger.error("%s", e)
            last_error = e
            continue

        except Exception as e:
            logger.warning("Error with %s: %s — trying next", model, e)
            last_error = e
            continue

    raise RuntimeError(
        f"All models in fallback chain exhausted.\nLast error: {last_error}\n"
        "Check your API keys in .env and ensure at least one provider has quota."
    )


async def run_shell_command(cmd: str, timeout: int = 30) -> str:
    """Execute a shell command on the host PC and return output."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode == 0:
            return out or "(command completed, no output)"
        else:
            return f"Exit code {proc.returncode}\n{err or out}"

    except asyncio.TimeoutError:
        return f"⏱ Command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"


def chunk_output(text: str, max_length: int = 4000) -> list[str]:
    """Split long responses into Telegram-safe chunks (≤4096 chars)."""
    if len(text) <= max_length:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            chunks.append(current.rstrip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def verify_api_keys() -> dict[str, bool]:
    """Check which API keys are present in the environment."""
    keys = {
        "CEREBRAS_API_KEY":   "cerebras",
        "GROQ_API_KEY":       "groq",
        "GEMINI_API_KEY":     "gemini",
        "OPENROUTER_API_KEY": "openrouter",
        "ZAI_API_KEY":        "zai",
        "HF_TOKEN":           "huggingface",
    }
    return {name: bool(os.getenv(name)) for name in keys}
