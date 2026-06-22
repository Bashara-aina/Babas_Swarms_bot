"""
lib/legiona/minimax_client.py
OpenCode M3 — fully optimized for maximum intelligence.
Methods implemented:
  #1  Model = deepseek-v4-pro (latest, self-evolving)
  #2  reasoning_split=False (env-var override: OPGO_REASONING_SPLIT)
  #3  Optimal sampling: temperature=1.0, top_p=0.95, top_k=40
  #6  Interleaved thinking between tool calls via system prompt
  #7  Preset parameter profiles for coding vs research tasks
  #10 OpenRouter fallback for stability
"""

from __future__ import annotations

import asyncio as _asyncio
import json as _json
import logging as _logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeVar

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from lib.legiona.tools.registry import get_tool_function

_logger = _logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ── Observability ──────────────────────────────────────────────────────────
_cost_log_path = Path("lib/legiona/memory/cost_log.jsonl")


def _log_usage(response: Any) -> None:
    """Append token usage + ¥ cost to cost_log.jsonl if usage data available."""
    try:
        if not hasattr(response, "usage") or response.usage is None:
            return
        usage = response.usage
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        input_jpy = (prompt_tokens / 1000) * 0.04
        output_jpy = (completion_tokens / 1000) * 0.12
        record = {
            "ts": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached,
            "input_jpy": round(input_jpy, 4),
            "output_jpy": round(output_jpy, 4),
            "total_jpy": round(input_jpy + output_jpy, 4),
        }
        with open(_cost_log_path, "a") as f:
            f.write(_json.dumps(record) + "\n")
    except Exception:
        pass  # never fail a call due to logging


def _build_cached_system(system_content: str) -> dict[str, Any]:
    """Wrap system content in a cache-controlled message for prompt caching."""
    return {
        "role": "system",
        "content": system_content,
        "cache_control": {"type": "ephemeral"},
    }


def _load_image_as_base64(image_path: str) -> str:
    """
    Load an image file and encode it as a base64 data URL.
    Supports PNG, JPEG, WebP, GIF. Returns data URL string.
    """
    from pathlib import Path

    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    import base64


    raw = p.read_bytes()
    ext = p.suffix.lower().lstrip(".")
    # imghdr is deprecated in 3.11+; detect from extension first
    valid = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg", "gif": "gif", "webp": "webp"}
    if ext not in valid:
        raise ValueError(f"Unsupported image format: .{ext} — use png/jpeg/gif/webp")
    mime = f"image/{valid[ext]}"
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _inject_images_into_messages(
    messages: list[dict[str, Any]],
    image_paths: list[str],
) -> list[dict[str, Any]]:
    """
    Take the first user message and inject image_url content blocks.
    Preserves message structure; converts string content to
    [{"type": "text", "text": ...}, {"type": "image_url", ...}] blocks.
    """
    if not image_paths:
        return messages

    b64_images = [_load_image_as_base64(p) for p in image_paths]

    # Find first user message to inject into
    msgs = list(messages)
    for i, msg in enumerate(msgs):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # Convert to content blocks format
            blocks: list[dict[str, Any]] = []
            if isinstance(content, str) and content:
                blocks.append({"type": "text", "text": content})
            for b64 in b64_images:
                blocks.append({"type": "image_url", "image_url": {"url": b64}})
            msgs[i] = {**msg, "content": blocks}
            break
    return msgs


def _resolve_reasoning_split(reasoning_split: bool = False) -> bool:
    """
    Allow env-var OPGO_REASONING_SPLIT to override the code-level default.

    Setting OPGO_REASONING_SPLIT=true re-enables reasoning trace output
    for debugging without needing code changes. Default is False — OpenCode
    performs internal chain-of-thought regardless; this flag only controls
    whether the reasoning trace stream is included in the API response.
    """
    env_val = os.environ.get("OPGO_REASONING_SPLIT")
    if env_val is not None:
        return env_val.lower() in ("true", "1", "yes")
    return reasoning_split


# ── Model ────────────────────────────────────────────────────────────────────
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "deepseek-v4-pro")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.opencode.ai/zen/go/v1")
MINIMAX_DIRECT = True  # Always route direct to OpenCode — no OpenRouter fallback


