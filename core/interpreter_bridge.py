"""Bridge between Telegram and Open Interpreter with multi-provider support."""

from __future__ import annotations
import asyncio
import logging
import os
import time
from typing import Optional
from interpreter import interpreter

logger = logging.getLogger(__name__)

# System prompts per agent
SYSTEM_PROMPTS = {
    "vision": (
        "You analyze screenshots, images, and visual interfaces on a Linux desktop (DISPLAY=:0). "
        "You can use computer.display.view() to take screenshots. "
        "Identify UI elements, read text via OCR, detect errors highlighted in red, "
        "and provide actionable next steps. When analyzing screens: "
        "1. Identify all visible elements. "
        "2. Read any text present. "
        "3. Detect errors or warnings. "
        "4. Suggest the next action."
    ),
    "coding": (
        "You are an expert software engineer with full computer control on a Linux desktop. "
        "You can: take screenshots with computer.display.view(), read VSCode files, "
        "execute shell commands, and click UI elements. "
        "When fixing code: 1. Screenshot to see the error. 2. Read the file. "
        "3. Analyze the issue. 4. Apply the minimal fix. 5. Run tests to verify. "
        "Always confirm before destructive actions (rm, git push --force, etc.)."
    ),
    "debug": (
        "You are a debugging expert for PyTorch/CUDA and Python systems. "
        "Analyze errors systematically: read the full traceback, identify root cause, "
        "explain WHY it failed in one sentence, then provide the minimal targeted fix. "
        "For CUDA OOM: enable AMP first (torch.cuda.amp), then reduce batch_size. "
        "For NaN loss: add gradient clipping (torch.nn.utils.clip_grad_norm_). "
        "Suggest a preventive assert or guard for the future."
    ),
    "math": (
        "You are a mathematics expert specializing in ML/deep learning math. "
        "Show step-by-step derivations. Verify numerical answers by writing and "
        "executing Python/NumPy code. For tensor operations, show shapes at each step. "
        "For gradient derivations, show the chain rule explicitly."
    ),
    "architect": (
        "You are a system architect. Design scalable, maintainable solutions. "
        "Focus on structure, data flow, and component boundaries. "
        "For ML systems: address data pipeline, training loop, evaluation, and deployment. "
        "For software systems: address APIs, storage, concurrency, and failure modes. "
        "Produce diagrams using ASCII art when helpful."
    ),
    "mentor": (
        "You are a patient teacher and expert explainer. "
        "Explain complex concepts using clear analogies and concrete examples. "
        "Always answer WHY, not just what. Structure explanations as: "
        "1. Simple intuition. 2. Technical detail. 3. Concrete example. "
        "4. One actionable takeaway. Adjust depth to the user's apparent level."
    ),
    "analyst": (
        "You are a data analyst specializing in ML training metrics and system performance. "
        "Extract insights from logs, metrics, and data. Identify trends and anomalies. "
        "Write Python code to produce visualizations (matplotlib/seaborn). "
        "For training runs: check loss curves, gradient norms, GPU utilization, and throughput. "
        "Alert on: NaN/Inf values, loss spikes > 2x, GPU utilization < 50%."
    ),
}

# Known context windows per model (tokens). Open Interpreter defaults to 8000 without this.
_CONTEXT_WINDOWS: dict[str, int] = {
    # ⭐ PRIORITY 1: YOUR FASTEST APIs FIRST (60+ req/min)
    "gemini/gemini-1.5-flash-latest":     1000000,  # ⭐ MOST GENEROUS
    "groq/llama3-8b-8192":                 8192,    # Lightning fast  
    "cerebras/llama-3.1-8b":               131072,  # High quality
    
    # PRIORITY 2: OpenRouter free tier
    "openrouter/qwen/qwen2.5:0.5b":        32768,
    "openrouter/meta-llama/llama-3.1-8b-instruct:free": 8192,
    
    # PRIORITY 3: Current models (fallback)
    "openrouter/qwen/qwen3-coder:free":    131072,
    "cerebras/qwen3-coder:free":           131072,
    "gemini/gemini-1.5-flash":            1000000,
    "groq/moonshotai/llama3-8b-8192":     200000,
    "zai/glm-4":                           128000,
    "openrouter/openai/gpt-oss-120b:free": 32768,
}

_MAX_TOKENS = 4096

# Rate limit tracking: {provider: last_rate_limit_time}
_RATE_LIMIT_TRACKER: dict[str, float] = {}
_RATE_LIMIT_COOLDOWN = 120  # seconds to wait before retrying rate-limited provider


