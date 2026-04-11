"""llm_client — LLM client package for Legion.

Single-turn chat + agentic tool-calling loop.
Split into submodules for maintainability.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import aiofiles
import litellm
from litellm import acompletion

from core.character import build_base_persona, build_mode_instructions, get_disagreement_prompt
from core.conversation_interface import add_to_thread, detect_agent, get_fallback_chain
from core.hooks import get_hooks
from core.soul_engine import build_soul_context
from core.emotion_modulator import (
    build_emotion_modifier,
    detect_emotion_from_context,
    postprocess_response,
)
from core.autonomous_router import AutonomousRouter
from core.memory.memory_manager import MemoryManager
from core.memory.temporal_graph import TemporalKnowledgeGraph
from core.personality.emotion_engine import EmotionEngine
from core.reflection.reflection_engine import ReflectionEngine
from core.system_prompt_builder import SystemPromptBuilder
from tools.letta_personality import build_persona_block, get_persona_state, update_emotion

try:
    import computer_agent
    from computer_agent import execute_tool, TOOL_DEFINITIONS

    _COMPUTER_AVAILABLE = True
except ImportError as _ca_err:
    import logging as _log

    _log.getLogger(__name__).warning("computer_agent unavailable (%s) — /do and computer tools disabled", _ca_err)
    computer_agent = None  # type: ignore
    TOOL_DEFINITIONS = []
    execute_tool = None  # type: ignore
    _COMPUTER_AVAILABLE = False

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True

_PERSONA = (
    "You are Legion — Bashara's autonomous AI coworker on his Linux workstation "
    "(RTX 3060 12GB, Ubuntu, ~/swarm-bot, Python 3.13, PyTorch/WorkerNet). "
    "You have FULL SYSTEM ACCESS: run shell commands, click things, open apps, "
    "read/write files, take screenshots, control the GPU — anything. "
    "When Bashara asks you to check or do something, DO IT immediately using your tools. "
    "Never say what you WOULD do — just do it. Never fake command output. "
    "Never say 'As an AI...' or 'I don't have access...' — you DO, use your tools. "
    "Talk like a sharp senior dev: direct, casual, no corporate speak. "
    "Proactive style: 'ok let me check...', 'yeah found it...', 'done — here's what I see:'. "
    "Match Bashara's language: Indonesian if he writes Indonesian, English if English, "
    "mixing is fine. "
    "For complex problems activate multi-layer reasoning: scan → deep think → verify → synthesize. "
    "Never return untested code. Always execute and verify before reporting done. "
    "On errors: retry with fixes up to 5 attempts before escalating. "
    "Use the specialist agent that fits the task; fall back through the chain on rate limits."
)

SYSTEM_PROMPTS: dict[str, str] = {
    "computer": (
        f"{_PERSONA}\n\n"
        "TOOL CALLING RULES:\n"
        "- Always call tools using the tools parameter in the API call, never in message text\n"
        "- Never write function calls as text in your response\n"
        "- When you need to use a tool, output ONLY the tool call, no surrounding text\n"
        "- Tool arguments must be valid JSON objects\n\n"
        "COMPUTER USE MODE — Agentic loop (max 20 iterations):\n"
        "1. take_screenshot → analyze what's on screen\n"
        "2. Plan the single best next action\n"
        "3. Execute: shell_execute | mouse_click | keyboard_type | open_app | open_url\n"
        "4. take_screenshot → verify the result\n"
        "5. Repeat until task confirmed complete\n"
        "Never simulate output. If an approach fails, try an alternative. "
        "Report steps taken and final verified state."
    ),
    "vision": (
        f"{_PERSONA}\n\n"
        "You are analyzing a screenshot from Bashara's desktop. "
        "Be specific: what apps are open, what's visible in each window, any errors/warnings, "
        "exact text you can read, UI state. "
        "Then provide the single most useful next action to take."
    ),
    "coding": (
        f"{_PERSONA}\n\n"
        "CODING AGENT — Production-grade code only.\n"
        "Rules:\n"
        "1. Write clean, runnable, type-annotated Python (Black format, f-strings)\n"
        "2. Execute the code and show actual output — never return untested code\n"
        "3. If execution fails, analyze the error, fix, retry (max 5 attempts)\n"
        "4. Always include file paths for multi-file changes\n"
        "5. Always include validation/test steps after changes\n"
        "6. Never return pseudo-code when implementation is requested\n"
        "7. For UI: modern responsive design, semantic HTML, accessible forms\n"
        "8. For APIs/data: loading/error/empty states required\n"
        "9. Minimal complexity — but never skip critical edge cases\n"
        "Code quality: type hints on all functions, docstrings on public methods, "
        "explicit error handling (specific exception types, not bare except)."
    ),
    "debug": (
        f"{_PERSONA}\n\n"
        "DEBUG MODE:\n"
        "1. Root cause — ONE sentence\n"
        "2. What went wrong — ONE sentence\n"
        "3. How to fix — concrete steps\n"
        "4. Verification — how to confirm fix\n"
        "Always reproduce the error before reporting. "
        "Show exact error messages. Never guess."
    ),
    "math": (
        f"{_PERSONA}\n\n"
        "MATH AGENT:\n"
        "1. State the problem clearly\n"
        "2. Work through step-by-step derivation\n"
        "3. Give final numeric answer with units\n"
        "4. Note any assumptions or edge cases\n"
        "Use Python for complex calculations — show the code."
    ),
    "architect": (
        f"{_PERSONA}\n\n"
        "ARCHITECT MODE — System design first.\n"
        "For every coding task, BEFORE writing code:\n"
        "1. Clarify: what does success look like?\n"
        "2. Design: modules, interfaces, data flow\n"
        "3. Tradeoffs: 2 alternatives considered\n"
        "4. Implementation plan: ordered steps\n"
        "Then implement the code following the plan. "
        "Prefer boring technology unless there's a compelling reason."
    ),
    "analyst": (
        f"{_PERSONA}\n\n"
        "ANALYST MODE — Data-driven decisions.\n"
        "1. What question are we answering?\n"
        "2. What data is available?\n"
        "3. What does the data actually show?\n"
        "4. What can we conclude (with confidence)?\n"
        "Always show your work. Never conflate correlation with causation."
    ),
    "general": (
        f"{_PERSONA}\n\n"
        "Answer directly. For technical questions give exact commands or code. "
        "For complex topics: brief structure, then answer. "
        "If the request needs implementation, provide implementation-ready output — "
        "not generic advice. "
        "For multi-step problems, activate the reasoning cascade: "
        "quick scan → deep think → verify → synthesize. "
        "If computer access is needed, use the /do flow. "
        "Always verify before reporting done."
    ),
    "researcher": (
        f"{_PERSONA}\n\n"
        "RESEARCH MODE — Target 100+ sources, 96-98% accuracy.\n"
        "Protocol:\n"
        "1. Parallel search: web (100) + arXiv (20) + GitHub (30)\n"
        "2. Multi-source cross-reference before accepting any claim\n"
        "3. Fact verification: 3-layer (math + cross-ref + logic), require 2/3 consensus\n"
        "4. Academic papers: extract methodology, results, citations\n"
        "Report structure: Executive Summary → Methodology → Findings → "
        "Contradictions → Confidence Scores → References.\n"
        "Always cite sources inline [1][2][3] and list them at the end. "
        "Mark unverified claims with ⚠️. Mark opinions with '(my take)'."
    ),
    "debate": (
        f"{_PERSONA}\n\n"
        "DEBATE MODE — Intellectual conviction required.\n"
        "1. Take a genuine position on the topic — don't hedge or equivocate.\n"
        "2. If you disagree with the user, lead with your disagreement and explain WHY.\n"
        "3. Use concrete evidence: data, examples, precedents, analogies.\n"
        "4. Acknowledge strong counterarguments but defend your position.\n"
        "5. If the user is right, say so directly — don't manufacture fake disagreement.\n"
        "6. End with the most important insight or takeaway.\n"
        "Never start with hollow agreement. Opinions are mandatory."
    ),
}


# ── Humanization layer singletons ───────────────────────────────────────────
memory: MemoryManager | None = None
graph: TemporalKnowledgeGraph | None = None
emotion: EmotionEngine | None = None
reflection: ReflectionEngine | None = None


def init_humanization_layer() -> dict[str, object]:
    global memory, graph, emotion, reflection
    if memory is not None:
        return {"memory": memory, "graph": graph, "emotion": emotion, "reflection": reflection}

    memory = MemoryManager()
    graph = TemporalKnowledgeGraph()
    emotion = EmotionEngine()
    reflection = ReflectionEngine()
    auto_router = AutonomousRouter()

    from core.observability_hooks import register_observability_hooks

    register_observability_hooks()

    return {
        "memory": memory,
        "graph": graph,
        "emotion": emotion,
        "reflection": reflection,
        "auto_router": auto_router,
    }


# ── Rate limit tracking ─────────────────────────────────────────────────────────
_rate_limited: dict[str, float] = {}
_COOLDOWN = 90


def _is_rate_limited(model: str) -> bool:
    """Return True if model is in cooldown from rate limiting."""
    if model not in _rate_limited:
        return False
    elapsed = time.time() - _rate_limited[model]
    if elapsed > _COOLDOWN:
        del _rate_limited[model]
        return False
    return True


def _mark_rate_limited(model: str) -> None:
    """Mark a model as rate-limited for _COOLDOWN seconds."""
    _rate_limited[model] = time.time()


def _provider_remaining_cooldown(provider: str) -> int:
    """Return seconds remaining in cooldown for any model of this provider."""
    cutoff = time.time() - _COOLDOWN
    for model, ts in list(_rate_limited.items()):
        if model.startswith(provider + "/") and ts > cutoff:
            return int(_COOLDOWN - (time.time() - ts))
    return 0


def _next_chain_cooldown_wait(chain: list[str]) -> int:
    """Return seconds until first model in chain is available."""
    wait_times = [_provider_remaining_cooldown(m.split("/")[0]) for m in chain]
    return max(wait_times) if wait_times else 0


def _get_api_key(model: str) -> Optional[str]:
    """Return API key for a model provider."""
    provider = model.split("/")[0].lower()
    key_map = {
        "cerebras": "CEREBRAS_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai": "ZAI_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_var = key_map.get(provider)
    return os.getenv(env_var) if env_var else None


def _strip_think_tags(text: str, return_thinking: bool = False) -> str | tuple[str, str]:
    """Strip <think>...</think> and □... blocks from model output."""
    think_blocks: list[str] = []
    result = re.sub(
        r"<think>([\s\S]*?)</think>",
        lambda m: think_blocks.append(m.group(1).strip()) or "",
        text,
    )
    result = re.sub(r"□[\s\S]*?□", "", result)
    if return_thinking:
        return " ".join(think_blocks), result.strip()
    return result.strip()


def _parse_groq_xml_tool_call(error_str: str) -> tuple[str, dict] | None:
    """Parse Groq error containing XML-formatted tool call into (name, args)."""
    s = str(error_str)
    name_match = re.search(r"function=(\w+)", s)
    if not name_match:
        name_match = re.search(r"tool '(\w+)", s)
    if not name_match:
        return None
    name = name_match.group(1)

    start = s.find("{", name_match.end())
    if start == -1:
        return name, {}
    depth = 0
    for i, ch in enumerate(s[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                args_str = s[start : i + 1].replace('\\"', '"')
                try:
                    args = json.loads(args_str) or {}
                except json.JSONDecodeError:
                    return name, {}
                return name, args
    return name, {}


async def _execute_tool_with_self_heal(
    tool_name: str,
    args: dict,
    attempt: int = 0,
) -> str:
    """Execute a tool with small recovery tree to reduce transient failures."""
    plans: list[tuple[str, dict]] = [("primary", dict(args or {}))]

    sanitized = {str(k): (v.strip(" \t\n\r\"'") if isinstance(v, str) else v) for k, v in (args or {}).items()}
    if sanitized != (args or {}):
        plans.append(("sanitized", sanitized))

    errors: list[str] = []
    for label, attempt_args in plans:
        try:
            result = await execute_tool(tool_name, attempt_args)  # type: ignore
            return result
        except Exception as e:
            errors.append(f"{label}: {e}")

    return f"tool error: {'; '.join(set(errors))}"


# ── Core model call ─────────────────────────────────────────────────────────────


async def _call_model(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> Any:
    """Call a model via litellm acompletion."""
    provider = model.split("/")[0].lower()

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        **kwargs,
    }

    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if provider == "openrouter":
        kwargs["api_base"] = "https://openrouter.ai/api/v1"
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        kwargs["api_key"] = api_key
        kwargs["extra_body"] = {
            "HTTP-Referer": "https://github.com/Bashara-aina/Babas_Swarms_bot",
            "X-Title": "LegionSwarm",
        }

    elif provider == "minimax":
        kwargs["api_base"] = "https://api.minimax.io/v1"
        api_key = os.getenv("MINIMAX_API_KEY", "")
        if not api_key:
            raise ValueError("MINIMAX_API_KEY not set")
        kwargs["api_key"] = api_key

    elif provider == "anthropic":
        kwargs["api_base"] = "https://api.minimax.io/anthropic"
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        kwargs["api_key"] = api_key

    else:
        api_key = _get_api_key(model)
        if not api_key:
            raise ValueError(f"No API key for '{provider}'")
        kwargs["api_key"] = api_key

    # MiniMax retry logic — exponential backoff with jitter: 30s -> 60s -> 120s
    if provider == "minimax":
        for attempt in range(3):
            try:
                return await acompletion(**kwargs)
            except litellm.RateLimitError as e:
                if attempt < 2:
                    wait = min(30 * (2**attempt) + random.uniform(0, 5), 300)
                    logger.warning(f"MiniMax rate limit, attempt {attempt + 1}/3, waiting {wait:.1f}s: {e}")
                    await asyncio.sleep(wait)
                else:
                    raise
    return await acompletion(**kwargs)


# ── Wiki completion (lightweight, no humanization stack) ──────────────────────


async def wiki_raw_completion(
    user_prompt: str,
    *,
    system_prompt: str = "You follow instructions precisely. Output only what is asked — no preamble.",
    model: str | None = None,
    temperature: float = 0.25,
) -> str:
    """Single-turn LLM call for wiki maintenance (no mem0 / wiki / humanization stack)."""
    m = model or os.getenv("LEGION_WIKI_LLM_MODEL", "minimax/MiniMax-M2.7")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        resp = await _call_model(m, messages, temperature=temperature)
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("wiki_raw_completion failed: %s", e)
        return f"[wiki completion error: {e}]"


# ── Context compaction ────────────────────────────────────────────────────────────


def _compact_messages(
    messages: list[dict],
    keep_recent: int = 6,
    system_prompt: str = "",
    max_turns: int | None = None,
) -> list[dict]:
    """Compact conversation history to fit context window, preserving recent turns."""
    if max_turns is not None:
        keep_recent = max_turns
    if len(messages) <= keep_recent + 1:
        return messages

    system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    recent = messages[-keep_recent:]
    history = messages[1:-keep_recent] if not system_msg else messages[1:-keep_recent]

    summary_parts: list[str] = []
    for m in history:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant" and m.get("tool_calls"):
            tool_names = [tc.get("function", {}).get("name", "?") for tc in m.get("tool_calls", [])]
            summary_parts.append(f"Called tools: {', '.join(tool_names)}")
        elif role == "tool":
            truncated = content[:150] + "\u2026" if len(content) > 150 else content
            summary_parts.append(f"[tool: {truncated}]")
        elif role:
            truncated = content[:200] + "\u2026" if len(content) > 200 else content
            summary_parts.append(f"[{role}]: {truncated}")

    summary_text = "\n".join(summary_parts[-8:]) if summary_parts else "[older conversation omitted]"
    summary_msg = {
        "role": "system",
        "content": (f"[Conversation history (condensed from {len(history)} messages):]\n{summary_text}"),
    }

    result: list[dict] = []
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
    elif system_msg:
        result.append(system_msg)
    result.append(summary_msg)
    result.extend(recent)
    return result


# ── Agentic tool-calling loop ──────────────────────────────────────────────────


async def _agent_loop_inner(
    task: str,
    chain: list[str],
    system: str,
    image_b64: str | None = None,
    user_id: str | None = None,
    thread_id: str | None = None,
    progress_cb: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    photo_cb: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> tuple[str, str]:
    """Inner loop for agentic /do command — handles tool_calls from LLM."""
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]
    if image_b64:
        messages[1] = {
            "role": "user",
            "content": [
                {"type": "text", "text": task},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            ],
        }

    model = chain[0]
    steps_taken: list[str] = []
    consecutive_failures = 0
    total_tokens_used = 0

    def _advance_model() -> bool:
        nonlocal model, consecutive_failures
        current_idx = chain.index(model) if model in chain else 0
        if current_idx + 1 < len(chain):
            model = chain[current_idx + 1]
            logger.info("Advancing to fallback model: %s", model)
            consecutive_failures = 0
            return True
        return False

    for iteration in range(20):
        try:
            response = await _call_model(
                model,
                messages,
                max_tokens=2048,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                result_text = (msg.content or "").strip()
                if not result_text:
                    break

                if user_id:
                    try:
                        from core.conversation_interface import add_to_conversation

                        add_to_conversation(str(user_id), "user", task)
                        add_to_conversation(str(user_id), "assistant", result_text)
                    except Exception:
                        pass
                return result_text, model

            for tc in msg.tool_calls:
                fn = tc.function
                tool_name = fn.name
                args: dict[str, Any] = {}
                try:
                    args = json.loads(fn.arguments) if fn.arguments else {}
                except json.JSONDecodeError:
                    error_str = str(fn.arguments)
                    parsed = _parse_groq_xml_tool_call(error_str)
                    if parsed:
                        tool_name, args = parsed
                        logger.info("Recovered XML tool call: %s(%s)", tool_name, list(args.keys()) if args else [])

                if progress_cb:
                    await progress_cb(_tool_label(tool_name, args))

                tool_result_text = await _execute_tool_with_self_heal(tool_name, args)

                if tool_name == "take_screenshot":
                    screenshot_path = tool_result_text
                    if (
                        screenshot_path
                        and screenshot_path != "tool returned no output"
                        and Path(screenshot_path).exists()
                    ):
                        if photo_cb:
                            await photo_cb(screenshot_path)
                        try:
                            desc, _ = await analyze_screenshot(
                                screenshot_path, question="Describe exactly what's visible on screen."
                            )
                            tool_result_text = f"Screenshot taken. Screen shows:\n{desc}"
                        except Exception:
                            pass

                steps_taken.append(f"{tool_name} → {tool_result_text[:80]}...")

                tc_id = f"xml_{iteration}"
                messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": tc_id,
                                "type": "function",
                                "function": {"name": tool_name, "arguments": json.dumps(args)},
                            }
                        ],
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": tool_result_text[:4000],
                        "tool_call_id": tc_id,
                    }
                )

        except litellm.RateLimitError:
            _mark_rate_limited(model)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task, "rate limited on all providers")
            wait_s = _next_chain_cooldown_wait(chain)
            if wait_s > 0:
                return f"rate limited on all providers — retry in ~{wait_s}s", model
            return "rate limited on all providers — retry shortly", model

        except litellm.BadRequestError as e:
            logger.error("agent_loop BadRequest: %s", e)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task, f"model not available: {model}")
            return f"Model unavailable for /do: {model}. Please run /keys and retry.", model

        except litellm.AuthenticationError:
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task, f"auth error on model: {model}")
            return (
                f"Authentication failed for /do model {model}. Check API keys with /keys.",
                model,
            )

        except Exception as e:
            logger.exception("agent_loop error: %s", e)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task, f"error: {e}")
            return f"error: {e}", model

        if response is None or not hasattr(response, "choices") or not response.choices:
            logger.warning("agent_loop: empty response, breaking")
            break
        msg = response.choices[0].message

        if not msg.tool_calls:
            result_text = (msg.content or "").strip()
            if user_id:
                try:
                    from core.conversation_interface import add_to_conversation

                    add_to_conversation(str(user_id), "user", task)
                    add_to_conversation(str(user_id), "assistant", result_text)
                except Exception:
                    pass
            return result_text, model

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        if msg.content and msg.content.strip() and progress_cb:
            await progress_cb(f"\u2026 {msg.content[:200]}")

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            tc_id = tc.id
            tool_result_text = await _execute_tool_with_self_heal(tool_name, json.loads(tc.function.arguments))

            if tool_name == "take_screenshot":
                screenshot_path = tool_result_text
                if screenshot_path and screenshot_path != "tool returned no output" and Path(screenshot_path).exists():
                    if photo_cb:
                        await photo_cb(screenshot_path)
                    try:
                        description, _ = await analyze_screenshot(
                            screenshot_path,
                            question="Describe exactly what's visible on screen: "
                            "which apps, windows, text, errors. Be specific and detailed.",
                        )
                        tool_result_text = f"Screenshot taken. Screen shows:\n{description}"
                    except Exception:
                        pass

            steps_taken.append(f"{tool_name} → {tool_result_text[:80]}...")

            messages.append(
                {
                    "role": "tool",
                    "content": tool_result_text,
                    "tool_call_id": tc_id,
                }
            )
            consecutive_failures = 0

    summary = "\n".join(f"  • {s}" for s in steps_taken[-5:])
    return f"Max iterations reached.\nSteps:\n{summary}", model


async def agent_loop(
    task: str,
    agent_key: str = "computer",
    image_b64: str | None = None,
    user_id: str | None = None,
    thread_id: str | None = None,
    chain: list[str] | None = None,
    show_thinking: bool = False,
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    photo_cb: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> tuple[str, str]:
    """Public wrapper for _agent_loop_inner with conversation history injection."""
    if chain is None:
        chain = get_fallback_chain(agent_key or "computer")

    system = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["computer"])
    if user_id:
        try:
            from core.conversation_interface import get_conversation_summary_prompt

            ctx = get_conversation_summary_prompt(str(user_id))
            if ctx:
                system += "\n\n" + ctx
        except Exception:
            pass

    return await _agent_loop_inner(
        task=task,
        chain=chain,
        system=system,
        image_b64=image_b64,
        user_id=user_id,
        thread_id=thread_id,
        progress_cb=progress_fn,
        photo_cb=photo_cb,
    )


# ── Tool label ─────────────────────────────────────────────────────────────────


def _tool_label(name: str, args: dict) -> str:
    """Human-friendly progress label for a tool call."""
    labels = {
        "shell_execute": lambda a: f"$ {a.get('command', '')[:60]}",
        "take_screenshot": lambda a: "\U0001f4f8 grabbing screen\u2026",
        "mouse_click": lambda a: f"\U0001f5b1 click ({a.get('x')}, {a.get('y')}) [{a.get('button', 'left')}]",
        "keyboard_type": lambda a: f"\u2328\ufe0f typing: {a.get('text', '')[:30]}\u2026",
        "key_press": lambda a: f"\u2328\ufe0f {a.get('keys', '')}",
        "open_app": lambda a: f"\U0001f4c2 opening {a.get('app_name', '')}",
        "open_url": lambda a: f"\U0001f310 {a.get('url', '')}",
        "browser_navigate": lambda a: f"\U0001f310 \u2192 {a.get('url', '')}",
        "new_browser_tab": lambda a: f"\U0001f5c2 new tab: {a.get('url', '')}",
        "focus_window": lambda a: f"\U0001fa9f focus: {a.get('pattern', '')}",
        "list_windows": lambda a: "\U0001fa9f listing windows\u2026",
        "scroll_at": lambda a: f"\u2195 scroll {a.get('direction', 'down')} \xd7{a.get('amount', 3)}",
        "read_file": lambda a: f"\U0001f4d6 reading {a.get('path', '')}",
        "write_file": lambda a: f"\u270f\ufe0f writing {a.get('path', '')}",
        "list_directory": lambda a: f"\U0001f4c1 ls {a.get('path', '~')}",
        "open_folder_gui": lambda a: f"\U0001f4c1 open {a.get('path', '~')}",
        "get_clipboard": lambda a: "\U0001f4cb get clipboard",
        "set_clipboard": lambda a: "\U0001f4cb set clipboard",
        "install_packages": lambda a: f"\U0001f4e6 pip install {' '.join(a.get('packages', []))}",
        "web_browse": lambda a: f"\U0001f310 browsing {a.get('url', '')}",
        "web_search": lambda a: f"\U0001f50d searching: {a.get('query', '')}",
        "web_research": lambda a: f"\U0001f52c researching: {a.get('topic', '')[:40]}\u2026",
        "web_fill_form": lambda a: f"\U0001f4dd filling form at {a.get('url', '')}",
        "web_get_links": lambda a: f"\U0001f517 getting links from {a.get('url', '')}",
        "web_click": lambda a: f"\U0001f5b1 clicking '{a.get('click_text', '')}' on {a.get('url', '')}",
        "read_pdf": lambda a: f"\U0001f4c4 reading PDF {a.get('path', '')}",
        "pdf_extract_tables": lambda a: f"\U0001f4ca extracting tables from {a.get('path', '')}",
        "read_excel": lambda a: f"\U0001f4d7 reading Excel {a.get('path', '')}",
        "write_excel": lambda a: f"\U0001f4d7 writing Excel {a.get('path', '')}",
        "excel_update_cell": lambda a: f"\U0001f4d7 updating {a.get('cell', '')} in {a.get('path', '')}",
        "ocr_image": lambda a: f"\U0001f524 OCR on {a.get('path', '')}",
        "ocr_pdf": lambda a: f"\U0001f524 OCR PDF {a.get('path', '')}",
        "read_docx": lambda a: f"\U0001f4dd reading Word {a.get('path', '')}",
        "organize_files": lambda a: f"\U0001f4c2 organizing {a.get('directory', '')}",
        "find_files": lambda a: f"\U0001f50e finding {a.get('pattern', '')} in {a.get('directory', '')}",
        "file_info": lambda a: f"\u2139\ufe0f info: {a.get('path', '')}",
        "email_check_inbox": lambda a: "\U0001f4e7 checking inbox\u2026",
        "email_read": lambda a: f"\U0001f4e7 reading email {a.get('uid', '')}",
        "email_send": lambda a: f"\U0001f4e7 sending to {a.get('to', '')}",
        "email_reply": lambda a: f"\U0001f4e7 replying to {a.get('uid', '')}",
        "email_search": lambda a: f"\U0001f50d searching emails: {a.get('query', '')}",
        "email_summarize": lambda a: "\U0001f4e7 summarizing inbox\u2026",
        "git_status": lambda a: f"\U0001f4e6 git status {a.get('repo_path', '')}",
        "git_diff": lambda a: f"\U0001f4e6 git diff {a.get('repo_path', '')}",
        "git_log": lambda a: f"\U0001f4e6 git log {a.get('repo_path', '')}",
        "git_commit": lambda a: f"\U0001f4e6 git commit: {a.get('message', '')[:40]}",
        "git_branch": lambda a: f"\U0001f4e6 git branch {a.get('action', 'list')}",
        "git_pull": lambda a: f"\U0001f4e6 git pull {a.get('repo_path', '')}",
        "git_push": lambda a: f"\U0001f4e6 git push {a.get('repo_path', '')}",
        "git_stash": lambda a: f"\U0001f4e6 git stash {a.get('action', 'push')}",
        "run_tests": lambda a: f"\U0001f9ea running tests in {a.get('path', '.')}",
        "lint_code": lambda a: f"\U0001f50d linting {a.get('path', '')}",
        "find_in_codebase": lambda a: f"\U0001f50e grep '{a.get('pattern', '')}'",
        "analyze_codebase": lambda a: f"\U0001f4ca analyzing {a.get('path', '.')}",
        "db_query": lambda a: f"\U0001f5c4 SQL: {a.get('query', '')[:40]}",
        "check_disk_space": lambda a: "\U0001f4be checking disk space\u2026",
        "check_memory_usage": lambda a: "\U0001f9e0 checking memory\u2026",
        "check_gpu_health": lambda a: "\U0001f3ae checking GPU health\u2026",
        "check_services": lambda a: f"\U0001f527 checking services: {a.get('services', 'swarm-bot,ollama')}",
        "system_cleanup": lambda a: f"\U0001f9f9 {'previewing' if a.get('dry_run', True) else 'running'} cleanup\u2026",
        "check_updates": lambda a: "\U0001f4e6 checking for updates\u2026",
        "driver_status": lambda a: "\U0001f527 checking drivers\u2026",
        "full_maintenance_check": lambda a: "\U0001f3e5 full health check\u2026",
    }
    fn = labels.get(name)
    return fn(args) if fn else f"\U0001f527 {name}()"


# ── Single-turn chat ────────────────────────────────────────────────────────────


async def chat(
    task: str,
    agent_key: str | None = None,
    thread_id: str | None = None,
    image_b64: str | None = None,
    show_thinking: bool = False,
    user_id: str | None = None,
    task_context: str = "",
    model_override: str | None = None,
    routing_hint: str | None = None,
    run_post_hooks: bool = True,
) -> tuple[str, str]:
    """Single-turn Q&A for text responses."""
    if not agent_key:
        agent_key = detect_agent(task)
        try:
            from core.intent_router import classify_intent_fast as _cif

            _intent = _cif(task)
            if _intent.confidence >= 0.65 and _intent.suggested_agent:
                agent_key = _intent.suggested_agent
        except Exception:
            pass

    if agent_key == "general":
        try:
            from core.intent_classifier import classify_intent as _ci, _last_agent_key

            _intent_result = _ci(task, prior_agent_key=_last_agent_key.get(str(user_id) if user_id else "", "general"))
            if _intent_result.confidence >= 0.6:
                agent_key = _intent_result.agent_key
                if user_id:
                    _last_agent_key[str(user_id)] = agent_key
        except Exception:
            pass

    chain = get_fallback_chain(agent_key or "general")
    if model_override:
        chain = [model_override] + [m for m in chain if m != model_override]

    if image_b64 is None and agent_key in ("vision", "computer"):
        chain = [m for m in chain if not m.startswith("ollama_chat/")]
    elif agent_key == "vision" and image_b64 is not None:
        try:
            from tools.resource_monitor import can_use_local_model

            _local_ok, _local_skip_reason = await can_use_local_model()
            if not _local_ok:
                logger.info(
                    "Skipping local Ollama (resource constrained): %s",
                    _local_skip_reason,
                )
                chain = [m for m in chain if not m.startswith("ollama_chat/")]
        except Exception:
            pass

    prompt_sections: list[str] = []

    _soul = build_soul_context()
    if _soul:
        prompt_sections.append(_soul)

    prompt_sections.append(build_base_persona())

    _disagree = get_disagreement_prompt()
    if _disagree:
        prompt_sections.append(_disagree)

    _agent_role_full = SYSTEM_PROMPTS.get(agent_key, "")
    if _agent_role_full:
        _persona_prefix = _PERSONA + "\n\n"
        if _agent_role_full.startswith(_persona_prefix):
            _agent_specialization = _agent_role_full[len(_persona_prefix) :]
        elif _agent_role_full.startswith(_PERSONA):
            _agent_specialization = _agent_role_full[len(_PERSONA) :].strip()
        else:
            _agent_specialization = _agent_role_full
        if _agent_specialization.strip():
            prompt_sections.append(f"[AGENT MODE: {agent_key.upper()}]\n{_agent_specialization.strip()}")

    _current_emotion = "neutral"
    try:
        from tools.letta_personality import get_persona_state as _gps

        _current_emotion = str(_gps().get("dominant_emotion", "neutral"))
        detected = detect_emotion_from_context(task, _current_emotion)
        if detected != _current_emotion:
            update_emotion(detected, event=f"Context shift from message: {task[:50]}")
            _current_emotion = detected
        prompt_sections.append(build_emotion_modifier(_current_emotion))
    except Exception:
        pass

    try:
        from core.episodic_narrative import build_narrative_context

        _narrative = build_narrative_context(task)
        if _narrative:
            prompt_sections.append(_narrative)
    except Exception:
        pass

    try:
        from core.relationship_memory import get_relationship_context

        rel_ctx = get_relationship_context()
        if rel_ctx:
            prompt_sections.append(rel_ctx)
    except Exception:
        pass

    try:
        from core.cognition_pipeline import build_cognition_system_fragment

        _cog = build_cognition_system_fragment(str(user_id), task, routing_hint=routing_hint)
        if _cog:
            prompt_sections.append(_cog)
    except Exception:
        pass

    try:
        from core.intent_router import classify_intent_fast, build_intent_hint

        _intent_result = classify_intent_fast(task)
        _intent_hint = build_intent_hint(_intent_result)
        if _intent_hint:
            prompt_sections.append(_intent_hint)
    except Exception:
        pass

    try:
        from core.memory_manager import LegionSemanticMemory

        semantic_memory_lines = await LegionSemanticMemory().search_memories(task, str(user_id), limit=5)
    except Exception:
        pass

    try:
        from core.unified_prompt_context import gather_parallel_prompt_layers

        _chat_mode = os.getenv("LEGION_CHAT_MODE", "text")
        for _layer in await gather_parallel_prompt_layers(task, str(user_id), mode=_chat_mode):
            if _layer:
                prompt_sections.append(_layer)
    except Exception:
        pass

    _conversation_history: list[dict] = []
    if user_id:
        try:
            from core.conversation_interface import get_conversation_history as _get_ch

            _conversation_history = _get_ch(str(user_id), last_n=6)
        except Exception:
            pass

        try:
            from core.memory.unified_context import build_unified_memory_context

            umc = await build_unified_memory_context(str(user_id), task)
            if umc:
                prompt_sections.append(umc)
        except Exception:
            pass

    try:
        from tools.memoryos_client import mos_retrieve_context

        mos_ctx = await mos_retrieve_context(query=task, user_id=str(user_id))
        if mos_ctx:
            prompt_sections.append(f"[Long-term conversation context from MemoryOS:]\n{mos_ctx}")
    except Exception:
        pass

    try:
        from tools.open_memory import om_search, build_om_context

        om_results = await om_search(user_id=str(user_id), query=task, limit=8)
        om_ctx = build_om_context(om_results)
        if om_ctx:
            prompt_sections.append(om_ctx)
    except Exception:
        pass

    try:
        from tools.memory import search_memory, build_memory_context

        legacy_memories = await search_memory(task, top_k=3, user_id=str(user_id))
        legacy_ctx = await build_memory_context(task, top_k=3, user_id=str(user_id))
        if legacy_ctx:
            prompt_sections.append(legacy_ctx)
    except Exception:
        pass

    try:
        from tools.persistence import get_instinct_context

        instinct_block = await get_instinct_context(max_tokens=300)
        if instinct_block:
            prompt_sections.append(instinct_block)
    except Exception:
        pass

    try:
        from tools.skill_loader import get_skills_for_agent

        skills_block = get_skills_for_agent(agent_key, max_chars=6000)
        if skills_block:
            prompt_sections.append(skills_block)
    except Exception:
        pass

    try:
        prompt_sections.append(build_mode_instructions(agent_key))
    except Exception:
        pass

    try:
        from core.research_policy import maybe_attach_research_context

        r_block, _ran = await maybe_attach_research_context(task, str(user_id), agent_key or "general")
        if r_block:
            prompt_sections.append(r_block)
    except Exception:
        pass

    if agent_key not in ("computer", "vision"):
        try:
            from core.character_voice import (
                get_debate_trigger,
                get_humor_nudge,
                get_opinion_on,
                get_proactive_check,
            )

            proactive_nudge = get_proactive_check(task)
            if proactive_nudge:
                prompt_sections.append(proactive_nudge)

            debate_block = get_debate_trigger(task)
            if debate_block:
                prompt_sections.append(debate_block)
            else:
                opinion_block = get_opinion_on(task)
                if opinion_block:
                    prompt_sections.append(opinion_block)

            humor_block = get_humor_nudge(task)
            if humor_block:
                prompt_sections.append(humor_block)

        except Exception:
            pass

    system_prompt = "\n\n".join(section for section in prompt_sections if section)

    _word_count = len(task.split()) if task else 0
    if agent_key not in ("computer", "vision", "think") and _word_count > 12:
        system_prompt += (
            "\n\n[INTERNAL REASONING DISCIPLINE]\n"
            "Before finalising your response, briefly stress-test it: "
            "ask yourself 'Is this actually correct? What would a smart skeptic push back on?' "
            "If the self-check reveals a real weakness or blind spot, lead with it honestly. "
            "If your first take holds up, answer with confidence — no need to hedge. "
            "This is about intellectual honesty, not performative uncertainty."
        )

    if image_b64:
        user_content: Any = [
            {"type": "text", "text": task},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
    else:
        user_content = task

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(_conversation_history)
    messages.append({"role": "user", "content": user_content})

    _skip_cache = image_b64 is not None or show_thinking or agent_key == "vision"
    if not _skip_cache:
        try:
            from tools.persistence import cache_get

            _cache_key = hashlib.sha256(f"{agent_key}:{task}:{chain[0]}".encode()).hexdigest()
            cached = await cache_get(_cache_key)
            if cached:
                logger.info("Cache hit for agent=%s", agent_key)
                if thread_id:
                    add_to_thread(thread_id, agent_key, task, cached)
                return cached, f"cache:{chain[0]}"
        except Exception:
            _cache_key = ""
    else:
        _cache_key = ""

    last_error: Exception = Exception("No models available")
    hooks = get_hooks()

    for model in chain:
        if _is_rate_limited(model):
            continue

        try:
            logger.info("Trying: %s (agent=%s)", model, agent_key)
            _t0 = time.time()
            await hooks.emit(
                "pre_llm_call",
                {
                    "agent": agent_key,
                    "model": model,
                    "task": task[:200],
                },
            )
            resp = await _call_model(
                model,
                messages,
                temperature={
                    "excited": 0.85,
                    "curious": 0.82,
                    "frustrated": 0.6,
                    "focused": 0.2,
                    "debug": 0.2,
                    "happy": 0.88,
                    "banter": 0.92,
                }.get(_current_emotion, 0.7),
            )
            raw = (resp.choices[0].message.content or "").strip()
            _elapsed_ms = int((time.time() - _t0) * 1000)

            _usage = getattr(resp, "usage", None)
            _tin = getattr(_usage, "prompt_tokens", 0) if _usage else 0
            _tout = getattr(_usage, "completion_tokens", 0) if _usage else 0

            await hooks.emit(
                "post_llm_call",
                {
                    "agent": agent_key,
                    "model": model,
                    "tokens_in": _tin,
                    "tokens_out": _tout,
                    "duration_ms": _elapsed_ms,
                    "success": True,
                },
            )

            thinking, answer = _strip_think_tags(raw, return_thinking=True)
            if thinking and show_thinking:
                _th_suffix = "\u2026" if len(thinking) > 400 else ""
                result = f"<i>\U0001f4ad {thinking[:400]}{_th_suffix}</i>\n\n{answer}"
            else:
                result = answer if thinking else raw

            if thread_id:
                add_to_thread(thread_id, agent_key, task, result)

            if user_id:
                try:
                    from core.conversation_interface import add_to_conversation

                    add_to_conversation(user_id, "user", task)
                    add_to_conversation(user_id, "assistant", result)
                except Exception:
                    pass

            if _cache_key:
                try:
                    from tools.persistence import cache_set

                    await cache_set(_cache_key, result, agent_key, model, _tin + _tout)
                except Exception:
                    pass

            if run_post_hooks:
                try:
                    asyncio.create_task(
                        _post_call_hooks(
                            user_msg=task,
                            response=result,
                            agent_used=agent_key,
                            session_id=thread_id,
                            user_id=user_id,
                        )
                    )
                except Exception:
                    pass

            logger.info("Success: %s", model)
            try:
                result = postprocess_response(result, _current_emotion, task)
            except Exception:
                pass
            try:
                from core.character_enforcer import enforce_character

                result = enforce_character(result, agent_key)
            except Exception:
                pass
            try:
                from core.episodic_narrative import update_narrative_from_conversation

                asyncio.create_task(asyncio.to_thread(update_narrative_from_conversation, task, result))
            except Exception:
                pass
            try:
                from core.self_improvement import buffer_conversation, maybe_run_self_review

                buffer_conversation(task, result)
                asyncio.create_task(maybe_run_self_review())
            except Exception:
                pass
            try:
                from core.humanizer import humanize

                result = humanize(result, emotion=_current_emotion)
            except Exception:
                pass

            if user_id and os.getenv("LEGION_WIKI_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
                try:
                    from core.wiki_manager import schedule_wiki_ingest_exchange

                    asyncio.create_task(schedule_wiki_ingest_exchange(str(user_id), task, result))
                except Exception:
                    pass

            if user_id and os.getenv("LEGION_WIKI_AUTO_INGEST", "1").strip().lower() not in ("0", "false", "no", "off"):
                try:
                    from core.wiki_auto_ingest import on_conversation_turn

                    asyncio.create_task(on_conversation_turn(str(user_id), task, result))
                except Exception:
                    pass

            if user_id:
                try:
                    from core.working_memory import record_turn

                    record_turn(
                        str(user_id),
                        user_message=task,
                        assistant_snippet=result,
                        agent_key=agent_key or "",
                        routing_hint=routing_hint or "",
                    )
                except Exception:
                    pass

            if user_id:
                try:
                    from core.memory_engine import MemoryEngine

                    _me = MemoryEngine()
                    await _me.store(
                        {
                            "user_id": str(user_id),
                            "turn": {"user": task, "assistant": result},
                            "emotion_state": None,
                            "agent_key": agent_key or "",
                        }
                    )
                except Exception:
                    pass

            return result, model

        except litellm.RateLimitError:
            _mark_rate_limited(model)
            continue
        except litellm.AuthenticationError:
            logger.error("Auth error: %s", model)
            last_error = Exception(f"Auth error: {model}")
            continue
        except litellm.BadRequestError as e:
            logger.warning("BadRequest %s: %s", model, e)
            last_error = e
            continue
        except ValueError as e:
            last_error = e
            continue
        except Exception as e:
            logger.warning("Error %s: %s", model, e)
            last_error = e
            continue

    raise RuntimeError(
        f"All models exhausted for '{agent_key}'.\nLast error: {last_error}\nRun /keys to check API keys."
    )


# ── Post-call hooks ─────────────────────────────────────────────────────────────


async def _post_call_hooks(
    user_msg: str,
    response: str,
    agent_used: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """Runs asynchronously after every LLM call."""
    global memory, emotion, reflection

    try:
        init_humanization_layer()
        try:
            from tools.letta_personality import update_emotion
            from core.emotion_modulator import detect_emotion_from_context

            update_emotion(detect_emotion_from_context(user_msg), event=f"assistant response: {response[:80]}")
        except Exception:
            pass
        if emotion is not None:
            emotion.update_from_interaction(user_msg, response)
        if memory is not None:
            await memory.auto_extract_and_save(user_msg, response)
            emotion_state = emotion.state.to_dict() if emotion is not None else None
            memory.add_conversation_turn(
                "user",
                user_msg,
                agent_used=agent_used,
                emotion_state=emotion_state,
                session_id=session_id,
            )
            memory.add_conversation_turn(
                "assistant",
                response,
                agent_used=agent_used,
                emotion_state=emotion_state,
                session_id=session_id,
            )
        if reflection is not None:
            await reflection.post_turn_hook(user_msg, response)

        if user_id:
            try:
                from tools.recallmax import should_store
                from core.memory_manager import LegionSemanticMemory
                from tools.memoryos_client import mos_add_conversation
                from tools.open_memory import SECTOR_EPISODIC, SECTOR_SEMANTIC, om_store

                _mem_msgs: list[dict[str, str]] = [{"role": "user", "content": user_msg}]
                if should_store(user_msg):
                    _mem_msgs.append({"role": "assistant", "content": response})
                await LegionSemanticMemory().save_memory(_mem_msgs, str(user_id))
                await mos_add_conversation(user_msg=user_msg, assistant_msg=response, user_id=str(user_id))
                await om_store(user_id=str(user_id), content=user_msg, sector=SECTOR_EPISODIC)
                if should_store(user_msg):
                    await om_store(user_id=str(user_id), content=user_msg, sector=SECTOR_SEMANTIC, importance=1.5)
            except Exception:
                pass

        try:
            from core.memory.consolidator import promote_important

            recent = [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": response},
            ]
            asyncio.create_task(promote_important(recent))
        except Exception:
            pass

        try:
            from core.relationship_memory import record_interaction

            record_interaction(user_msg, response_length=len(response))
        except Exception:
            pass

    except Exception as exc:
        logger.warning("[PostCall hooks] %s", exc)


# ── Facade ──────────────────────────────────────────────────────────────────────


class _LLMClientFacade:
    """Compatibility facade exposing complete() for handler integrations."""

    async def complete(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        task_context: str = "",
        skip_post_hooks: bool = False,
        **kwargs: Any,
    ) -> str:
        user_msg = ""
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                user_msg = content if isinstance(content, str) else str(content)
                break
        if not user_msg and messages:
            content = messages[-1].get("content", "")
            user_msg = content if isinstance(content, str) else str(content)

        response, _used_model = await chat(
            task=user_msg,
            agent_key=None,
            thread_id=None,
            image_b64=None,
            show_thinking=kwargs.get("show_thinking", False),
            user_id=kwargs.get("user_id"),
            task_context=task_context,
            model_override=model,
            run_post_hooks=not skip_post_hooks,
        )

        return response


llm_client = _LLMClientFacade()


# ── Screenshot utilities ────────────────────────────────────────────────────────


if _COMPUTER_AVAILABLE:
    take_screenshot = computer_agent.take_screenshot
else:

    async def take_screenshot() -> str:  # type: ignore
        return ""


async def analyze_screenshot(image_path: str, question: str = "Describe what you see on screen.") -> tuple[str, str]:
    """Analyze a screenshot with vision model."""
    img_path = Path(image_path)
    if not img_path.exists() or img_path.stat().st_size < 500:
        raise RuntimeError(
            f"Screenshot file is missing or too small "
            f"({img_path.stat().st_size if img_path.exists() else 0} bytes): {image_path}"
        )
    try:
        from PIL import Image as _PILImage

        with _PILImage.open(image_path) as _img:
            _img.verify()
    except Exception as e:
        raise RuntimeError(f"Screenshot is not a valid image: {e}")

    async with aiofiles.open(image_path, "rb") as f:
        raw_bytes = await f.read()
    b64 = base64.b64encode(raw_bytes).decode()

    vision_question = question
    _skip_local = False
    _skip_reason = ""

    try:
        from tools.resource_monitor import can_use_local_model

        _local_ok, _skip_reason = await can_use_local_model()
        if not _local_ok:
            _skip_local = True
            logger.info(
                "analyze_screenshot: skipping Ollama (resource constrained): %s",
                _skip_reason,
            )
    except Exception:
        pass

    if not _skip_local:
        try:
            resp = await _call_model(
                "ollama_chat/gemma4:e4b",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_question},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }
                ],
                max_tokens=1024,
            )
            result = (resp.choices[0].message.content or "").strip()
            logger.info("Screenshot analyzed locally via Ollama")
            return result, "ollama/gemma4:e4b \U0001f512 local"
        except Exception as e:
            logger.warning("Ollama vision failed: %s \u2192 trying Groq", e)
    else:
        logger.info("analyze_screenshot: using cloud directly (%s)", _skip_reason)

    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        raise RuntimeError("No GROQ_API_KEY and Ollama vision failed/skipped")

    try:
        resp = await acompletion(
            model="groq/meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS["vision"]},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_question},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ],
                },
            ],
            api_key=groq_key,
            max_tokens=1024,
        )
        result = (resp.choices[0].message.content or "").strip()
        _cloud_label = "groq/llama-4-scout"
        if _skip_local and _skip_reason:
            _cloud_label += f" \u2601\ufe0f (local bypassed: {_skip_reason[:60]})"
        logger.info("Screenshot analyzed via Groq cloud vision")
        return result, _cloud_label
    except Exception as e:
        raise RuntimeError(
            f"Screenshot analysis failed.\n"
            f"\u2022 Local: {'bypassed — ' + _skip_reason if _skip_local else 'run ollama pull gemma4:e4b'}\n"
            f"\u2022 Cloud: {e}"
        )


# ── Shell execution ────────────────────────────────────────────────────────────


async def run_shell_command(cmd: str, timeout: int = 30) -> str:
    """Alias for computer_agent.run_shell used by main.py."""
    if not _COMPUTER_AVAILABLE:
        return "computer_agent not available"
    return await computer_agent.run_shell(cmd, timeout=timeout)


# ── Output utilities ──────────────────────────────────────────────────────────


def chunk_output(text: str, max_length: int = 4000) -> list[str]:
    """Split text into Telegram-safe chunks (4096 char limit)."""
    if text is None:
        return []
    text = str(text)
    if text == "":
        return []
    if len(text) <= max_length:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        while len(line) > max_length:
            remaining_space = max_length - len(current)
            if remaining_space <= 0:
                chunks.append(current.rstrip())
                current = ""
                break
            current += line[:remaining_space]
            line = line[remaining_space:]
            chunks.append(current.rstrip())
            current = ""
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
        "CEREBRAS_API_KEY",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
        "ZAI_API_KEY",
        "HF_TOKEN",
    ]
    return {k: bool(os.getenv(k)) for k in keys}