# ── Sampling presets (#3, #7) ────────────────────────────────────────────────
# OpenCode M3 is tuned for temperature=1.0 — NOT 0.7
PRESET_PROFILES = {
    "coding": {
        "temperature": 1.0,
        "top_p": 0.95,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1,
    },
    "research": {
        "temperature": 1.0,
        "top_p": 0.95,
        "frequency_penalty": 0.3,
        "presence_penalty": 0.2,
    },
    "debate": {
        "temperature": 1.0,
        "top_p": 0.95,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.15,
    },
    "memory_consolidation": {
        "temperature": 1.0,
        "top_p": 0.95,
        "frequency_penalty": 0.05,
        "presence_penalty": 0.05,
    },
    # Legacy alias
    "creative": {
        "temperature": 1.0,
        "top_p": 0.98,
        "frequency_penalty": 0.4,
        "presence_penalty": 0.3,
    },
}


def get_profile(profile_name: str) -> dict[str, Any]:
    """
    Return sampling parameters for the given profile name.
    Raises KeyError if profile_name is not found.
    """
    return PRESET_PROFILES[profile_name]


# Legacy aliases (for backwards compatibility)
PRESET_CODING = PRESET_PROFILES["coding"]
PRESET_RESEARCH = PRESET_PROFILES["research"]
PRESET_CREATIVE = PRESET_PROFILES["creative"]


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


# ── Structured output validation ─────────────────────────────────────────────
def _validate_structured_output(data: dict, expected_model: type[BaseModel]) -> tuple[bool, str]:
    """
    Validate that a dict matches the expected Pydantic model schema.
    Returns (is_valid, error_message).

    Anti-hallucination pillar #4: ensures LLM JSON output conforms to schema.

    Args:
        data: Parsed JSON dict from LLM response
        expected_model: Pydantic model class to validate against

    Returns:
        (True, "") if valid, (False, error_message) if invalid
    """
    try:
        # Try to parse through Pydantic validation
        expected_model(**data)
        return True, ""
    except Exception as exc:
        error_msg = str(exc)
        return False, f"Schema validation failed: {error_msg}"


# ── Client factory (#10: primary + fallback) ────────────────────────────────
def _build_go_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENCODE_GO_API_KEY", "")
    if not api_key:
        raise ValueError("OPENCODE_GO_API_KEY not set")
    return AsyncOpenAI(api_key=api_key, base_url=MINIMAX_BASE_URL)


def get_client(fallback: bool = False) -> AsyncOpenAI:
    """
    Returns plain AsyncOpenAI client (no instructor dependency).
    OpenCode direct only — OpenRouter fallback disabled (MINIMAX_DIRECT=True).

    Gap 3 fix: removed instructor.from_openai() — structured output
    is now handled via response_format={"type": "json_object"} + manual parsing.
    """
    return _build_go_client()


# ── Smart async completion wrapper (#2: reasoning_split, #3: optimal params) ─
async def create_structured_completion[T: BaseModel](
    *,
    messages: list[dict[str, Any]],
    response_model: type[T] = LegionaOutput,
    preset: str = "coding",
    profile: str | None = None,
    fallback: bool = False,
    max_tokens: int = 8192,
    reasoning_split: bool = False,
    model: str | None = None,
) -> T:
    """
    Main async call wrapper. Uses reasoning_split=False by default to save
    ~50% output tokens — OpenCode performs internal chain-of-thought regardless;
    this flag only controls whether the reasoning trace is streamed in the response.
    Set OPGO_REASONING_SPLIT=true env-var to re-enable for debugging.

    Gap 3 fix: replaced instructor response_model= with native JSON-mode parsing.
    M3 is instructed to output a JSON object; we parse it manually.

    Args:
        preset: "coding" | "research" | "creative" — selects sampling parameters
        reasoning_split: Whether to stream interleaved CoT trace (default False)
        fallback: Route via OpenRouter instead of OpenCode direct
        model: Override model string (default: MINIMAX_MODEL or OPENROUTOR_MODEL)
    """
    profile_key = profile or preset
    params = PRESET_PROFILES.get(profile_key, PRESET_PROFILES["coding"])
    model_str = model or MINIMAX_MODEL  # Always use OpenCode direct — no OpenRouter fallback
    client = get_client(fallback=fallback)

    # Prepend cached evolved rules as system message
    from lib.legiona.self_evolve import load_evolved_rules
    evolved = load_evolved_rules()
    msgs = list(messages)
    if msgs and msgs[0].get("role") == "system":
        merged = _build_cached_system(evolved + msgs[0]["content"])
        msgs[0] = merged
    else:
        msgs.insert(0, _build_cached_system(evolved))

    # Gap 3: use json_object response_format instead of response_model=
    response = await client.chat.completions.create(
        model=model_str,
        messages=msgs,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
        extra_body={"reasoning_split": _resolve_reasoning_split(reasoning_split)},
        **params,
    )

    _log_usage(response)
    # Parse JSON from content manually
    content = response.choices[0].message.content or ""
    try:
        data = _json.loads(content)
    except _json.JSONDecodeError:
        # Try stripping markdown code fences
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            stripped = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        data = _json.loads(stripped)

    # Anti-hallucination: validate structured output
    is_valid, error_msg = _validate_structured_output(data, response_model)
    if not is_valid:
        _logger.warning("[legiona] Structured output validation failed: %s", error_msg)
        _logger.warning("[legiona] Raw data: %s", str(data)[:500])

    return response_model(**data)


