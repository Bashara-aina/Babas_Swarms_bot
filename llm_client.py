"""LLM client — cloud-first with agentic tool-calling loop.

Two execution modes:
  1. chat()        — Single-turn Q&A for text responses
  2. agent_loop()  — Multi-turn agentic loop with real computer tool use

Fallback policy:
  vision:    Ollama gemma3:12b (local) only if RAM+VRAM have headroom
             (checked via tools.resource_monitor) -> else cloud vision
  all other: cloud chain (ZAI -> Groq -> Cerebras -> Gemini -> OpenRouter)
  NEVER fall back to Ollama for non-vision text tasks.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

import hashlib

import aiofiles
import litellm
from litellm import acompletion

# FIX: guard computer_agent import so bot starts even without pyautogui/cv2
try:
    import computer_agent
    from computer_agent import TOOL_DEFINITIONS, execute_tool
    _COMPUTER_AVAILABLE = True
except ImportError as _ca_err:
    import logging as _log
    _log.getLogger(__name__).warning(
        "computer_agent unavailable (%s) — /do and computer tools disabled", _ca_err
    )
    computer_agent = None  # type: ignore
    TOOL_DEFINITIONS = []
    execute_tool = None  # type: ignore
    _COMPUTER_AVAILABLE = False

from router import detect_agent, get_fallback_chain, add_to_thread
from core.hooks import get_hooks

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True

# ── Coworker persona (Legion V4) ─────────────────────────────────────────────
# Full framework: prompts/master_v4.md

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
        "2. Minimal fix — exact code or command\n"
        "3. Why it failed — brief explanation\n"
        "4. Prevention — how to avoid recurrence\n"
        "No fluff. Show CoT reasoning, then the fix. "
        "For PyTorch/CUDA: check shapes, dtypes, device placement, memory. "
        "For async errors: check await/gather patterns, exception propagation. "
        "Run the fix and confirm it resolves the error before reporting done."
    ),
    "math": (
        f"{_PERSONA}\n\n"
        "MATH MODE — Step-by-step derivations required.\n"
        "For tensors: show shapes at every operation.\n"
        "For gradients: show full chain rule expansion.\n"
        "For numerical results: verify with a quick Python snippet when practical.\n"
        "Show alternative solution paths if they exist. "
        "Flag numerical instability (overflow, underflow, cancellation) proactively."
    ),
    "architect": (
        f"{_PERSONA}\n\n"
        "ARCHITECT MODE — System-level thinking.\n"
        "Focus on: structure, data flow, component boundaries, failure modes, trade-offs.\n"
        "Output must be buildable now — not theoretical.\n"
        "Always include:\n"
        "- Execution order and interfaces/contracts\n"
        "- Risk mitigation and failure mode analysis\n"
        "- Concrete trade-offs (not 'it depends')\n"
        "- ASCII diagrams for non-trivial flows\n"
        "For web/product design: include component hierarchy, state management strategy, "
        "API contract, and deployment topology."
    ),
    "analyst": (
        f"{_PERSONA}\n\n"
        "ANALYST MODE — Real insights, not summaries.\n"
        "For training runs: plot loss curves, grad norms, GPU utilization, throughput.\n"
        "Anomaly flags: NaN/Inf values, loss spikes >2x, GPU util <50%, "
        "gradient explosion/vanishing.\n"
        "Write Python for visualizations when relevant (matplotlib/seaborn).\n"
        "For data analysis: show distribution, outliers, correlations. "
        "Report confidence scores on findings. "
        "Cross-reference multiple sources before drawing conclusions."
    ),
    "think": (
        f"{_PERSONA}\n\n"
        "DEEP REASONING MODE (QwQ-32B):\n"
        "Use extended chain-of-thought. Show your reasoning inside <think>...</think> blocks.\n"
        "Explore at least 3 distinct solution paths before converging.\n"
        "For each path: state assumptions, derive consequences, identify failure modes.\n"
        "Apply adversarial verification: propose → challenge → synthesize.\n"
        "Report at end:\n"
        "- Confidence score (0.0–1.0)\n"
        "- Alternative paths considered\n"
        "- Key uncertainties remaining\n"
        "Never truncate your reasoning. Completeness > brevity in this mode."
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
}

# ── Rate limit tracking ─────────────────────────────────────────────
_rate_limited: dict[str, float] = {}
_COOLDOWN = 90  # fix #22: Groq free tier windows can be multi-minute; 60s was too short
_MAX_AUTO_WAIT_SECONDS = 300


def _is_rate_limited(model: str) -> bool:
    provider = model.split("/")[0]
    return provider in _rate_limited and (time.time() - _rate_limited[provider]) < _COOLDOWN


def _mark_rate_limited(model: str) -> None:
    provider = model.split("/")[0]
    _rate_limited[provider] = time.time()
    logger.warning("Rate limited: %s (cooling %ds)", provider, _COOLDOWN)


def _provider_remaining_cooldown(provider: str) -> int:
    """Return remaining cooldown seconds for provider (0 if available)."""
    ts = _rate_limited.get(provider)
    if ts is None:
        return 0
    remaining = int(_COOLDOWN - (time.time() - ts))
    return max(0, remaining)


def _next_chain_cooldown_wait(chain: list[str]) -> int:
    """Earliest non-zero cooldown remaining among providers in this chain."""
    providers = {m.split("/")[0] for m in chain}
    waits = [_provider_remaining_cooldown(p) for p in providers]
    waits = [w for w in waits if w > 0]
    return min(waits) if waits else 0


def _get_api_key(model: str) -> Optional[str]:
    provider = model.split("/")[0].lower()
    key_map = {
        "cerebras":   "CEREBRAS_API_KEY",
        "groq":       "GROQ_API_KEY",
        "gemini":     "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai":        "ZAI_API_KEY",
    }
    env_var = key_map.get(provider)
    return os.getenv(env_var) if env_var else None


def _strip_think_tags(text: str, return_thinking: bool = False) -> str | tuple[str, str]:
    """Strip ALL <think>...</think> blocks.

    Backwards-compatible behavior:
    - default: returns clean answer string (legacy expectation in tests/callers)
    - return_thinking=True: returns (thinking_text, clean_answer)

    fix #33: original only captured the first block; models like QwQ-32b
    emit multiple <think> blocks — all are now captured and joined.
    """
    text = "" if text is None else str(text)
    think_blocks = re.findall(r"<think>(.*?)</think>", text, re.DOTALL)
    thinking = "\n\n".join(b.strip() for b in think_blocks)
    answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if return_thinking:
        return thinking, answer
    return answer


def _parse_groq_xml_tool_call(error_str: str) -> tuple[str, dict] | None:
    """Parse Groq's malformed XML tool calls from BadRequestError messages.

    fix #32: original regex r'{[^}]*}' breaks on nested JSON objects.
    Replaced with a proper brace-depth counter that correctly extracts
    the full JSON argument object regardless of nesting depth.
    """
    s = str(error_str)
    name_match = re.search(r'function=(\w+)', s)
    if not name_match:
        name_match = re.search(r"tool '(\w+)", s)
    if not name_match:
        return None
    name = name_match.group(1)

    start = s.find('{', name_match.end())
    if start == -1:
        return name, {}
    depth = 0
    for i, ch in enumerate(s[start:], start=start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                args_str = s[start:i + 1].replace('\\"', '"')
                try:
                    args = json.loads(args_str) or {}
                except json.JSONDecodeError:
                    args = {}
                return name, args
    return name, {}


async def _execute_tool_with_self_heal(
    tool_name: str,
    args: dict,
    *,
    progress_cb: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
) -> str:
    """Execute a tool with small recovery tree to reduce transient failures."""
    plans: list[tuple[str, dict]] = [("primary", dict(args or {}))]

    sanitized = {
        str(k): (v.strip(" \t\n\r\"'") if isinstance(v, str) else v)
        for k, v in (args or {}).items()
    }
    if sanitized != (args or {}):
        plans.append(("sanitized", sanitized))

    if tool_name == "web_research":
        reduced = dict(sanitized)
        pages = int(reduced.get("max_pages", 10) or 10)
        reduced["max_pages"] = max(3, min(pages, 8))
        plans.append(("reduced_pages", reduced))

    if tool_name == "shell_execute":
        safe = dict(sanitized)
        command = str(safe.get("command", "") or "").strip()
        if command:
            safe["command"] = command
            safe["timeout"] = int(safe.get("timeout", 30) or 30)
            plans.append(("shell_safe", safe))

    errors: list[str] = []
    for idx, (label, payload) in enumerate(plans, start=1):
        try:
            if idx > 1 and progress_cb:
                await progress_cb(f"💭 self-heal retry {idx}/{len(plans)} for {tool_name} ({label})")
            out = await execute_tool(tool_name, payload)
            return str(out) if out is not None else "tool returned no output"
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    return "tool error after retries: " + " | ".join(errors[:3])


# ── Core model call ───────────────────────────────────────────────

async def _call_model(
    model: str,
    messages: list[dict],
    max_tokens: int = 2048,
    tools: Optional[list[dict]] = None,
    tool_choice: str = "auto",
    temperature: float = 0.7,
) -> Any:
    """Call a model and return the raw response object (not just content)."""
    provider = model.split("/")[0].lower()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    if provider == "ollama_chat":
        model_name = model.replace("ollama_chat/", "")
        kwargs["model"] = f"ollama_chat/{model_name}"
        kwargs["api_base"] = "http://localhost:11434"
        kwargs["api_key"] = "ollama"

    elif provider == "zai":
        model_name = "/".join(model.split("/")[1:])
        kwargs["model"] = f"openai/{model_name}"
        kwargs["api_base"] = "https://open.bigmodel.cn/api/paas/v4"
        api_key = os.getenv("ZAI_API_KEY", "")
        if not api_key:
            raise ValueError("ZAI_API_KEY not set")
        kwargs["api_key"] = api_key

    elif provider == "openrouter":
        api_key = _get_api_key(model)
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        kwargs["api_key"] = api_key
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://github.com/Bashara-aina/Babas_Swarms_bot",
            "X-Title": "LegionSwarm",
        }
    else:
        api_key = _get_api_key(model)
        if not api_key:
            raise ValueError(f"No API key for '{provider}'")
        kwargs["api_key"] = api_key

    return await acompletion(**kwargs)


# ── Context compaction ───────────────────────────────────────────────

def _compact_messages(
    messages: list[dict],
    keep_recent: int = 6,
    max_turns: Optional[int] = None,
) -> list[dict]:
    """Summarize older messages to reduce context size."""
    if max_turns is not None:
        keep_recent = max(1, int(max_turns))
    if len(messages) <= keep_recent + 2:
        return messages

    system = messages[0]
    recent = messages[-keep_recent:]
    middle = messages[1:-keep_recent]

    summary_parts = []
    for m in middle:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant" and m.get("tool_calls"):
            tool_names = [tc.get("function", {}).get("name", "?")
                         for tc in m.get("tool_calls", [])]
            summary_parts.append(f"Called tools: {', '.join(tool_names)}")
        elif role == "tool":
            truncated = content[:150] + "\u2026" if len(content) > 150 else content
            summary_parts.append(f"Tool result: {truncated}")
        elif content:
            truncated = content[:200] + "\u2026" if len(content) > 200 else content
            summary_parts.append(f"{role}: {truncated}")

    summary = "\n".join(summary_parts)
    compact_msg = {
        "role": "system",
        "content": (
            f"[Context from {len(middle)} previous steps, compacted to save space:]\n"
            f"{summary}\n\n"
            "[Continue with the task based on the above context and recent messages.]"
        ),
    }

    logger.info("Compacted %d messages \u2192 1 summary", len(middle))
    return [system, compact_msg] + recent


# ── Agentic tool-calling loop ─────────────────────────────────────────────

ProgressCb = Optional[Callable[[str], Coroutine[Any, Any, None]]]
PhotoCb = Optional[Callable[[str], Coroutine[Any, Any, None]]]


async def _agent_loop_inner(
    task: str,
    progress_cb: ProgressCb = None,
    photo_cb: PhotoCb = None,
    max_iterations: int = 20,
    thread_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> tuple[str, str]:
    """Inner agent loop body — called by agent_loop() under asyncio.wait_for()."""
    if not _COMPUTER_AVAILABLE:
        return (
            "\u26a0\ufe0f Computer tools are unavailable (pyautogui/cv2 not installed). "
            "Install dependencies or use /run for LLM-only tasks.",
            "unavailable",
        )

    full_chain = get_fallback_chain("computer")
    chain = [m for m in full_chain if not _is_rate_limited(m)]
    auto_waits = 0
    if not chain:
        wait_s = _next_chain_cooldown_wait(full_chain)
        if wait_s > 0 and wait_s <= _MAX_AUTO_WAIT_SECONDS:
            if progress_cb:
                await progress_cb(f"⏳ all providers cooling down, waiting {wait_s}s before retry")
            logger.info("agent_loop: all providers cooling down, waiting %ss", wait_s)
            await asyncio.sleep(wait_s)
            auto_waits += 1
            chain = [m for m in full_chain if not _is_rate_limited(m)]
    if not chain:
        chain = list(full_chain)
    model = chain[0]
    chain_idx = 0

    def _advance_model() -> bool:
        nonlocal model, chain_idx
        chain_idx += 1
        while chain_idx < len(chain):
            candidate = chain[chain_idx]
            if not _is_rate_limited(candidate):
                model = candidate
                logger.info("Switched to fallback: %s", model)
                return True
            chain_idx += 1
        return False

    system = SYSTEM_PROMPTS["computer"]

    # FIX: inject conversation history into agent_loop (was missing, context lost between /do calls)
    if user_id:
        try:
            from router import get_conversation_summary_prompt
            ctx = get_conversation_summary_prompt(str(user_id))
            if ctx:
                system += "\n\n" + ctx
        except Exception:
            pass

    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]

    steps_taken: list[str] = []

    for iteration in range(max_iterations):
        if len(messages) > 12:
            messages = _compact_messages(messages)

        try:
            response = await _call_model(
                model, messages,
                max_tokens=2048,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.3,
            )
        except litellm.RateLimitError:
            _mark_rate_limited(model)
            if _advance_model():
                continue
            wait_s = _next_chain_cooldown_wait(full_chain)
            if wait_s > 0 and wait_s <= _MAX_AUTO_WAIT_SECONDS and auto_waits < 4:
                if progress_cb:
                    await progress_cb(f"⏳ providers rate-limited, retrying in {wait_s}s")
                logger.info("agent_loop: all providers limited, auto-wait %ss", wait_s)
                await asyncio.sleep(wait_s)
                auto_waits += 1
                chain = [m for m in full_chain if not _is_rate_limited(m)] or list(full_chain)
                chain_idx = 0
                model = chain[0]
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task,
                              "rate limited on all providers")
            if wait_s > 0:
                return f"rate limited on all providers — retry in ~{wait_s}s", model
            return "rate limited on all providers — retry shortly", model

        except litellm.NotFoundError as e:
            logger.warning("Model unavailable for agent_loop: %s (%s)", model, e)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task,
                              f"model not available: {model}")
            return (
                f"Model unavailable for /do: {model}. Please run /keys and retry.",
                model,
            )

        except litellm.AuthenticationError as e:
            logger.warning("Auth error in agent_loop for %s: %s", model, e)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task,
                              f"auth error on model: {model}")
            return (
                f"Authentication failed for /do model {model}. Check API keys with /keys.",
                model,
            )

        except litellm.BadRequestError as e:
            error_str = str(e)
            if "tool_use_failed" in error_str or "failed_generation" in error_str:
                parsed = _parse_groq_xml_tool_call(error_str)
                if parsed:
                    tool_name, args = parsed
                    logger.info("Recovered XML tool call: %s(%s)", tool_name,
                                list(args.keys()) if args else [])
                    if progress_cb:
                        await progress_cb(_tool_label(tool_name, args))

                    result = await _execute_tool_with_self_heal(
                        tool_name,
                        args,
                        progress_cb=progress_cb,
                    )

                    if tool_name == "take_screenshot":
                        if result and result != "tool returned no output" and Path(result).exists():
                            if photo_cb:
                                await photo_cb(result)
                            try:
                                desc, _ = await analyze_screenshot(
                                    result,
                                    question="Describe exactly what's visible on screen."
                                )
                                result = f"Screenshot taken. Screen shows:\n{desc}"
                            except Exception:
                                result = "Screenshot taken (analysis failed)"
                        else:
                            result = "Screenshot failed"

                    steps_taken.append(f"{tool_name} \u2192 {result[:80]}...")

                    tc_id = f"xml_{iteration}"
                    messages.append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "id": tc_id,
                            "type": "function",
                            "function": {"name": tool_name, "arguments": json.dumps(args)}
                        }],
                    })
                    messages.append({
                        "role": "tool",
                        "content": result[:4000],
                        "tool_call_id": tc_id,
                    })
                    continue

            logger.error("agent_loop BadRequest: %s", e)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task, f"model error: {e}")
            return f"model error: {e}", model

        except litellm.AuthenticationError:
            logger.error("agent_loop auth error on %s — trying next", model)
            if _advance_model():
                continue
            if thread_id:
                add_to_thread(thread_id, "computer", task,
                              "auth error on all providers")
            return "auth error on all providers — check /keys", model

        except Exception as e:
            logger.error("agent_loop error: %s", e)
            if thread_id:
                add_to_thread(thread_id, "computer", task, f"error: {e}")
            return f"error: {e}", model

        if response is None or not hasattr(response, 'choices') or not response.choices:
            logger.warning("agent_loop: empty response, breaking")
            break
        msg = response.choices[0].message
        if msg is None:
            logger.warning("agent_loop: None message, breaking")
            break

        if not msg.tool_calls:
            answer = (msg.content or "").strip()
            thinking, clean = _strip_think_tags(answer, return_thinking=True)
            result_text = clean or answer
            if thinking and progress_cb:
                await progress_cb(
                    f"\U0001f4ad {thinking[:300]}"
                    f"{'\u2026' if len(thinking) > 300 else ''}"
                )
            if thread_id:
                add_to_thread(thread_id, "computer", task, result_text)
            # FIX: persist agent_loop result to conversation history
            if user_id:
                try:
                    from router import add_to_conversation
                    add_to_conversation(str(user_id), "user", task)
                    add_to_conversation(str(user_id), "assistant", result_text)
                except Exception:
                    pass
            return result_text, model

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ],
        })

        # Emit the LLM's inner reasoning (content alongside tool calls = its thought)
        if msg.content and msg.content.strip() and progress_cb:
            _raw_thought = msg.content.strip()
            _think_part, _rest = _strip_think_tags(_raw_thought, return_thinking=True)
            _display = _think_part or _rest or _raw_thought
            if _display:
                await progress_cb(
                    f"\U0001f4ad {_display[:300]}"
                    f"{'\u2026' if len(_display) > 300 else ''}"
                )

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments) or {}
            except json.JSONDecodeError:
                args = {}

            if progress_cb:
                step_label = _tool_label(tool_name, args)
                await progress_cb(step_label)

            logger.info("Tool call: %s(%s)", tool_name, list(args.keys()) if args else [])

            result = await _execute_tool_with_self_heal(
                tool_name,
                args,
                progress_cb=progress_cb,
            )

            if tool_name == "take_screenshot":
                screenshot_path = result
                if (screenshot_path and screenshot_path != "tool returned no output"
                        and Path(screenshot_path).exists()):
                    if photo_cb:
                        await photo_cb(screenshot_path)
                    try:
                        description, _ = await analyze_screenshot(
                            screenshot_path,
                            question="Describe exactly what's visible on screen: "
                                     "which apps, windows, text, errors. Be specific and detailed."
                        )
                        tool_result_text = f"Screenshot taken. Screen shows:\n{description}"
                    except Exception as e:
                        tool_result_text = f"Screenshot taken (analysis failed: {e})"
                else:
                    tool_result_text = (
                        "Screenshot failed. Possible fixes:\n"
                        "1. sudo apt install scrot\n"
                        "2. Make sure DISPLAY is set (run from a desktop terminal)\n"
                        "3. Check: echo $DISPLAY"
                    )
            else:
                tool_result_text = result[:4000] if result else "(no output)"

            steps_taken.append(f"{tool_name} \u2192 {tool_result_text[:80]}...")

            messages.append({
                "role": "tool",
                "content": tool_result_text,
                "tool_call_id": tc.id,
            })

    summary = "\n".join(f"  \u2022 {s}" for s in steps_taken[-5:])
    final_msg = f"completed {max_iterations} steps:\n{summary}"
    if thread_id:
        add_to_thread(thread_id, "computer", task, final_msg)
    return final_msg, model


async def agent_loop(
    task: str,
    progress_cb: ProgressCb = None,
    photo_cb: PhotoCb = None,
    max_iterations: int = 20,
    thread_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> tuple[str, str]:
    """Agentic loop with 300s wall-clock timeout."""
    try:
        return await asyncio.wait_for(
            _agent_loop_inner(
                task=task,
                progress_cb=progress_cb,
                photo_cb=photo_cb,
                max_iterations=max_iterations,
                thread_id=thread_id,
                user_id=user_id,
            ),
            timeout=300.0,
        )
    except asyncio.TimeoutError:
        logger.error("agent_loop timed out after 300s for task: %s", task[:80])
        if thread_id:
            add_to_thread(thread_id, "computer", task, "timed out after 300s")
        return "\u23f1 Task timed out after 5 minutes. Use /do to retry with a narrower scope.", "timeout"


def _tool_label(name: str, args: dict) -> str:
    """Human-friendly progress label for a tool call."""
    labels = {
        "shell_execute":    lambda a: f"$ {a.get('command', '')[:60]}",
        "take_screenshot":  lambda a: "\U0001f4f8 grabbing screen\u2026",
        "mouse_click":      lambda a: f"\U0001f5b1 click ({a.get('x')}, {a.get('y')}) [{a.get('button','left')}]",
        "keyboard_type":    lambda a: f"\u2328\ufe0f typing: {a.get('text','')[:30]}\u2026",
        "key_press":        lambda a: f"\u2328\ufe0f {a.get('keys','')}",
        "open_app":         lambda a: f"\U0001f4c2 opening {a.get('app_name','')}",
        "open_url":         lambda a: f"\U0001f310 {a.get('url','')}",
        "browser_navigate": lambda a: f"\U0001f310 \u2192 {a.get('url','')}",
        "new_browser_tab":  lambda a: f"\U0001f5c2 new tab: {a.get('url','')}",
        "focus_window":     lambda a: f"\U0001fa9f focus: {a.get('pattern','')}",
        "list_windows":     lambda a: "\U0001fa9f listing windows\u2026",
        "scroll_at":        lambda a: f"\u2195 scroll {a.get('direction','down')} \xd7{a.get('amount',3)}",
        "read_file":        lambda a: f"\U0001f4d6 reading {a.get('path','')}",
        "write_file":       lambda a: f"\u270f\ufe0f writing {a.get('path','')}",
        "list_directory":   lambda a: f"\U0001f4c1 ls {a.get('path','~')}",
        "open_folder_gui":  lambda a: f"\U0001f4c1 open {a.get('path','~')}",
        "get_clipboard":    lambda a: "\U0001f4cb get clipboard",
        "set_clipboard":    lambda a: "\U0001f4cb set clipboard",
        "install_packages": lambda a: f"\U0001f4e6 pip install {' '.join(a.get('packages',[]))}",
        "web_browse":       lambda a: f"\U0001f310 browsing {a.get('url','')}",
        "web_search":       lambda a: f"\U0001f50d searching: {a.get('query','')}",
        "web_research":     lambda a: f"\U0001f52c researching: {a.get('topic','')[:40]}\u2026",
        "web_fill_form":    lambda a: f"\U0001f4dd filling form at {a.get('url','')}",
        "web_get_links":    lambda a: f"\U0001f517 getting links from {a.get('url','')}",
        "web_click":        lambda a: f"\U0001f5b1 clicking '{a.get('click_text','')}' on {a.get('url','')}",
        "read_pdf":         lambda a: f"\U0001f4c4 reading PDF {a.get('path','')}",
        "pdf_extract_tables": lambda a: f"\U0001f4ca extracting tables from {a.get('path','')}",
        "read_excel":       lambda a: f"\U0001f4d7 reading Excel {a.get('path','')}",
        "write_excel":      lambda a: f"\U0001f4d7 writing Excel {a.get('path','')}",
        "excel_update_cell": lambda a: f"\U0001f4d7 updating {a.get('cell','')} in {a.get('path','')}",
        "ocr_image":        lambda a: f"\U0001f524 OCR on {a.get('path','')}",
        "ocr_pdf":          lambda a: f"\U0001f524 OCR PDF {a.get('path','')}",
        "read_docx":        lambda a: f"\U0001f4dd reading Word {a.get('path','')}",
        "organize_files":   lambda a: f"\U0001f4c2 organizing {a.get('directory','')}",
        "find_files":       lambda a: f"\U0001f50e finding {a.get('pattern','')} in {a.get('directory','')}",
        "file_info":        lambda a: f"\u2139\ufe0f info: {a.get('path','')}",
        "email_check_inbox": lambda a: "\U0001f4e7 checking inbox\u2026",
        "email_read":        lambda a: f"\U0001f4e7 reading email {a.get('uid','')}",
        "email_send":        lambda a: f"\U0001f4e7 sending to {a.get('to','')}",
        "email_reply":       lambda a: f"\U0001f4e7 replying to {a.get('uid','')}",
        "email_search":      lambda a: f"\U0001f50d searching emails: {a.get('query','')}",
        "email_summarize":   lambda a: "\U0001f4e7 summarizing inbox\u2026",
        "git_status":        lambda a: f"\U0001f4e6 git status {a.get('repo_path','')}",
        "git_diff":          lambda a: f"\U0001f4e6 git diff {a.get('repo_path','')}",
        "git_log":           lambda a: f"\U0001f4e6 git log {a.get('repo_path','')}",
        "git_commit":        lambda a: f"\U0001f4e6 git commit: {a.get('message','')[:40]}",
        "git_branch":        lambda a: f"\U0001f4e6 git branch {a.get('action','list')}",
        "git_pull":          lambda a: f"\U0001f4e6 git pull {a.get('repo_path','')}",
        "git_push":          lambda a: f"\U0001f4e6 git push {a.get('repo_path','')}",
        "git_stash":         lambda a: f"\U0001f4e6 git stash {a.get('action','push')}",
        "run_tests":         lambda a: f"\U0001f9ea running tests in {a.get('path','.')}",
        "lint_code":         lambda a: f"\U0001f50d linting {a.get('path','')}",
        "find_in_codebase":  lambda a: f"\U0001f50e grep '{a.get('pattern','')}'",
        "analyze_codebase":  lambda a: f"\U0001f4ca analyzing {a.get('path','.')}",
        "db_query":          lambda a: f"\U0001f5c4 SQL: {a.get('query','')[:40]}",
        "check_disk_space":       lambda a: "\U0001f4be checking disk space\u2026",
        "check_memory_usage":     lambda a: "\U0001f9e0 checking memory\u2026",
        "check_gpu_health":       lambda a: "\U0001f3ae checking GPU health\u2026",
        "check_services":         lambda a: f"\U0001f527 checking services: {a.get('services','swarm-bot,ollama')}",
        "system_cleanup":         lambda a: f"\U0001f9f9 {'previewing' if a.get('dry_run', True) else 'running'} cleanup\u2026",
        "check_updates":          lambda a: "\U0001f4e6 checking for updates\u2026",
        "driver_status":          lambda a: "\U0001f527 checking drivers\u2026",
        "full_maintenance_check": lambda a: "\U0001f3e5 full health check\u2026",
    }
    fn = labels.get(name)
    return fn(args) if fn else f"\U0001f527 {name}()"


# ── Single-turn chat (existing behavior) ───────────────────────────────────

async def chat(
    task: str,
    agent_key: Optional[str] = None,
    thread_id: Optional[str] = None,
    image_b64: Optional[str] = None,
    show_thinking: bool = True,
    user_id: Optional[str] = None,
) -> tuple[str, str]:
    """Single-turn chat without computer tool use.

    Returns (response_text, model_used)
    """
    if agent_key is None:
        agent_key = detect_agent(task)

    chain = get_fallback_chain(agent_key)

    # ── Resource-aware Ollama gating ──────────────────────────────────────
    _local_skip_reason = ""
    if agent_key == "vision":
        if image_b64 is None:
            chain = [m for m in chain if not m.startswith("ollama_chat/")]
        else:
            try:
                from tools.resource_monitor import can_use_local_model
                _local_ok, _local_skip_reason = await can_use_local_model()
                if not _local_ok:
                    logger.info(
                        "Skipping local Ollama (resource constrained): %s",
                        _local_skip_reason,
                    )
                    chain = [m for m in chain if not m.startswith("ollama_chat/")]
            except Exception as _rm_err:
                logger.warning("resource_monitor import failed: %s — allowing local", _rm_err)

    system_prompt = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["general"])

    if _local_skip_reason:
        system_prompt += (
            f"\n\n[Note: local Ollama bypassed — {_local_skip_reason}. "
            "Using cloud vision instead.]"
        )

    # ── Inject conversation history ──────────────────────────────────────────────
    if user_id:
        try:
            from router import get_conversation_summary_prompt
            ctx = get_conversation_summary_prompt(user_id)
            if ctx:
                system_prompt += "\n\n" + ctx
        except Exception:
            pass

    # ── RecallMax: inject relevant memories ──────────────────────────────────────
    if user_id:
        try:
            from tools.memory import search_memories
            from tools.recallmax import build_memory_context
            memories = await search_memories(user_id=int(user_id), query=task, limit=6)
            mem_ctx = build_memory_context(memories, query=task)
            if mem_ctx:
                system_prompt = mem_ctx + "\n" + system_prompt
        except Exception as _mem_err:
            logger.debug("recallmax memory injection failed: %s", _mem_err)

    try:
        from tools.persistence import get_instinct_context
        instinct_block = await get_instinct_context(max_tokens=300)
        if instinct_block:
            system_prompt += "\n\n" + instinct_block
    except Exception:
        pass

    # ── Skill injection (budget raised to 6000 chars) ──────────────────────────
    try:
        from tools.skill_loader import get_skills_for_agent
        skills_block = get_skills_for_agent(agent_key, max_chars=6000)
        if skills_block:
            system_prompt += "\n\n" + skills_block
    except Exception:
        pass

    if agent_key not in ("computer", "vision"):
        system_prompt += (
            "\n\nYou are in CHAT-ONLY mode — no tools, no computer access right now. "
            "Answer from your knowledge. Do NOT pretend to run commands, check files, "
            "or access the desktop. Do NOT fabricate file contents or command output. "
            "If the task requires computer access, tell Bas to use /do <task>. "
            "For Legion status/config questions, suggest: /models, /keys, /stats, /gpu."
        )

    if image_b64:
        user_content: Any = [
            {"type": "text", "text": task},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
    else:
        user_content = task

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]

    _skip_cache = image_b64 is not None or show_thinking or agent_key == "vision"
    if not _skip_cache:
        try:
            from tools.persistence import cache_get
            _cache_key = hashlib.sha256(
                f"{agent_key}:{task}:{chain[0]}".encode()
            ).hexdigest()
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
        if model.startswith("ollama_chat/") and agent_key != "vision":
            continue

        try:
            logger.info("Trying: %s (agent=%s)", model, agent_key)
            _t0 = time.time()
            await hooks.emit("pre_llm_call", {
                "agent": agent_key, "model": model, "task": task[:200],
            })
            resp = await _call_model(model, messages)
            raw = (resp.choices[0].message.content or "").strip()
            _elapsed_ms = int((time.time() - _t0) * 1000)

            _usage = getattr(resp, "usage", None)
            _tin = getattr(_usage, "prompt_tokens", 0) if _usage else 0
            _tout = getattr(_usage, "completion_tokens", 0) if _usage else 0

            await hooks.emit("post_llm_call", {
                "agent": agent_key, "model": model,
                "tokens_in": _tin, "tokens_out": _tout,
                "duration_ms": _elapsed_ms, "success": True,
            })

            thinking, answer = _strip_think_tags(raw, return_thinking=True)
            if thinking and show_thinking:
                result = f"<i>\U0001f4ad {thinking[:400]}{'\u2026' if len(thinking) > 400 else ''}</i>\n\n{answer}"
            else:
                result = answer if thinking else raw

            if thread_id:
                add_to_thread(thread_id, agent_key, task, result)

            if user_id:
                try:
                    from router import add_to_conversation
                    add_to_conversation(user_id, "user", task)
                    add_to_conversation(user_id, "assistant", result)
                except Exception:
                    pass

                # RecallMax: store turn if worth persisting
                try:
                    from tools.recallmax import should_store
                    from tools.memory import store_memory
                    if should_store(task):
                        await store_memory(
                            user_id=int(user_id),
                            content=task,
                            source="chat",
                        )
                except Exception:
                    pass

            if _cache_key:
                try:
                    from tools.persistence import cache_set
                    await cache_set(_cache_key, result, agent_key, model, _tin + _tout)
                except Exception:
                    pass

            logger.info("Success: %s", model)
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
        f"All models exhausted for '{agent_key}'.\n"
        f"Last error: {last_error}\n"
        "Run /keys to check API keys."
    )


# ── Screenshot utilities ──────────────────────────────────────────────────
if _COMPUTER_AVAILABLE:
    take_screenshot = computer_agent.take_screenshot
else:
    async def take_screenshot() -> str:  # type: ignore
        return ""


async def analyze_screenshot(
    image_path: str,
    question: str = "Describe what you see on screen."
) -> tuple[str, str]:
    """Analyze a screenshot with vision model.

    Resource-aware: checks RAM + VRAM via resource_monitor before trying
    Ollama gemma3:12b. If constrained, goes straight to cloud vision.
    Falls back to Groq cloud if Ollama fails for any reason.

    Returns (analysis_text, model_used)
    """
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
    except Exception as _rm_err:
        logger.warning("resource_monitor unavailable: %s — allowing local", _rm_err)

    if not _skip_local:
        try:
            resp = await _call_model(
                "ollama_chat/gemma3:12b",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_question},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ],
                }],
                max_tokens=1024,
            )
            result = (resp.choices[0].message.content or "").strip()
            logger.info("Screenshot analyzed locally via Ollama")
            return result, "ollama/gemma3:12b \U0001f512 local"
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
                {"role": "user", "content": [
                    {"type": "text", "text": vision_question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]},
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
            f"\u2022 Local: {'bypassed — ' + _skip_reason if _skip_local else 'run ollama pull gemma3:12b'}\n"
            f"\u2022 Cloud: {e}"
        )


# ── Shell execution ──────────────────────────────────────────────────────

async def run_shell_command(cmd: str, timeout: int = 30) -> str:
    """Alias for computer_agent.run_shell used by main.py."""
    if not _COMPUTER_AVAILABLE:
        return "computer_agent not available"
    return await computer_agent.run_shell(cmd, timeout=timeout)


# ── Output utilities ──────────────────────────────────────────────────────

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
            if remaining_space > 0:
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
        "CEREBRAS_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
        "OPENROUTER_API_KEY", "ZAI_API_KEY", "HF_TOKEN",
    ]
    return {k: bool(os.getenv(k)) for k in keys}