def _get_provider_from_model(model: str) -> str:
    """Extract provider name from model string."""
    if "/" in model:
        return model.split("/")[0]
    return "unknown"


def _is_provider_rate_limited(provider: str) -> bool:
    """Check if provider was recently rate-limited."""
    if provider not in _RATE_LIMIT_TRACKER:
        return False
    elapsed = time.time() - _RATE_LIMIT_TRACKER[provider]
    return elapsed < _RATE_LIMIT_COOLDOWN


def mark_provider_rate_limited(model: str) -> None:
    """Mark a provider as rate-limited (call this from error handlers)."""
    provider = _get_provider_from_model(model)
    _RATE_LIMIT_TRACKER[provider] = time.time()
    logger.warning("Provider %s marked as rate-limited for %ds", provider, _RATE_LIMIT_COOLDOWN)


def configure_interpreter(model: str, agent_key: str) -> str:
    """Configure interpreter for the specified model and agent.
    
    Implements proactive rate limit avoidance by checking recent rate limit history.
    Falls back to Ollama if the requested provider was recently rate-limited.

    Args:
        model: Full LiteLLM model string with provider prefix (e.g. "cerebras/qwen3-coder:free")
        agent_key: Agent identifier for system prompt selection
        
    Returns:
        Actual model being used (may differ from requested if fallback occurred)
    """
    interpreter.auto_run = True
    interpreter.system_message = SYSTEM_PROMPTS.get(agent_key, "")
    
    original_model = model
    provider = _get_provider_from_model(model)
    
    # Proactive rate limit check - switch to Ollama if provider recently failed
    if _is_provider_rate_limited(provider):
        cooldown_remaining = _RATE_LIMIT_COOLDOWN - (time.time() - _RATE_LIMIT_TRACKER[provider])
        logger.warning(
            "Provider %s was recently rate-limited (%.0fs ago). "
            "Proactively falling back to Ollama to avoid delays.",
            provider, _RATE_LIMIT_COOLDOWN - cooldown_remaining
        )
        model = "ollama_chat/qwen3.5:35b"

    if model.startswith("ollama_chat/"):
        interpreter.llm.model = model
        interpreter.llm.api_base = "http://localhost:11434"
        interpreter.llm.api_key = "ollama"
        interpreter.llm.context_window = 8192
        interpreter.llm.max_tokens = _MAX_TOKENS
        interpreter.offline = True
        if model != original_model:
            logger.info("Using local Ollama (fallback from %s): %s", original_model, model)
        else:
            logger.info("Using local Ollama: %s", model)

    elif model.startswith("zai/"):
        # Z.AI uses a custom base URL not natively in LiteLLM — use openai/ prefix
        model_name = model.replace("zai/", "")
        interpreter.llm.model = f"openai/{model_name}"
        interpreter.llm.api_base = "https://open.bigmodel.cn/api/paas/v4"
        interpreter.llm.api_key = os.getenv("ZAI_API_KEY", "")
        interpreter.llm.context_window = _CONTEXT_WINDOWS.get(model, 128000)
        interpreter.llm.max_tokens = _MAX_TOKENS
        interpreter.offline = False
        logger.info("Using Z.AI: %s", model_name)

    elif model.startswith(("openrouter/", "cerebras/", "gemini/", "groq/")):
        # LiteLLM handles these providers natively via their prefix.
        # Do NOT strip the prefix and do NOT set api_base — LiteLLM picks the right URL.
        interpreter.llm.model = model
        interpreter.llm.api_base = None  # Let LiteLLM use its built-in provider URL
        interpreter.llm.context_window = _CONTEXT_WINDOWS.get(model, 32768)
        interpreter.llm.max_tokens = _MAX_TOKENS
        provider = model.split("/")[0]
        key_map = {
            "openrouter": "OPENROUTER_API_KEY",
            "cerebras":   "CEREBRAS_API_KEY",
            "gemini":     "GEMINI_API_KEY",
            "groq":       "GROQ_API_KEY",
        }
        env_var = key_map.get(provider, "")
        api_key = os.getenv(env_var, "")
        if not api_key:
            logger.warning(
                "No API key for provider '%s' — falling back to local Ollama", provider
            )
            interpreter.llm.model = "ollama_chat/qwen3.5:35b"
            interpreter.llm.api_base = "http://localhost:11434"
            interpreter.llm.api_key = "ollama"
            interpreter.llm.context_window = 8192
            interpreter.offline = True
            return "ollama_chat/qwen3.5:35b"
        # Set both the attribute AND the env var so LiteLLM picks it up as BYOK
        interpreter.llm.api_key = api_key
        if env_var:
            os.environ[env_var] = api_key
        interpreter.offline = False
        logger.info("Using %s: %s", provider, model)

    else:
        logger.warning("Unknown model prefix '%s' — falling back to local Ollama", model)
        interpreter.llm.model = "ollama_chat/qwen3.5:35b"
        interpreter.llm.api_base = "http://localhost:11434"
        interpreter.llm.api_key = "ollama"
        interpreter.llm.context_window = 8192
        interpreter.llm.max_tokens = _MAX_TOKENS
        interpreter.offline = True
        model = "ollama_chat/qwen3.5:35b"
        
    return model  # Return actual model being used