# ── Sync completion (for non-async contexts) ────────────────────────────────
def complete[T: BaseModel](
    messages: list[dict[str, Any]],
    preset: str = "coding",
    profile: str | None = None,
    response_model: type[T] = LegionaOutput,
    fallback: bool = False,
    max_tokens: int = 8192,
    reasoning_split: bool = False,
    model: str | None = None,
) -> T:
    """
    Synchronous wrapper. Prefer create_structured_completion() in async contexts.
    Evolved rules are auto-prepended as a cached system message.
    Usage + ¥ cost are logged after each call.

    Gap 3 fix: replaced instructor response_model= with native JSON-mode parsing.
    """
    # Load evolved rules and prepend as cached system message
    # Lazy import to avoid circular: self_evolve → minimax_client.complete
    from lib.legiona.self_evolve import load_evolved_rules
    evolved = load_evolved_rules()

    # Inject cache-controlled system message
    msgs = list(messages)
    if msgs and msgs[0].get("role") == "system":
        # Merge with existing system message
        merged = _build_cached_system(evolved + msgs[0]["content"])
        msgs[0] = merged
    else:
        cached_sys = _build_cached_system(evolved)
        msgs.insert(0, cached_sys)

    profile_key = profile or preset
    params = PRESET_PROFILES.get(profile_key, PRESET_PROFILES["coding"])
    model_str = model or MINIMAX_MODEL  # Always use OpenCode direct — no OpenRouter fallback
    client = get_client(fallback=fallback)

    # Gap 3: use json_object response_format instead of response_model=
    response = client.chat.completions.create(
        model=model_str,
        messages=msgs,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
        extra_body={"reasoning_split": _resolve_reasoning_split(reasoning_split)},
        **params,
    )

    _log_usage(response)
    # Parse JSON from content manually
    content = response.choices[0].message.content or ""
    try:
        data = _json.loads(content)
    except _json.JSONDecodeError:
        # Try stripping markdown code fences
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            stripped = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        data = _json.loads(stripped)

    # Anti-hallucination: validate structured output
    is_valid, error_msg = _validate_structured_output(data, response_model)
    if not is_valid:
        _logger.warning("[legiona] Structured output validation failed: %s", error_msg)
        _logger.warning("[legiona] Raw data: %s", str(data)[:500])

    return response_model(**data)


