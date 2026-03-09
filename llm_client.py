"""LLM client — cloud-first with Ollama only for vision specialisation.

Fallback policy:
  vision:    Ollama gemma3:12b (local) → Groq Llama-4-Scout (cloud)
  all other: cloud chain only (ZAI → Groq → Cerebras → Gemini → OpenRouter)
  NEVER fall back to Ollama for non-vision tasks.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import litellm
from litellm import acompletion

from router import detect_agent, get_fallback_chain, add_to_thread

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True

# ── Coworker system prompts ─────────────────────────────────────────────────
# Legion = Bas's AI coworker. Talks like a sharp senior dev, not a corporate bot.
_PERSONA = (
    "You're Legion — Bas's AI coworker running on his Linux workstation "
    "(RTX 3060 12GB, Ubuntu, ~/swarm-bot, Python 3.13, PyTorch/WorkerNet project). "
    "Talk like a sharp senior dev who knows the stack well. "
    "Direct, casual, no corporate speak. Say things like 'ok so the issue is...', "
    "'yeah that's because...', 'quick fix here is...'. "
    "When solving complex problems, think out loud briefly (2-3 sentences) then give the answer. "
    "Match Bas's language: Indonesian if he writes Indonesian, English if English, mixing both is fine. "
    "Never say 'As an AI...' or start with 'Certainly!' — just answer. "
    "Reference his actual setup when relevant."
)

SYSTEM_PROMPTS: dict[str, str] = {
    "vision": (
        f"{_PERSONA}\n\n"
        "You're analyzing a screenshot from Bas's desktop. "
        "Describe what you see clearly and specifically: what apps are open, "
        "any errors or warnings, relevant text, layout. "
        "Then suggest the most useful next action. Keep it tight."
    ),
    "coding": (
        f"{_PERSONA}\n\n"
        "You're the coding agent. Write clean, working code. "
        "For shell tasks give exact commands. Explain what each block does in one line. "
        "Prefer minimal solutions. Always handle errors. "
        "If you'd do it differently in production, say so briefly."
    ),
    "debug": (
        f"{_PERSONA}\n\n"
        "You're debugging. Work through it like this: "
        "1. Root cause in ONE sentence. "
        "2. Minimal fix (code or command). "
        "3. Why it failed. "
        "4. One-line preventive guard. "
        "No fluff, no padding. Show the reasoning, then the fix."
    ),
    "math": (
        f"{_PERSONA}\n\n"
        "You're the math agent. Show derivations step by step. "
        "For tensor ops, always show shapes at each step. "
        "For gradients, show chain rule explicitly. "
        "Verify numerically with Python/NumPy when it makes sense."
    ),
    "architect": (
        f"{_PERSONA}\n\n"
        "You're the system design agent. Focus on structure, data flow, "
        "component boundaries, failure modes. Use ASCII diagrams when helpful. "
        "For ML systems: data pipeline → training loop → eval → deployment. "
        "Give concrete trade-offs, not just options."
    ),
    "analyst": (
        f"{_PERSONA}\n\n"
        "You're the data/systems analyst. Extract real insights. "
        "Write Python for visualisations when relevant. "
        "For training runs: check loss curves, grad norms, GPU util, throughput. "
        "Flag anomalies: NaN/Inf, loss spikes >2x, GPU util <50%."
    ),
    "general": (
        f"{_PERSONA}\n\n"
        "Answer directly and clearly. For technical stuff, show exact commands. "
        "For complex topics, brief structure then the answer. "
        "If the task needs a specific agent (debug, math, coding), say which one and why."
    ),
}

# ── Rate limit tracking ─────────────────────────────────────────────────────
_rate_limited: dict[str, float] = {}
_COOLDOWN = 60  # seconds


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
    provider = model.split("/")[0].lower()
    key_map = {
        "cerebras":    "CEREBRAS_API_KEY",
        "groq":        "GROQ_API_KEY",
        "gemini":      "GEMINI_API_KEY",
        "openrouter":  "OPENROUTER_API_KEY",
        "zai":         "ZAI_API_KEY",
    }
    env_var = key_map.get(provider)
    return os.getenv(env_var) if env_var else None


def _strip_think_tags(text: str) -> tuple[str, str]:
    """Strip <think>...</think> from model output. Returns (thinking, answer)."""
    think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else ""
    answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return thinking, answer


# ── Core model call ─────────────────────────────────────────────────────────

async def _call_model(model: str, messages: list[dict], max_tokens: int = 2048) -> str:
    provider = model.split("/")[0].lower()
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    # Ollama — local, no API key needed
    if provider == "ollama_chat":
        model_name = model.replace("ollama_chat/", "")
        kwargs["model"] = f"ollama_chat/{model_name}"
        kwargs["api_base"] = "http://localhost:11434"
        kwargs["api_key"] = "ollama"

    # ZAI/GLM — OpenAI-compatible endpoint
    elif provider == "zai":
        model_name = "/".join(model.split("/")[1:])
        kwargs["model"] = f"openai/{model_name}"
        kwargs["api_base"] = "https://open.bigmodel.cn/api/paas/v4"
        api_key = os.getenv("ZAI_API_KEY", "")
        if not api_key:
            raise ValueError("ZAI_API_KEY not set in .env")
        kwargs["api_key"] = api_key

    # OpenRouter — needs extra headers
    elif provider == "openrouter":
        api_key = _get_api_key(model)
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        kwargs["api_key"] = api_key
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://github.com/Bashara-aina/Babas_Swarms_bot",
            "X-Title": "LegionSwarm",
        }

    # Standard cloud providers (cerebras, groq, gemini)
    else:
        api_key = _get_api_key(model)
        if not api_key:
            raise ValueError(
                f"No API key for '{provider}' — set {provider.upper()}_API_KEY in .env"
            )
        kwargs["api_key"] = api_key

    response = await acompletion(**kwargs)
    return (response.choices[0].message.content or "").strip()


# ── Main chat function ───────────────────────────────────────────────────────

async def chat(
    task: str,
    agent_key: Optional[str] = None,
    thread_id: Optional[str] = None,
    image_b64: Optional[str] = None,
    show_thinking: bool = False,
) -> tuple[str, str]:
    """Send a task to the best available model.

    Args:
        task:          User's message
        agent_key:     Force a specific agent (auto-detected if None)
        thread_id:     Conversation thread for memory
        image_b64:     Base64-encoded image for vision tasks
        show_thinking: If True, prepend <think> reasoning to output

    Returns:
        (response_text, model_used)
    """
    if agent_key is None:
        agent_key = detect_agent(task)

    # Vision agent with no image → skip Ollama, use cloud vision
    chain = get_fallback_chain(agent_key)
    if agent_key == "vision" and image_b64 is None:
        chain = [m for m in chain if not m.startswith("ollama_chat/")]

    system_prompt = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["general"])

    # Build messages
    if image_b64:
        user_content: list | str = [
            {"type": "text", "text": task},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
    else:
        user_content = task

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]

    last_error: Exception = Exception("No models available")

    for model in chain:
        if _is_rate_limited(model):
            logger.debug("Skipping rate-limited: %s", model)
            continue

        # Skip Ollama for non-vision or when no image
        if model.startswith("ollama_chat/") and agent_key != "vision":
            continue

        try:
            logger.info("Trying: %s (agent=%s)", model, agent_key)
            raw = await _call_model(model, messages)

            # Handle <think> tags from reasoning models (QwQ, R1, etc.)
            thinking, answer = _strip_think_tags(raw)
            if thinking and show_thinking:
                result = f"<i>💭 {thinking[:300]}{'…' if len(thinking) > 300 else ''}</i>\n\n{answer}"
            elif thinking:
                result = answer  # silently use the cleaner answer
            else:
                result = raw

            if thread_id:
                add_to_thread(thread_id, agent_key, task, result)

            logger.info("Success: %s", model)
            return result, model

        except litellm.RateLimitError:
            _mark_rate_limited(model)
            logger.warning("Rate limit: %s → trying next", model)
            continue

        except litellm.AuthenticationError:
            logger.error("Auth error for %s — check API key", model)
            last_error = Exception(f"Auth error for {model}")
            continue

        except ValueError as e:
            logger.error("%s", e)
            last_error = e
            continue

        except Exception as e:
            logger.warning("Error with %s: %s → trying next", model, e)
            last_error = e
            continue

    raise RuntimeError(
        f"All models exhausted for agent '{agent_key}'.\n"
        f"Last error: {last_error}\n"
        "Run /keys to check your API keys."
    )


# ── Screenshot utilities ─────────────────────────────────────────────────────

async def take_screenshot() -> Optional[str]:
    """Take a desktop screenshot. Returns file path or None."""
    ts = int(time.time())
    path = f"/tmp/legion_{ts}.png"
    # Try scrot first, then imagemagick import
    cmd = (
        f"DISPLAY=:0 scrot '{path}' 2>/dev/null || "
        f"DISPLAY=:0 import -window root '{path}' 2>/dev/null"
    )
    await run_shell_command(cmd, timeout=10)
    return path if Path(path).exists() else None


async def analyze_screenshot(image_path: str, question: str = "Describe what you see on screen.") -> tuple[str, str]:
    """Analyze a screenshot. Tries local Ollama first, then cloud vision.

    Returns:
        (analysis_text, model_used)
    """
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    # Try local Ollama (private — image never leaves the machine)
    try:
        result = await _call_model(
            "ollama_chat/gemma3:12b",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
            max_tokens=1024,
        )
        logger.info("Screenshot analyzed locally (Ollama)")
        return result, "ollama/gemma3:12b 🔒 local"
    except Exception as e:
        logger.warning("Local Ollama vision failed: %s — trying cloud", e)

    # Fall back to Groq Llama-4-Scout (supports vision)
    try:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        result = await acompletion(
            model="groq/meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS["vision"]},
                {"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]},
            ],
            api_key=api_key,
            max_tokens=1024,
        )
        logger.info("Screenshot analyzed via Groq cloud vision")
        return (result.choices[0].message.content or "").strip(), "groq/llama-4-scout"
    except Exception as e:
        raise RuntimeError(
            f"Screenshot analysis failed.\n"
            f"Local Ollama: gemma3:12b not found → run: ollama pull gemma3:12b\n"
            f"Cloud fallback also failed: {e}"
        )


# ── Shell execution ──────────────────────────────────────────────────────────

async def run_shell_command(cmd: str, timeout: int = 30) -> str:
    """Run a shell command on the PC. Returns stdout/stderr as string."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()
        if proc.returncode == 0:
            return out or "(done, no output)"
        return f"exit {proc.returncode}\n{err or out}"
    except asyncio.TimeoutError:
        return f"⏱ Timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def chunk_output(text: str, max_length: int = 4000) -> list[str]:
    """Split long text into Telegram-safe chunks."""
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
    keys = [
        "CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
        "OPENROUTER_API_KEY", "ZAI_API_KEY", "HF_TOKEN",
    ]
    return {k: bool(os.getenv(k)) for k in keys}