async def _raw_run(model: str, task: str, agent_key: str) -> str:
    """Execute interpreter.chat in thread pool and format output."""
    actual_model = configure_interpreter(model, agent_key)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: interpreter.chat(task, display=False),
    )

    output_parts = []
    for msg in result:
        if msg.get("type") == "message":
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                output_parts.append(content)
        elif msg.get("type") == "code":
            code = msg.get("content", "")
            if code.strip():
                output_parts.append(f"```\n{code}\n```")
        elif msg.get("type") == "console":
            console_out = msg.get("content", "")
            if console_out.strip():
                output_parts.append(f"Output: {console_out}")

    full_output = "\n\n".join(output_parts)
    return full_output if full_output else "Task completed (no output generated)"


async def run_task(model: str, task: str, agent_key: str = "coding") -> str:
    """Execute a task with caching, metrics, error recovery, and cost tracking.

    Pipeline:
      1. Check semantic cache → return hit immediately.
      2. Apply dynamic model routing (may downgrade to cheaper tier).
      3. Proactive rate limit check (may switch to Ollama preemptively).
      4. Run with circuit-breaker + multi-level fallback.
      5. Store result in cache, record metrics and usage cost.

    Args:
        model: Model string with provider prefix (e.g. "openrouter/...")
        task: User task description
        agent_key: Agent identifier for system prompt selection

    Returns:
        Concatenated output from interpreter
    """
    # --- 1. Semantic cache check ---
    cached_result: str | None = None
    try:
        from core.memory.semantic_cache import get_cache
        from core.observability.metrics import record_cache_event
        cache = get_cache()
        cached = cache.get(task, agent_key)
        if cached and cached != "__EVICTED__":
            record_cache_event(agent_key, hit=True)
            logger.debug("Cache hit for agent=%s", agent_key)
            return cached
        record_cache_event(agent_key, hit=False)
    except Exception as exc:
        logger.debug("Cache check skipped: %s", exc)

    # --- 2. Dynamic model routing ---
    effective_model = model
    try:
        from core.reliability.model_router import select_model
        effective_model = select_model(agent_key, task) or model
    except Exception as exc:
        logger.debug("Model router skipped: %s", exc)

    # --- 3. Error recovery wrapper ---
    async def _run_fn(t: str) -> str:
        return await _raw_run(effective_model, t, agent_key)

    result: str
    try:
        from core.reliability.error_recovery import get_recovery
        from core.observability.metrics import trace_agent
        async with trace_agent(agent_key):
            result = await get_recovery().execute(task, agent_key, _run_fn)
    except Exception as exc:
        logger.warning("Error recovery pipeline failed, running directly: %s", exc)
        result = await _raw_run(effective_model, task, agent_key)

    # --- 4. Store in cache and record usage ---
    try:
        from core.memory.semantic_cache import get_cache
        get_cache().set(task, agent_key, result)
    except Exception:
        pass

    try:
        from core.optimization.usage_tracker import get_tracker
        # Token counts are not available from OI; use rough estimate
        estimated_in = len(task.split()) * 1_000 // 750
        estimated_out = len(result.split()) * 1_000 // 750
        alert = get_tracker().record(effective_model, estimated_in, estimated_out)
        if alert:
            logger.warning("Usage alert: %s", alert)
    except Exception:
        pass

    return result

def chunk_output(text: str, max_length: int = 4000) -> list[str]:
    """Split text into chunks safe for Telegram's message length limit.
    
    Args:
        text: Full output text
        max_length: Maximum characters per chunk (default 4000 for safety)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