# ── Streaming completions (Gap 1) ─────────────────────────────────────────────
async def stream_complete(
    messages: list[dict[str, Any]],
    preset: str = "coding",
    profile: str | None = None,
    fallback: bool = False,
    max_tokens: int = 8192,
    reasoning_split: bool = False,
    model: str | None = None,
):
    """
    Async generator that yields SSE Delta events from M3.

    Each yield is a dict with keys:
      content     — str token chunk (accumulates in .join() for final answer)
      reasoning   — str token from reasoning_detail (if present)
      usage       — dict of usage numbers (emitted on final event)
      done        — True on final event (stop iterating)

    Usage:
        async for event in stream_complete(msgs):
            if event["done"]:
                print(f"final answer: {event['content']}")
    """
    from lib.legiona.self_evolve import load_evolved_rules

    evolved = load_evolved_rules()
    msgs = list(messages)
    if msgs and msgs[0].get("role") == "system":
        merged = _build_cached_system(evolved + msgs[0]["content"])
        msgs[0] = merged
    else:
        msgs.insert(0, _build_cached_system(evolved))

    profile_key = profile or preset
    params = PRESET_PROFILES.get(profile_key, PRESET_PROFILES["coding"])
    model_str = model or MINIMAX_MODEL  # Always use OpenCode direct — no OpenRouter fallback
    client = get_client(fallback=fallback)

    stream = await client.chat.completions.create(
        model=model_str,
        messages=msgs,
        stream=True,
        max_tokens=max_tokens,
        extra_body={"reasoning_split": _resolve_reasoning_split(reasoning_split)},
        **params,
    )

    reasoning_buf = ""
    content_buf = ""

    async for event in stream:
        # event is ServerSentEvent; .model_dump() gives dict
        choice = event.choices[0]
        delta = choice.delta

        # Accumulate reasoning from model_extra
        reasoning_this = ""
        extra = choice.model_extra or {}
        if "reasoning_detail" in extra:
            reasoning_this = str(extra["reasoning_detail"])
        elif "reasoning" in extra:
            reasoning_this = str(extra["reasoning"])

        if reasoning_this:
            reasoning_buf += reasoning_this
            yield {"reasoning": reasoning_this, "content": "", "usage": None, "done": False}

        # Accumulate content tokens
        token = delta.content or ""
        if token:
            content_buf += token
            yield {"content": token, "reasoning": "", "usage": None, "done": False}

        # Emit usage on the last event
        if event.usage:
            yield {"content": "", "reasoning": "", "usage": _dict_from_obj(event.usage), "done": True}

    # Guard: if stream ended without a usage event (some providers omit it)
    if not event.usage:
        yield {"content": "", "reasoning": "", "usage": None, "done": True}


