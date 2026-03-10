"""LLM client — cloud-first with agentic tool-calling loop.

Two execution modes:
  1. chat()        — Single-turn Q&A for text responses
  2. agent_loop()  — Multi-turn agentic loop with real computer tool use

Fallback policy:
  vision:    Ollama gemma3:12b (local) → Groq Llama-4-Scout (cloud)
  all other: cloud chain (ZAI → Groq → Cerebras → Gemini → OpenRouter)
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

import litellm
from litellm import acompletion

import computer_agent
from computer_agent import TOOL_DEFINITIONS, execute_tool
from router import detect_agent, get_fallback_chain, add_to_thread

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True

# ── Coworker persona ─────────────────────────────────────────────────────────

_PERSONA = (
    "You're Legion — Bas's AI coworker on his Linux workstation "
    "(RTX 3060 12GB, Ubuntu, ~/swarm-bot, Python 3.13, PyTorch/WorkerNet). "
    "You have FULL access to his desktop: you can run shell commands, click things, "
    "open apps, read files, take screenshots — anything. "
    "When Bas asks you to check something, DO IT immediately using your tools. "
    "Don't say what you WOULD do — just do it. "
    "Talk like a sharp senior dev: direct, casual, no corporate speak. "
    "Say things like 'ok let me check...', 'yeah found it...', 'done — here's what I see:'. "
    "Match Bas's language: Indonesian if he writes Indonesian, English if English, mixing is fine. "
    "Never say 'As an AI...' or 'I don't have access...' — you DO have access, use your tools."
)

SYSTEM_PROMPTS: dict[str, str] = {
    "computer": (
        f"{_PERSONA}\n\n"
        "TOOL CALLING RULES:\n"
        "- Always call tools using the tools parameter in the API call, never in message text\n"
        "- Never write function calls as text in your response\n"
        "- When you need to use a tool, output ONLY the tool call, no surrounding text\n"
        "- Tool arguments must be valid JSON objects\n\n"
        "You are in COMPUTER USE mode. You have tools to control the desktop.\n"
        "For ANY task involving the computer:\n"
        "1. Use shell_execute to run commands and get real output\n"
        "2. Use take_screenshot to see what's on screen\n"
        "3. Use mouse_click + keyboard_type to interact with GUI\n"
        "4. Use open_app/open_url to launch things\n"
        "Always verify results with shell_execute or take_screenshot. "
        "If one approach fails, try another. Be persistent."
    ),
    "vision": (
        f"{_PERSONA}\n\n"
        "You're analyzing a screenshot from Bas's desktop. "
        "Be specific: what apps are open, what's in each window, any errors/warnings, "
        "exact text you can read. Then suggest the most useful next action."
    ),
    "coding": (
        f"{_PERSONA}\n\n"
        "You're the coding agent. Write clean, working code. "
        "For shell tasks give exact commands. Explain each block in one line. "
        "Prefer minimal solutions. Always handle errors. "
        "If you'd do it differently in prod, say so briefly."
    ),
    "debug": (
        f"{_PERSONA}\n\n"
        "Debug mode: 1. Root cause in ONE sentence. "
        "2. Minimal fix (code/command). 3. Why it failed. 4. Prevention. "
        "No fluff. Show reasoning, then fix."
    ),
    "math": (
        f"{_PERSONA}\n\n"
        "Show derivations step by step. For tensors show shapes at each step. "
        "For gradients show chain rule. Verify numerically when it makes sense."
    ),
    "architect": (
        f"{_PERSONA}\n\n"
        "Focus on structure, data flow, component boundaries, failure modes. "
        "Use ASCII diagrams when helpful. Give concrete trade-offs."
    ),
    "analyst": (
        f"{_PERSONA}\n\n"
        "Extract real insights. Write Python for visualisations when relevant. "
        "For training runs: loss curves, grad norms, GPU util, throughput. "
        "Flag anomalies: NaN/Inf, loss spikes >2x, GPU util <50%."
    ),
    "general": (
        f"{_PERSONA}\n\n"
        "Answer directly. For technical stuff give exact commands. "
        "For complex topics: brief structure then answer. "
        "If a task needs computer access, say so — Bas can use /do for that."
    ),
}

# ── Rate limit tracking ──────────────────────────────────────────────────────
_rate_limited: dict[str, float] = {}
_COOLDOWN = 60


def _is_rate_limited(model: str) -> bool:
    provider = model.split("/")[0]
    return provider in _rate_limited and (time.time() - _rate_limited[provider]) < _COOLDOWN


def _mark_rate_limited(model: str) -> None:
    provider = model.split("/")[0]
    _rate_limited[provider] = time.time()
    logger.warning("Rate limited: %s (cooling %ds)", provider, _COOLDOWN)


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


def _strip_think_tags(text: str) -> tuple[str, str]:
    """Strip <think>...</think> blocks. Returns (thinking_text, clean_answer)."""
    think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else ""
    answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return thinking, answer


def _parse_groq_xml_tool_call(error_str: str) -> tuple[str, dict] | None:
    """Parse Groq's malformed XML tool calls from BadRequestError messages.

    Groq Llama models sometimes emit <function=name{args}></function> instead of
    proper tool_calls. This extracts tool name + args from the error so we can
    execute the tool and continue the agentic loop.
    """
    s = str(error_str)
    for pat in [
        r'function=(\w+)(\{[^}]*\})',       # <function=name{args}>
        r"tool '(\w+)(\{[^}]*\})'",          # attempted to call tool 'name{args}'
    ]:
        m = re.search(pat, s)
        if m:
            name = m.group(1)
            args_str = m.group(2).replace('\\"', '"')
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}
            return name, args
    return None


# ── Core model call ──────────────────────────────────────────────────────────

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

    # Provider-specific config
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


# ── Context compaction ───────────────────────────────────────────────────────

def _compact_messages(messages: list[dict], keep_recent: int = 6) -> list[dict]:
    """Summarize older messages to reduce context size.

    Keeps: system prompt + last `keep_recent` messages.
    Summarizes everything in between into a single context message.
    """
    if len(messages) <= keep_recent + 2:
        return messages

    system = messages[0]  # Always keep system prompt
    recent = messages[-keep_recent:]  # Keep last N messages
    middle = messages[1:-keep_recent]  # Summarize these

    # Build a compact summary of middle messages
    summary_parts = []
    for m in middle:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant" and m.get("tool_calls"):
            tool_names = [tc.get("function", {}).get("name", "?")
                         for tc in m.get("tool_calls", [])]
            summary_parts.append(f"Called tools: {', '.join(tool_names)}")
        elif role == "tool":
            # Truncate long tool results
            truncated = content[:150] + "…" if len(content) > 150 else content
            summary_parts.append(f"Tool result: {truncated}")
        elif content:
            truncated = content[:200] + "…" if len(content) > 200 else content
            summary_parts.append(f"{role}: {truncated}")

    summary = "\n".join(summary_parts)
    compact_msg = {
        "role": "user",
        "content": (
            f"[Context from {len(middle)} previous steps, compacted to save space:]\n"
            f"{summary}\n\n"
            "[Continue with the task based on the above context and recent messages.]"
        ),
    }

    logger.info("Compacted %d messages → 1 summary", len(middle))
    return [system, compact_msg] + recent


# ── Agentic tool-calling loop ─────────────────────────────────────────────────

# Fallback chain for the agentic loop (must support function calling)
_AGENT_CHAIN = [
    "groq/llama-3.3-70b-versatile",
    "cerebras/qwen-3-235b-a22b",
    "gemini/gemini-2.0-flash",
    "openrouter/meta-llama/llama-3.3-70b-instruct:free",
]

# Callbacks: progress_cb(text) sends status to Telegram
# photo_cb(path) sends screenshot to Telegram
ProgressCb = Optional[Callable[[str], Coroutine[Any, Any, None]]]
PhotoCb = Optional[Callable[[str], Coroutine[Any, Any, None]]]


async def agent_loop(
    task: str,
    progress_cb: ProgressCb = None,
    photo_cb: PhotoCb = None,
    max_iterations: int = 20,
    thread_id: Optional[str] = None,
) -> tuple[str, str]:
    """Agentic loop: LLM calls computer tools until the task is complete.

    The LLM gets access to all TOOL_DEFINITIONS. On each iteration:
    1. LLM decides what to do (or gives final answer)
    2. If tool call: execute it, feed result back
    3. If screenshot: also send the image to Telegram via photo_cb
    4. Repeat until LLM gives a text-only final answer

    Returns (final_response, model_used)
    """
    # Build fallback chain — skip rate-limited models
    chain = [m for m in _AGENT_CHAIN if not _is_rate_limited(m)]
    if not chain:
        chain = list(_AGENT_CHAIN)
    model = chain[0]
    chain_idx = 0

    def _advance_model() -> bool:
        """Switch to next available model in chain. Returns False if exhausted."""
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
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]

    steps_taken: list[str] = []

    for iteration in range(max_iterations):
        # Context compaction: summarize old messages to stay within limits
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
            return "rate limited on all providers — try again in a minute", model

        except litellm.BadRequestError as e:
            error_str = str(e)
            # Groq XML tool calls: model outputs <function=name{args}> instead of tool_calls
            if "tool_use_failed" in error_str or "failed_generation" in error_str:
                parsed = _parse_groq_xml_tool_call(error_str)
                if parsed:
                    tool_name, args = parsed
                    logger.info("Recovered XML tool call: %s(%s)", tool_name, list(args.keys()))
                    if progress_cb:
                        await progress_cb(_tool_label(tool_name, args))

                    try:
                        result = await execute_tool(tool_name, args)
                    except Exception as te:
                        result = f"tool error: {te}"
                    result = str(result) if result is not None else "tool returned no output"

                    # Screenshot special handling
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

                    steps_taken.append(f"{tool_name} → {result[:80]}...")

                    # Build synthetic tool call messages for conversation continuity
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

            # Non-recoverable BadRequest → try next model
            logger.error("agent_loop BadRequest: %s", e)
            if _advance_model():
                continue
            return f"model error: {e}", model

        except litellm.AuthenticationError:
            logger.error("agent_loop auth error on %s — trying next", model)
            if _advance_model():
                continue
            return "auth error on all providers — check /keys", model

        except Exception as e:
            logger.error("agent_loop error: %s", e)
            return f"error: {e}", model

        # Guard against None/empty response
        if response is None or not hasattr(response, 'choices') or not response.choices:
            logger.warning("agent_loop: empty response, breaking")
            break
        msg = response.choices[0].message
        if msg is None:
            logger.warning("agent_loop: None message, breaking")
            break

        # No tool calls → LLM gave final answer
        if not msg.tool_calls:
            answer = (msg.content or "").strip()
            thinking, clean = _strip_think_tags(answer)
            if thread_id:
                add_to_thread(thread_id, "computer", task, clean)
            return clean or answer, model

        # Append assistant message with tool calls
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

        # Execute each tool call
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            # Progress update to Telegram
            if progress_cb:
                step_label = _tool_label(tool_name, args)
                await progress_cb(step_label)

            logger.info("Tool call: %s(%s)", tool_name, list(args.keys()))

            # Execute the tool
            try:
                result = await execute_tool(tool_name, args)
            except Exception as e:
                result = f"tool error: {e}"
            # Coerce to string — tool executors can return None
            result = str(result) if result is not None else "tool returned no output"

            # Special handling: screenshot → send image to Telegram, analyze for LLM
            if tool_name == "take_screenshot":
                screenshot_path = result  # returns file path as string
                if screenshot_path and screenshot_path != "tool returned no output" and Path(screenshot_path).exists():
                    # Send image to Telegram user
                    if photo_cb:
                        await photo_cb(screenshot_path)
                    # Analyze for LLM (gives it a text description of what's on screen)
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

            steps_taken.append(f"{tool_name} → {tool_result_text[:80]}...")

            # Feed result back to LLM
            messages.append({
                "role": "tool",
                "content": tool_result_text,
                "tool_call_id": tc.id,
            })

    # Exceeded max iterations
    summary = "\n".join(f"  • {s}" for s in steps_taken[-5:])
    return f"completed {max_iterations} steps:\n{summary}", model


def _tool_label(name: str, args: dict) -> str:
    """Human-friendly progress label for a tool call."""
    labels = {
        "shell_execute":    lambda a: f"$ {a.get('command', '')[:60]}",
        "take_screenshot":  lambda a: "📸 grabbing screen…",
        "mouse_click":      lambda a: f"🖱 click ({a.get('x')}, {a.get('y')}) [{a.get('button','left')}]",
        "keyboard_type":    lambda a: f"⌨️ typing: {a.get('text','')[:30]}…",
        "key_press":        lambda a: f"⌨️ {a.get('keys','')}",
        "open_app":         lambda a: f"📂 opening {a.get('app_name','')}",
        "open_url":         lambda a: f"🌐 {a.get('url','')}",
        "browser_navigate": lambda a: f"🌐 → {a.get('url','')}",
        "new_browser_tab":  lambda a: f"🗂 new tab: {a.get('url','')}",
        "focus_window":     lambda a: f"🪟 focus: {a.get('pattern','')}",
        "list_windows":     lambda a: "🪟 listing windows…",
        "scroll_at":        lambda a: f"↕ scroll {a.get('direction','down')} ×{a.get('amount',3)}",
        "read_file":        lambda a: f"📖 reading {a.get('path','')}",
        "write_file":       lambda a: f"✏️ writing {a.get('path','')}",
        "list_directory":   lambda a: f"📁 ls {a.get('path','~')}",
        "open_folder_gui":  lambda a: f"📁 open {a.get('path','~')}",
        "get_clipboard":    lambda a: "📋 get clipboard",
        "set_clipboard":    lambda a: "📋 set clipboard",
        "install_packages": lambda a: f"📦 pip install {' '.join(a.get('packages',[]))}",
        # Web browsing
        "web_browse":       lambda a: f"🌐 browsing {a.get('url','')}",
        "web_search":       lambda a: f"🔍 searching: {a.get('query','')}",
        "web_research":     lambda a: f"🔬 researching: {a.get('topic','')[:40]}…",
        "web_fill_form":    lambda a: f"📝 filling form at {a.get('url','')}",
        "web_get_links":    lambda a: f"🔗 getting links from {a.get('url','')}",
        "web_click":        lambda a: f"🖱 clicking '{a.get('click_text','')}' on {a.get('url','')}",
        # Document processing
        "read_pdf":         lambda a: f"📄 reading PDF {a.get('path','')}",
        "pdf_extract_tables": lambda a: f"📊 extracting tables from {a.get('path','')}",
        "read_excel":       lambda a: f"📗 reading Excel {a.get('path','')}",
        "write_excel":      lambda a: f"📗 writing Excel {a.get('path','')}",
        "excel_update_cell": lambda a: f"📗 updating {a.get('cell','')} in {a.get('path','')}",
        "ocr_image":        lambda a: f"🔤 OCR on {a.get('path','')}",
        "ocr_pdf":          lambda a: f"🔤 OCR PDF {a.get('path','')}",
        "read_docx":        lambda a: f"📝 reading Word {a.get('path','')}",
        "organize_files":   lambda a: f"📂 organizing {a.get('directory','')}",
        "find_files":       lambda a: f"🔎 finding {a.get('pattern','')} in {a.get('directory','')}",
        "file_info":        lambda a: f"ℹ️ info: {a.get('path','')}",
        # Email
        "email_check_inbox": lambda a: "📧 checking inbox…",
        "email_read":        lambda a: f"📧 reading email {a.get('uid','')}",
        "email_send":        lambda a: f"📧 sending to {a.get('to','')}",
        "email_reply":       lambda a: f"📧 replying to {a.get('uid','')}",
        "email_search":      lambda a: f"🔍 searching emails: {a.get('query','')}",
        "email_summarize":   lambda a: "📧 summarizing inbox…",
        # Git operations
        "git_status":        lambda a: f"📦 git status {a.get('repo_path','')}",
        "git_diff":          lambda a: f"📦 git diff {a.get('repo_path','')}",
        "git_log":           lambda a: f"📦 git log {a.get('repo_path','')}",
        "git_commit":        lambda a: f"📦 git commit: {a.get('message','')[:40]}",
        "git_branch":        lambda a: f"📦 git branch {a.get('action','list')}",
        "git_pull":          lambda a: f"📦 git pull {a.get('repo_path','')}",
        "git_push":          lambda a: f"📦 git push {a.get('repo_path','')}",
        "git_stash":         lambda a: f"📦 git stash {a.get('action','push')}",
        # Dev tools
        "run_tests":         lambda a: f"🧪 running tests in {a.get('path','.')}",
        "lint_code":         lambda a: f"🔍 linting {a.get('path','')}",
        "format_code":       lambda a: f"✨ formatting {a.get('path','')}",
        "find_in_codebase":  lambda a: f"🔎 grep '{a.get('pattern','')}'",
        "analyze_codebase":  lambda a: f"📊 analyzing {a.get('path','.')}",
        "db_query":          lambda a: f"🗄 SQL: {a.get('query','')[:40]}",
        # Orchestration
        "parallel_agents":   lambda a: f"🔄 swarm: {a.get('task','')[:40]}",
        # System maintenance
        "check_disk_space":      lambda a: "💾 checking disk space…",
        "check_memory_usage":    lambda a: "🧠 checking memory…",
        "check_gpu_health":      lambda a: "🎮 checking GPU health…",
        "check_services":        lambda a: f"🔧 checking services: {a.get('services','swarm-bot,ollama')}",
        "system_cleanup":        lambda a: f"🧹 {'previewing' if a.get('dry_run', True) else 'running'} cleanup…",
        "check_updates":         lambda a: "📦 checking for updates…",
        "driver_status":         lambda a: "🔧 checking drivers…",
        "full_maintenance_check": lambda a: "🏥 full health check…",
    }
    fn = labels.get(name)
    return fn(args) if fn else f"🔧 {name}()"


# ── Single-turn chat (existing behavior) ─────────────────────────────────────

async def chat(
    task: str,
    agent_key: Optional[str] = None,
    thread_id: Optional[str] = None,
    image_b64: Optional[str] = None,
    show_thinking: bool = False,
) -> tuple[str, str]:
    """Single-turn chat without computer tool use.

    Returns (response_text, model_used)
    """
    if agent_key is None:
        agent_key = detect_agent(task)

    chain = get_fallback_chain(agent_key)
    if agent_key == "vision" and image_b64 is None:
        chain = [m for m in chain if not m.startswith("ollama_chat/")]

    system_prompt = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["general"])

    # In chat mode (no tools), prevent hallucination of computer access
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

    last_error: Exception = Exception("No models available")

    for model in chain:
        if _is_rate_limited(model):
            continue
        if model.startswith("ollama_chat/") and agent_key != "vision":
            continue

        try:
            logger.info("Trying: %s (agent=%s)", model, agent_key)
            resp = await _call_model(model, messages)
            raw = (resp.choices[0].message.content or "").strip()

            thinking, answer = _strip_think_tags(raw)
            if thinking and show_thinking:
                result = f"<i>💭 {thinking[:400]}{'…' if len(thinking) > 400 else ''}</i>\n\n{answer}"
            else:
                result = answer if thinking else raw

            if thread_id:
                add_to_thread(thread_id, agent_key, task, result)

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


# ── Screenshot utilities ──────────────────────────────────────────────────────

async def take_screenshot() -> Optional[str]:
    """Wrapper that delegates to computer_agent.take_screenshot()."""
    return await computer_agent.take_screenshot()


async def analyze_screenshot(
    image_path: str,
    question: str = "Describe what you see on screen."
) -> tuple[str, str]:
    """Analyze a screenshot image with vision model.

    Tries Ollama gemma3:12b first (local/private), falls back to Groq cloud.
    Returns (analysis_text, model_used)
    """
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    vision_question = question

    # Try local Ollama first (image stays on machine)
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
        return result, "ollama/gemma3:12b 🔒 local"
    except Exception as e:
        logger.warning("Ollama vision failed: %s → trying Groq", e)

    # Fall back to Groq Llama-4-Scout (cloud vision)
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        raise RuntimeError("No GROQ_API_KEY and Ollama vision failed")

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
        logger.info("Screenshot analyzed via Groq cloud vision")
        return result, "groq/llama-4-scout"
    except Exception as e:
        raise RuntimeError(
            f"Screenshot analysis failed.\n"
            f"• Local: run 'ollama pull gemma3:12b' to enable local vision\n"
            f"• Cloud: {e}"
        )


# ── Shell execution ───────────────────────────────────────────────────────────

async def run_shell_command(cmd: str, timeout: int = 30) -> str:
    """Alias for computer_agent.run_shell used by main.py."""
    return await computer_agent.run_shell(cmd, timeout=timeout)


# ── Output utilities ──────────────────────────────────────────────────────────

def chunk_output(text: str, max_length: int = 4000) -> list[str]:
    """Split text into Telegram-safe chunks (4096 char limit)."""
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