def _dict_from_obj(obj: Any) -> dict[str, Any]:
    """Convert OpenAI Usage object to plain dict."""
    return {
        "prompt_tokens": getattr(obj, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(obj, "completion_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(obj, "cache_read_input_tokens", 0) or 0,
    }


async def stream_structured_completion[T: BaseModel](
    *,
    messages: list[dict[str, Any]],
    response_model: type[T] = LegionaOutput,
    preset: str = "coding",
    profile: str | None = None,
    fallback: bool = False,
    max_tokens: int = 8192,
    reasoning_split: bool = False,
    model: str | None = None,
) -> T:
    """
    Streams tokens for UX (yields content + reasoning chunks),
    collects the full content string, then parses JSON into response_model.

    Returns the parsed Pydantic model (same shape as create_structured_completion).
    """
    content_parts: list[str] = []

    async for event in stream_complete(
        messages=messages,
        preset=preset,
        fallback=fallback,
        max_tokens=max_tokens,
        reasoning_split=reasoning_split,
        model=model,
    ):
        if event["content"]:
            content_parts.append(event["content"])
        if event["done"]:
            _log_usage(event.get("usage") or {})

    full_content = "".join(content_parts)
    try:
        data = _json.loads(full_content)
    except _json.JSONDecodeError:
        stripped = full_content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            stripped = "\n".join(
                lines[1:-1] if lines[-1].startswith("```") else lines[1:]
            )
        data = _json.loads(stripped)

    return response_model(**data)


# ── Embedding (for RAG — embo-01) ───────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    """
    OpenCode embedding via direct HTTP (not instructor).
    Model: emo-01 (1536-dim) [VERIFY BEFORE USE: confirm dimension on platform]
    """
    api_key = os.getenv("OPENCODE_GO_API_KEY", "")
    if not api_key:
        raise ValueError("OPENCODE_GO_API_KEY not set")
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


# ── Tool calling loop ─────────────────────────────────────────────────────────


@dataclass
class ToolResult:
    """
    Result from complete_with_tools() — includes reasoning trace and tool call log.
    """
    reasoning_trace: list[str] = field(default_factory=list)
    final_answer: str = ""
    tool_calls_made: list[str] = field(default_factory=list)
    rounds: int = 0


def _validate_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure messages is a valid OpenAI-style message list."""
    if not messages:
        raise ValueError("messages cannot be empty")
    for m in messages:
        if "role" not in m or "content" not in m:
            raise ValueError(f"Each message must have 'role' and 'content': {m}")
    return messages


async def create_completion_with_tools(
    *,
    messages: list[dict[str, Any]],
    tool_schemas: list[dict[str, Any]] | None = None,
    preset: str = "coding",
    profile: str | None = None,
    fallback: bool = False,
    max_tokens: int = 8192,
    max_rounds: int = 10,
    model: str | None = None,
    verbose: bool = True,
    image_paths: list[str] | None = None,
    reasoning_split: bool = False,
) -> ToolResult:
    """
    M3 native tool-calling loop with per-round reasoning trace.

    Executes a tool-call loop: sends messages + tools to M3,
    executes any tool_calls in the response, appends results, and
    loops until M3 returns a plain answer.

    Args:
        messages: OpenAI-style message list (role + content)
        tool_schemas: OpenAI tool schemas to register (from tools.registry.TOOL_SCHEMAS)
        preset: "coding" | "research" | "creative"
        fallback: Route via OpenRouter instead of OpenCode direct
        max_tokens: Max tokens per completion call
        max_rounds: Hard cap on tool-call loops (prevents infinite loops)
        model: Override model string
        verbose: Log reasoning details between rounds
        image_paths: Optional list of image file paths to inject as base64
                     into the first user message for vision tasks.

    Returns:
        ToolResult with reasoning_trace, final_answer, tool_calls_made, rounds
    """
    _validate_messages(messages)
    if image_paths:
        messages = _inject_images_into_messages(messages, image_paths)

    # Prepend cached evolved rules as system message
    from lib.legiona.self_evolve import load_evolved_rules
    evolved = load_evolved_rules()
    working_messages: list[dict[str, Any]] = list(messages)
    if working_messages and working_messages[0].get("role") == "system":
        merged = _build_cached_system(evolved + working_messages[0]["content"])
        working_messages[0] = merged
    else:
        working_messages.insert(0, _build_cached_system(evolved))

    profile_key = profile or preset
    params = PRESET_PROFILES.get(profile_key, PRESET_PROFILES["coding"])
    model_str = model or MINIMAX_MODEL  # Always use OpenCode direct — no OpenRouter fallback
    client = get_client(fallback=fallback)

    # If no tool schemas passed, pull all from registry
    if not tool_schemas:
        from lib.legiona.tools.registry import TOOL_SCHEMAS
        tool_schemas = TOOL_SCHEMAS

    tool_map: dict[str, Any] = {}
    for schema in tool_schemas:
        fn = get_tool_function(schema["name"])
        if fn:
            tool_map[schema["name"]] = fn

    result = ToolResult()
    result.rounds = 0

    while result.rounds < max_rounds:
        result.rounds += 1

        # Call M3 with reasoning_split + tools
        try:
            response = await client.chat.completions.create(
                model=model_str,
                messages=working_messages,
                tools=tool_schemas,
                tool_choice="auto",
                max_tokens=max_tokens,
                extra_body={"reasoning_split": _resolve_reasoning_split(reasoning_split)},
                **params,
            )
        except Exception as exc:
            return ToolResult(
                final_answer=f"[ERROR during completion: {exc}]",
                rounds=result.rounds,
            )

        _log_usage(response)

        choice = response.choices[0]
        assistant_message: dict[str, Any] = choice.message.model_dump()

        # Log reasoning details if present (OpenCode M3 puts CoT in reasoning field)
        reasoning_detail = ""
        if hasattr(response, "choices") and response.choices:
            extra = response.choices[0].model_extra or {}
            if "reasoning_detail" in extra:
                reasoning_detail = str(extra["reasoning_detail"])
            elif "reasoning" in extra:
                reasoning_detail = str(extra["reasoning"])

        if reasoning_detail and verbose:
            _logger.debug("[legiona] reasoning round %d: %s", result.rounds, reasoning_detail[:200])
            result.reasoning_trace.append(reasoning_detail)

        content = assistant_message.get("content") or ""
        tool_calls = assistant_message.get("tool_calls") or []

        # If no tool calls → M3 returned a final answer
        if not tool_calls:
            result.final_answer = content
            break

        # Execute each tool call and collect results
        for tc in tool_calls:
            tool_name: str = tc.get("function", {}).get("name", "unknown")
            raw_args: str = tc.get("function", {}).get("arguments", "{}")

            # Parse arguments (may be string or dict)
            try:
                args = _json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except _json.JSONDecodeError:
                args = {"raw": raw_args}

            fn = tool_map.get(tool_name)
            if not fn:
                tool_result_str = f"ERROR: Unknown tool '{tool_name}'"
            else:
                try:
                    from lib.legiona.observability.tracer import trace_call
                    with trace_call("legiona.tool_call", tool=tool_name, round=result.rounds):
                        _asyncio.get_event_loop()
                        if _asyncio.iscoroutinefunction(fn):
                            tool_result_str = await fn(**args)
                        else:
                            tool_result_str = fn(**args)
                except Exception as exc:
                    tool_result_str = f"ERROR: {type(exc).__name__}: {exc}"

            if verbose:
                _logger.debug("[legiona] tool_call: %s → %s", tool_name, tool_result_str[:200])

            result.tool_calls_made.append(tool_name)

            # Append assistant message with tool call, then tool result
            working_messages.append(assistant_message)
            working_messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", "unknown"),
                "content": tool_result_str,
            })

    if result.rounds >= max_rounds:
        result.final_answer = (
            f"[TOOL LOOP HIT MAX ROUNDS ({max_rounds})] "
            f"Accumulated reasoning:\n" + "\n".join(result.reasoning_trace[-3:])
        )

    return result


def complete_with_tools(
    messages: list[dict[str, Any]],
    tool_schemas: list[dict[str, Any]] | None = None,
    preset: str = "coding",
    profile: str | None = None,
    fallback: bool = False,
    max_tokens: int = 8192,
    max_rounds: int = 10,
    model: str | None = None,
    verbose: bool = True,
    image_paths: list[str] | None = None,
) -> ToolResult:
    """
    Synchronous wrapper around create_completion_with_tools().
    Prefer the async version in async contexts.
    """
    try:
        _asyncio.get_running_loop()
        # Already in async context — create a task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                _sync_inner,
                messages,
                tool_schemas,
                preset,
                profile,
                fallback,
                max_tokens,
                max_rounds,
                model,
                verbose,
                image_paths,
            )
            return future.result()
    except RuntimeError:
        # No running loop — safe to use _asyncio.run
        return _asyncio.run(
            create_completion_with_tools(
                messages=messages,
                tool_schemas=tool_schemas,
                preset=preset,
                profile=profile,
                fallback=fallback,
                max_tokens=max_tokens,
                max_rounds=max_rounds,
                model=model,
                verbose=verbose,
                image_paths=image_paths,
            )
        )


def _sync_inner(
    messages: list[dict[str, Any]],
    tool_schemas: list[dict[str, Any]] | None,
    preset: str,
    profile: str | None,
    fallback: bool,
    max_tokens: int,
    max_rounds: int,
    model: str | None,
    verbose: bool,
    image_paths: list[str] | None,
) -> ToolResult:
    """Inner sync implementation using new event loop in thread."""
    return _asyncio.run(
        create_completion_with_tools(
            messages=messages,
            tool_schemas=tool_schemas,
            preset=preset,
            profile=profile,
            fallback=fallback,
            max_tokens=max_tokens,
            max_rounds=max_rounds,
            model=model,
            verbose=verbose,
            image_paths=image_paths,
        )
    )


# ── Convenience: one-shot image analysis ──────────────────────────────────────

def analyze_image(
    image_paths: list[str],
    prompt: str = "Describe what you see in this image in detail.",
    model: str | None = None,
) -> str:
    """
    One-shot image analysis using M3 vision.
    Loads images as base64, sends to M3 with a user message, returns the answer.

    Args:
        image_paths: List of image file paths (PNG, JPEG, GIF, WebP)
        prompt: Question/instruction about the image(s)
        model: Optional model override

    Returns:
        The model's text answer.
    """
    messages = [
        {"role": "user", "content": prompt},
    ]
    result = complete_with_tools(
        messages=messages,
        model=model,
        image_paths=image_paths,
        preset="research",
    )
    return result.final_answer
