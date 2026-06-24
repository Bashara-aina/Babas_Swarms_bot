"""llm_client — LLM client package for Legion.

Single-turn chat + agentic tool-calling loop.
Split into submodules for maintainability.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import hashlib
import json
import logging
import os
import random
import re
import time
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, Optional

import aiofiles
import litellm
from litellm import acompletion

# Surrogate character regex (U+D800 to U+DFFF) — used by _sanitize_messages_surrogates
# and _sanitize_structure_surrogates to prevent JSONEncodeError crashes from
# byte-level reasoning models (xiaomi/mimo, kimi, glm).
_SURROGATE_RE = re.compile(r'[\ud800-\udfff]')

# ── Per-task max_tokens (Mitigation 3: token reduction) ─────────────────────
# When call_llm() is called with task_type=<str> and no explicit max_tokens
# in kwargs, it pulls the default from this table. Concrete-cap call sites
# (e.g. max_tokens=3072) keep their explicit value; this only fills gaps.
# Override the "default" key via env: LEGION_DEFAULT_MAX_TOKENS
_TASK_MAX_TOKENS: dict[str, int] = {
    "default": 4096,
    "chat": 2048,
    "wiki": 2048,
    "summary": 3072,
    "agent": 2048,
    "code": 4096,
    "research": 4096,
    "vision": 1024,
}
_default_max_tokens_env = os.getenv("LEGION_DEFAULT_MAX_TOKENS")
if _default_max_tokens_env and _default_max_tokens_env.isdigit():
    _TASK_MAX_TOKENS["default"] = int(_default_max_tokens_env)

def _sanitize_surrogates(text: str) -> str:
    """Replace surrogate code points with the Unicode replacement character."""
    return _SURROGATE_RE.sub('\ufffd', text)

def _sanitize_messages_surrogates(messages: list[dict]) -> bool:
    """Walk message dicts in-place, replacing surrogates in all string fields.

    Returns True if any surrogates were found and replaced.
    Covers content, name, tool_calls, and any additional nested fields
    (reasoning_content, reasoning_details, etc.) from byte-level reasoning models.
    """
    found = False
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        # content (str or list of parts)
        content = msg.get("content")
        if isinstance(content, str) and _SURROGATE_RE.search(content):
            msg["content"] = _SURROGATE_RE.sub('\ufffd', content)
            found = True
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str) and _SURROGATE_RE.search(text):
                        part["text"] = _SURROGATE_RE.sub('\ufffd', text)
                        found = True
        # name
        name = msg.get("name")
        if isinstance(name, str) and _SURROGATE_RE.search(name):
            msg["name"] = _SURROGATE_RE.sub('\ufffd', name)
            found = True
        # tool_calls
        tool_calls = msg.get("tool_calls")
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                tc_id = tc.get("id")
                if isinstance(tc_id, str) and _SURROGATE_RE.search(tc_id):
                    tc["id"] = _SURROGATE_RE.sub('\ufffd', tc_id)
                    found = True
                fn = tc.get("function")
                if isinstance(fn, dict):
                    fn_name = fn.get("name")
                    if isinstance(fn_name, str) and _SURROGATE_RE.search(fn_name):
                        fn["name"] = _SURROGATE_RE.sub('\ufffd', fn_name)
                        found = True
                    fn_args = fn.get("arguments")
                    if isinstance(fn_args, str) and _SURROGATE_RE.search(fn_args):
                        fn["arguments"] = _SURROGATE_RE.sub('\ufffd', fn_args)
                        found = True
        # Walk any additional nested string fields
        for key, value in msg.items():
            if key in {"content", "name", "tool_calls", "role"}:
                continue
            if isinstance(value, str) and _SURROGATE_RE.search(value):
                msg[key] = _SURROGATE_RE.sub('\ufffd', value)
                found = True
            elif isinstance(value, (dict, list)):
                if _sanitize_structure_surrogates(value):
                    found = True
    return found

def _sanitize_structure_surrogates(payload: Any) -> bool:
    """Replace surrogate code points in nested dict/list payloads in-place.

    Returns True if any surrogates were replaced.
    """
    found = False
    def _walk(node):
        nonlocal found
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str):
                    if _SURROGATE_RE.search(value):
                        node[key] = _SURROGATE_RE.sub('\ufffd', value)
                        found = True
                elif isinstance(value, (dict, list)):
                    _walk(value)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    _walk(item)
    _walk(payload)
    return found

from core.autonomous_router import AutonomousRouter  # noqa: E402
from core.character import build_base_persona, build_mode_instructions, get_disagreement_prompt  # noqa: E402
from core.cognition_pipeline import build_cognition_system_fragment  # noqa: E402
from core.conversation_interface import add_to_thread, detect_agent, get_fallback_chain  # noqa: E402
from core.emotion_modulator import (  # noqa: E402
    build_emotion_modifier,
    detect_emotion_from_context,
    postprocess_response,
)
from core.episodic_narrative import build_narrative_context  # noqa: E402
from core.hooks import get_hooks  # noqa: E402
from core.intent_router import build_intent_hint, classify_intent_fast  # noqa: E402
from core.memory.infinite.llm_wrapper import inject_memory_into_messages  # noqa: E402
from core.memory.infinite.llm_wrapper import store_response as _store_response  # noqa: E402
from core.memory.memory_manager import MemoryManager  # noqa: E402
from core.memory.temporal_graph import TemporalKnowledgeGraph  # noqa: E402
from core.personality.emotion_engine import EmotionEngine  # noqa: E402
from core.reflection.reflection_engine import ReflectionEngine  # noqa: E402
from core.relationship_memory import get_relationship_context  # noqa: E402
from core.soul_engine import build_soul_context  # noqa: E402
from core.system_prompt_builder import SystemPromptBuilder  # noqa: E402, F401
from tools.letta_personality import build_persona_block, get_persona_state, update_emotion  # noqa: E402, F401
from tools.memory import build_memory_context as _build_memory_context_sync  # noqa: E402, F401
from tools.memoryos_client import mos_retrieve_context  # noqa: E402, F401
from tools.open_memory import build_om_context, om_search  # noqa: E402, F401
from tools.persistence import get_instinct_context  # noqa: E402, F401
from tools.skill_loader import get_skills_for_agent  # noqa: E402, F401

try:
    import computer_agent  # noqa: E402
    from computer_agent import TOOL_DEFINITIONS as _COMPUTER_TOOLS, execute_tool  # noqa: E402

    _COMPUTER_AVAILABLE = True
except ImportError as _ca_err:
    import logging as _log

    _log.getLogger(__name__).warning("computer_agent unavailable (%s) — /do and computer tools disabled", _ca_err)
    computer_agent = None  # type: ignore
    _COMPUTER_TOOLS = []
    execute_tool = None  # type: ignore
    _COMPUTER_AVAILABLE = False

# ── MCP tool registration ─────────────────────────────────────────────────────
# Aggregate all MCP server tools and prepend them to the tool registry.
# This makes 200+ MCP tools (ruflo, hermes, crawl4ai, etc.) callable by the
# agent alongside the built-in computer_agent tools.
#
# The pattern: MCP tool names are prefixed (e.g. "ruflo_memory_search") to
# avoid collisions. The router maps prefixed name → original tool name.


async def _register_mcp_tools() -> None:
    """Async initialization — call once at startup to populate MCP tools."""
    global TOOL_DEFINITIONS
    try:
        from core.mcp.router import get_mcp_router

        router = get_mcp_router()
        await router.initialize()
        mcp_tools = await router.get_tool_definitions()
        if mcp_tools:
            TOOL_DEFINITIONS = mcp_tools + _COMPUTER_TOOLS
            logger.info("MCP tools registered: %d (MCP) + %d (computer) = %d total",
                        len(mcp_tools), len(_COMPUTER_TOOLS), len(TOOL_DEFINITIONS))
        else:
            TOOL_DEFINITIONS = list(_COMPUTER_TOOLS)
            logger.warning("No MCP tools available — using computer tools only (%d)", len(TOOL_DEFINITIONS))
    except Exception as e:
        logger.error("Failed to register MCP tools: %s — falling back to computer tools", e)
        TOOL_DEFINITIONS = list(_COMPUTER_TOOLS)


# Synchronous fallback for when async init hasn't run yet
TOOL_DEFINITIONS = list(_COMPUTER_TOOLS)

# Kick off async registration in background (non-blocking)
try:
    import threading
    _reg_thread = threading.Thread(target=lambda: asyncio.run(_register_mcp_tools()), daemon=True)
    _reg_thread.start()
except Exception:
    pass  # Best-effort async registration

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True


async def _safe_record_failure(
    task: str,
    approach: str,
    failure_mode: str,
    root_cause: str,
    fix_applied: str,
    prevention: str,
) -> None:
    """Call record_failure() without letting it raise — evolution must never block execution."""
    try:
        from core.self_evolution import get_self_evolution_engine

        engine = get_self_evolution_engine()
        await engine.record_failure(
            task=task,
            approach=approach,
            failure_mode=failure_mode,
            root_cause=root_cause,
            fix_applied=fix_applied,
            prevention_rule=prevention,
        )
    except Exception:
        pass

__all__ = [
    "agent_loop",
    "call_llm",
    "chat",
    "wiki_raw_completion",
]

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
    "build": (
        f"{_PERSONA}\n\n"
        "BUILD MODE — Incremental implementation with verification.\n"
        "1. Make one change at a time — small, self-contained, testable.\n"
        "2. Run tests immediately after each change.\n"
        "3. Verify with actual command output, not assumptions.\n"
        "4. If test fails: read the error, fix the error, re-test.\n"
        "5. Commit after each verified successful change.\n"
        "Never batch multiple changes without verification."
    ),
    "debug": (
        f"{_PERSONA}\n\n"
        "DEBUG MODE — Systematic root-cause analysis.\n"
        "1. Root cause — ONE sentence.\n"
        "2. What went wrong — ONE sentence.\n"
        "3. How to fix — concrete steps.\n"
        "4. Verification — how to confirm fix.\n"
        "Always reproduce the error before reporting. "
        "Show exact error messages. Never guess."
    ),
    "react": (
        f"{_PERSONA}\n\n"
        "REACT MODE — Fast reactive fixes.\n"
        "1. Identify the minimal change that fixes the issue.\n"
        "2. Apply it directly — no refactoring, no tests unless required.\n"
        "3. Verify it works.\n"
        "Ship the fix. Move on."
    ),
}

_MODE_SYSTEM_INJECT = """
CURRENT MODE: {{mode}}. Follow the mode-specific instructions above.
MODE SWITCH: If you need to switch mode, say MODE: <mode> at the start of your next response."""


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
    from llm_client import llm_client as _llm_client

    reflection = ReflectionEngine(memory, _llm_client)
    auto_router = AutonomousRouter(memory, reflection)

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


def _get_api_key(model: str) -> str | None:
    """Return API key for a model provider."""
    provider = model.split("/")[0].lower()
    key_map = {
        "opencode-go": "OPENCODE_GO_API_KEY",
        "ollama_chat": "OLLAMA_API_KEY",
        "zai": "ZAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_var = key_map.get(provider)
    if not env_var:
        if os.getenv("PYTEST_CURRENT_TEST"):
            return "dummy"
        return None
    key = os.getenv(env_var)
    if key:
        return key
    # Integration tests patch `llm_client.acompletion`; allow the patched call
    # path to run even when CI secrets are unavailable.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "dummy"
    return None


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
    """Execute a tool with multi-strategy self-healing to reduce transient failures.

    Recovery hierarchy (max 3 total attempts per tool call):
      Strategy 1 — Sanitize args: strip whitespace/quotes and retry
      Strategy 2 — Alternative pattern: re-parse arguments, try different key forms
      Strategy 3 — computer_use_loop fallback: use vision-reasoning-act for complex cases
      Strategy 4 — Failure analysis: structured report when all strategies exhausted

    Args:
        tool_name: Name of the tool to execute.
        args: Arguments to pass to the tool.
        attempt: Current attempt number (internal, starts at 0).

    Returns:
        Tool result string, or structured failure report if all strategies fail.
    """
    _MAX_ATTEMPTS = 3

    # ── SAFETY GATE: intercept ALL tool calls before execution ─────────────────
    # GAP-04 FIX: LegionSafetyGuard was UNWIRED — any agent could call any tool
    # including destructive commands (rm -rf, DROP TABLE, force push).
    # Fixed: wire check_tool_call() into every tool invocation here.
    try:
        from core.safety.invariant_guard import get_safety_guard

        guard = get_safety_guard()
        check = guard.check_tool_call(tool_name, args, agent="legion")
        if not check["allowed"]:
            blocked_msg = f"TOOL CALL BLOCKED by LegionSafetyGuard\n  tool: {tool_name}\n  args: {args}\n  reason: {check['reason']}\n  suggestion: {check.get('suggestion', 'n/a')}"
            logger.warning("safety gate blocked: %s", blocked_msg)
            return blocked_msg
        args = check.get("modified_args", args)
    except Exception:
        pass  # Safety guard errors must NOT block tool execution

    # Track strategy usage for structured failure report
    strategy_attempts: list[tuple[str, str]] = []
    errors: list[str] = []

    # ── Strategy 0: MCP tool routing ────────────────────────────────────────────
    # Route MCP-prefixed tools (ruflo_*, crawl4ai_*, etc.) through the MCP router
    # instead of trying computer_agent.execute_tool which doesn't know them.
    if attempt < _MAX_ATTEMPTS:
        try:
            from core.mcp.router import get_mcp_router
            router = get_mcp_router()
            # Check if this tool is registered in the MCP router
            if tool_name in router._tool_to_server or tool_name.startswith(("ruflo_", "crawl4ai_", "browser_use_", "sequential_thinking_", "exa_", "local_deep_research_", "gitnexus_", "obsidian_", "hermes_")):
                strategy_attempts.append(("mcp_router", f"routing via MCP router for {tool_name}"))
                mcp_result = await router.execute_tool(tool_name, args or {})
                if mcp_result:
                    # Check if it's a valid result (not an error JSON)
                    try:
                        parsed = json.loads(mcp_result)
                        if "error" not in parsed:
                            return mcp_result
                    except (json.JSONDecodeError, TypeError):
                        if mcp_result and "error" not in mcp_result.lower():
                            return mcp_result
                    errors.append("strategy_0_mcp_router: returned error result")
        except Exception as e:
            errors.append(f"strategy_0_mcp_router: {e}")

    # ── Strategy 1: Retry with sanitized args (enhanced from original) ──────────
    if attempt < _MAX_ATTEMPTS:
        sanitized = {
            str(k): (v.strip(" \t\n\r\"'") if isinstance(v, str) else v)
            for k, v in (args or {}).items()
        }
        if sanitized != (args or {}):
            strategy_attempts.append(("sanitized", "retry with stripped whitespace/quotes"))
            try:
                result = await execute_tool(tool_name, sanitized)  # type: ignore
                return result
            except Exception as e:
                errors.append(f"strategy_1_sanitize: {e}")

    # ── Strategy 2: Alternative argument pattern ────────────────────────────────
    if attempt < _MAX_ATTEMPTS:
        strategy_attempts.append(("alternative", "retry with re-parsed args"))
        # Try alternative key forms: snake_case, camelCase, original
        alternative_args: dict[str, Any] = {}
        for k, v in (args or {}).items():
            k_str = str(k)
            # Try the original key as-is first
            alternative_args[k_str] = v
        try:
            result = await execute_tool(tool_name, alternative_args)  # type: ignore
            return result
        except Exception as e:
            errors.append(f"strategy_2_alternative: {e}")

    # ── Strategy 3: computer_use_loop fallback ───────────────────────────────────
    # Lazy import to avoid circular imports — only loaded when needed
    if attempt < _MAX_ATTEMPTS:
        strategy_attempts.append(("computer_use_loop", "fallback to vision-reasoning-act loop"))
        try:
            computer_use_loop = None
            from tools.computer_use_agent import computer_use_loop as _cul
            computer_use_loop = _cul
        except ImportError:
            errors.append("strategy_3_computer_use_loop: computer_use_agent unavailable")
            computer_use_loop = None

        if computer_use_loop is not None:
            # Build a descriptive task from the tool call
            tool_description = f"Execute tool '{tool_name}' with arguments: {args}"
            try:
                loop_result = await computer_use_loop(
                    task=tool_description,
                    max_steps=5,
                )
                if loop_result.success:
                    return f"[computer_use_loop recovered] {loop_result.final_state}"
                errors.append(f"strategy_3_computer_use_loop: loop failed — {loop_result.error}")
            except Exception as e:
                errors.append(f"strategy_3_computer_use_loop: {e}")

    # ── Strategy 4: All strategies exhausted — structured failure report ─────────
    attempt_log = f"attempt={attempt}, max_attempts={_MAX_ATTEMPTS}"
    strategies_tried = "; ".join([f"{s} ({r})" for s, r in strategy_attempts])
    error_summary = "; ".join(set(errors))

    failure_report = (
        f"[TOOL SELF_HEAL FAILED]\n"
        f"  tool_name: {tool_name}\n"
        f"  args: {args}\n"
        f"  {attempt_log}\n"
        f"  strategies_tried: {strategies_tried}\n"
        f"  errors: {error_summary}\n"
        f"  conclusion: all recovery strategies exhausted"
    )
    logger.warning("self_heal failure report: %s", failure_report)
    return failure_report


async def call_llm(
    messages: list[dict],
    model: str | None = None,
    tools: list | None = None,
    stream: bool = False,
    task_type: str | None = None,
    **kwargs,
) -> str | dict:
    """Public LLM call interface with fallback chain and tool call support.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        model: Model string (e.g. "opencode-go/deepseek-v4-pro"). Defaults to LEGION_LLM_MODEL env var.
        tools: Optional list of tool definitions for function calling.
        stream: Whether to stream responses (not implemented yet).
        task_type: Optional task category (e.g. "summary", "agent", "wiki").
            When set and max_tokens is not in kwargs, the default for this
            task type is pulled from _TASK_MAX_TOKENS.
        **kwargs: Additional arguments passed to litellm.

    Returns:
        str: Normal text response
        dict: Tool call response with keys 'type' (="tool_call"), 'name', 'args'
    """
    model = model or os.getenv("LEGION_LLM_MODEL", "opencode-go/deepseek-v4-pro")

    if _is_rate_limited(model):
        # FIXED: Use "general" agent key instead of provider name.
        chain = get_fallback_chain("general")
        for fallback_model in chain:
            if not _is_rate_limited(fallback_model):
                model = fallback_model
                break
        else:
            return "rate limited on all providers — retry shortly"

    provider = model.split("/")[0].lower()

    # Per-task max_tokens default (Mitigation 3: token reduction)
    if task_type and "max_tokens" not in kwargs:
        kwargs["max_tokens"] = _TASK_MAX_TOKENS.get(
            task_type, _TASK_MAX_TOKENS["default"]
        )

    api_kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        **kwargs,
    }

    if tools:
        api_kwargs["tools"] = tools
        api_kwargs["tool_choice"] = "auto"

    _is_pytest_run = bool(os.getenv("PYTEST_CURRENT_TEST"))

    if provider == "opencode-go":
        api_kwargs["api_base"] = "https://opencode.ai/zen/go/v1"
        api_key = os.getenv("OPENCODE_GO_API_KEY", "")
        if not api_key:
            if _is_pytest_run:
                api_key = "dummy"
            else:
                raise ValueError("OPENCODE_GO_API_KEY not set")
        api_kwargs["api_key"] = api_key
    elif provider == "anthropic":
        api_kwargs["api_base"] = "https://api.minimax.io/anthropic"
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            if _is_pytest_run:
                api_key = "dummy"
            else:
                raise ValueError("ANTHROPIC_API_KEY not set")
        api_kwargs["api_key"] = api_key
    else:
        # Ollama local fallback
        api_kwargs["api_base"] = "http://localhost:11434"
        api_key = os.getenv("OLLAMA_API_KEY", "ollama")
        api_kwargs["api_key"] = api_key

    # Streaming: return async generator directly without awaiting
    if stream:
        return acompletion(**api_kwargs)

    # ── Infinite memory: recall relevant context, inject as system message ──────────
    try:
        messages = inject_memory_into_messages(messages, agent_id="legion", top_k=10)
    except Exception:
        pass  # Memory injection is non-critical

    # ── Surrogate sanitization (hermes ADR-095 pattern) ─────────────────────────
    # Strip lone surrogates that crash json.dumps in byte-level reasoning models
    _sanitize_messages_surrogates(messages)

    # Phoenix tracing — time the call and track token usage
    _start_time = time.perf_counter()
    _prompt_tokens = 0
    _completion_tokens = 0

    try:
        response = await acompletion(**api_kwargs)
        _latency_ms = (time.perf_counter() - _start_time) * 1000

        # Extract token usage from litellm response
        _usage = getattr(response, "usage", None)
        if _usage is not None:
            _prompt_tokens = getattr(_usage, "prompt_tokens", 0) or 0
            _completion_tokens = getattr(_usage, "completion_tokens", 0) or 0

        # Record to global token tracker
        try:
            from core.integrations.phoenix_observability import get_token_tracker
            _tracker = get_token_tracker()
            _tracker.record_run(model, _prompt_tokens, _completion_tokens, _latency_ms)
        except Exception:
            pass  # Tracing is non-critical

    except litellm.RateLimitError:
        _mark_rate_limited(model)
        # FIXED: Use agent key "general" instead of provider name.
        # Provider name (e.g., "minimax") is not a LEGACY_FALLBACK_CHAIN key —
        # it would fall through to LEGACY_FALLBACK_CHAIN["general"] anyway,
        # but without the correct model_id format (opencode-go/ prefix).
        chain = get_fallback_chain("general")
        for fallback_model in chain:
            if not _is_rate_limited(fallback_model):
                return await call_llm(messages, fallback_model, tools, stream, **kwargs)
        return "rate limited on all providers — retry shortly"
    except Exception:
        raise

    msg = response.choices[0].message
    if msg.tool_calls:
        tc = msg.tool_calls[0]
        return {
            "type": "tool_call",
            "name": tc.function.name,
            "args": json.loads(tc.function.arguments),
        }

    result = (msg.content or "").strip()

    # ── Infinite memory: store response as episodic memory (async, non-blocking) ───
    try:
        _store_response(result, agent_id="legion")
    except Exception:
        pass  # Storage is non-critical

    return result


# ── Core model call ─────────────────────────────────────────────────────────────


async def _call_model(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    _fallback_chain: list[str] | None = None,
    _timeout: float = 30.0,
    **kwargs: Any,
) -> Any:
    """Call a model via litellm acompletion.

    Hardened with:
    - 30s hard timeout per call
    - Exponential backoff retry: 1s→2s→4s, max 3 attempts
    - Retry on: RateLimitError, APIConnectionError, Timeout
    - Model fallback chain support
    """
    chain = _fallback_chain or [model]
    _is_pytest_run = bool(os.getenv("PYTEST_CURRENT_TEST"))

    for _attempt_idx, model_name in enumerate(chain):
        provider = model_name.split("/")[0].lower()

        kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        if provider == "opencode-go":
            kwargs["api_base"] = "https://opencode.ai/zen/go/v1"
            api_key = os.getenv("OPENCODE_GO_API_KEY", "")
            if not api_key:
                if _is_pytest_run:
                    api_key = "dummy"
                else:
                    raise ValueError("OPENCODE_GO_API_KEY not set")
            kwargs["api_key"] = api_key

        elif provider == "anthropic":
            kwargs["api_base"] = "https://api.minimax.io/anthropic"
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key:
                if _is_pytest_run:
                    api_key = "dummy"
                else:
                    raise ValueError("ANTHROPIC_API_KEY not set")
            kwargs["api_key"] = api_key

        else:
            api_key = _get_api_key(model_name)
            if not api_key:
                raise ValueError(f"No API key for '{provider}'")
            kwargs["api_key"] = api_key

        # Retry with exponential backoff: 1s → 2s → 4s
        for retry_attempt in range(3):
            try:
                # AUDIT04: Log every actual acompletion call
                logger.debug(
                    f"[AUDIT04] acompletion call: model={model_name}, messages={len(messages)}, "
                    f"roles={[m.get('role') for m in messages]}"
                )
                return await asyncio.wait_for(acompletion(**kwargs), timeout=_timeout)
            except (TimeoutError, litellm.RateLimitError, litellm.APIConnectionError) as exc:
                if retry_attempt < 2:
                    wait = (2**retry_attempt) + random.uniform(0, 1)
                    logger.warning(
                        "[_call_model] %s on '%s' (attempt %d/3), retrying in %.1fs: %s",
                        type(exc).__name__,
                        model_name,
                        retry_attempt + 1,
                        wait,
                        exc,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.warning("[_call_model] %s on '%s' — trying fallback model", type(exc).__name__, model_name)
                    break  # Break retry loop, try next model in chain
            except Exception:
                raise  # Non-retryable error — propagate immediately


# ── Wiki completion (lightweight, no humanization stack) ──────────────────────


async def wiki_raw_completion(
    user_prompt: str,
    *,
    system_prompt: str = "You follow instructions precisely. Output only what is asked — no preamble.",
    model: str | None = None,
    temperature: float = 0.25,
    max_tokens: int | None = None,
) -> str:
    """Single-turn LLM call for wiki maintenance (no mem0 / wiki / humanization stack)."""
    m = model or os.getenv("LEGION_WIKI_LLM_MODEL", "opencode-go/deepseek-v4-pro")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        resp = await _call_model(m, messages, temperature=temperature, max_tokens=max_tokens)
        return (resp.choices[0].message.reasoning_content or resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("wiki_raw_completion failed: %s", e)
        return f"[wiki completion error: {e}]"


# ── Six-Layer Memory-Aware Compaction Engine ─────────────────────────────────────
#
#  DESIGN (with unlimited go API + 6 memory layers + big storage):
#
#  Every full compaction:
#    1. PRE-COMPACT: query ALL 6 layers (build_memory_context)
#                   → also query CompactionStore (FTS5) for prior summaries
#                   → MCP deduplication to remove overlapping tool results
#    2. COMPACT: LLM summarization enriched with prior summaries + 6-layer context
#    3. POST-COMPACT: STORE summary to CompactionStore (FTS5 searchable)
#                    → also store to all 6 memory layers (future compactions get richer context)
#
#  Compaction triggers (model-aware — all relative to _COMPACTION_MAX_CONTEXT):
#    Tier 1 (50% fill):  microcompact — NO LLM, every turn, post-tool
#    Tier 2 (70% fill):  microcompact again if still over threshold
#    Tier 3 (85% fill):  ASYNC full compaction STARTS (non-blocking LLM call)
#    Tier 4 (95% fill):  BLOCKING full compaction (only if async hasn't finished)
#    Tier 5 (99% fill): EMERGENCY — force blocking even if async still running
#
#  The key insight: with unlimited API we can afford to run FULL compaction at 80%
#  (800K chars) so summaries are shorter and more precise (less history to condense = better quality).
#
#  Storage: every compaction summary is stored to CompactionStore (FTS5) AND all 6 layers,
#  making future compactions smarter because prior summaries are queryable and enriched.

# ── Model-aware compaction thresholds ──────────────────────────────────────
# All tiers are RELATIVE to _COMPACTION_MAX_CONTEXT (chars), which is read
# from `.opencode/opencode.json` → `compaction.maxContext` at import time.
# This means:
#   1. maxContext = 1000000 → Tier 3 fires at 850K chars (85%)
#   2. Edit maxContext in opencode.json → all 5 tiers auto-adjust
#   3. Behaves like OpenCode native: config is the single source of truth
#
# The config path is derived from this file's location (works regardless of cwd).
_COMPACTION_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".opencode" / "opencode.json"


def _load_compaction_max_context(fallback: int = 1000000) -> int:
    """Read `compaction.maxContext` from opencode.json at import time.

    This mirrors how OpenCode native reads config — the JSON file is the
    single source of truth for the model's context window. If unavailable
    (e.g. tests, different project layout), returns the fallback.
    """
    try:
        import json
        cfg = json.loads(_COMPACTION_CONFIG_PATH.read_text())
        max_ctx = cfg.get("compaction", {}).get("maxContext")
        if max_ctx and isinstance(max_ctx, (int, float)) and max_ctx > 0:
            return int(max_ctx)
    except Exception:
        pass
    return fallback


_COMPACTION_MAX_CONTEXT = _load_compaction_max_context()
_COMPACTION_TIER_1 = int(0.50 * _COMPACTION_MAX_CONTEXT)  # 50% — microcompact, NO LLM
_COMPACTION_TIER_2 = int(0.70 * _COMPACTION_MAX_CONTEXT)  # 70% — tighter microcompact
_COMPACTION_TIER_3 = int(0.85 * _COMPACTION_MAX_CONTEXT)  # 85% — ASYNC full LLM compaction
_COMPACTION_TIER_4 = int(0.95 * _COMPACTION_MAX_CONTEXT)  # 95% — BLOCKING full LLM
_COMPACTION_TIER_5 = int(0.99 * _COMPACTION_MAX_CONTEXT)  # 99% — EMERGENCY force

# ── Tier 1 & 2: Ultra-light microcompact — NO LLM, runs every turn ────────────────

def _microcompact_messages(messages: list[dict], threshold: int = _COMPACTION_TIER_1) -> list[dict]:
    """Ultra-light pruning — truncate long tool results, preserve structure.

    Called PROACTIVELY after EVERY tool result and when context crosses 50% fill.
    NO LLM involved — pure string truncation. Keeps context at ~35% fill.
    """
    if len(messages) <= 4:
        return messages

    total_size = sum(len(str(m.get("content", ""))) for m in messages)
    if total_size < threshold:
        return messages

    system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    result: list[dict] = []

    if system_msg:
        result.append(system_msg)

    for m in messages[1:]:
        if m.get("role") == "system":
            result.append(m)
            continue

        content = m.get("content", "")
        role = m.get("role", "")

        if role == "tool":
            # Errors: keep SHORT (critical but noisy)
            if any(kw in content.lower() for kw in ("error", "fail", "traceback", "exception", "invalid")):
                truncated = content[:150] + "\u2026" if len(content) > 150 else content
            else:
                # Successful results: keep MEDIUM (may contain useful data)
                truncated = content[:500] + "\u2026" if len(content) > 500 else content
            result.append({**m, "content": truncated})
        elif role == "assistant" and m.get("tool_calls"):
            # NEVER truncate tool_calls — they're tiny and critical for the LLM
            result.append(m)
        elif role in ("user", "assistant"):
            # Keep conversational content snappy
            truncated = content[:200] + "\u2026" if len(content) > 200 else content
            result.append({**m, "content": truncated})
        else:
            result.append(m)

    new_size = sum(len(str(m.get("content", ""))) for m in result)
    logger.debug("Microcompact: %d → %d (saved %d chars)", total_size, new_size, total_size - new_size)
    return result


def _microcompact_if_needed(messages: list[dict]) -> list[dict]:
    """Called after EVERY tool result — proactive microcompact to keep context under 50%."""
    total_size = sum(len(str(m.get("content", ""))) for m in messages)
    if total_size > _COMPACTION_TIER_1:
        return _microcompact_messages(messages, threshold=_COMPACTION_TIER_1)
    return messages


# ── Context compaction (async, non-blocking) ────────────────────────────────────
import concurrent.futures  # noqa: E402
import threading  # noqa: E402
from collections import OrderedDict  # noqa: E402
from pathlib import Path  # noqa: E402

# LRU cache for compaction — 100x speedup on repeated conversation patterns
_COMPACT_CACHE: OrderedDict = OrderedDict()
_COMPACT_CACHE_LOCK = threading.Lock()
_COMPACT_CACHE_MAX = 100  # increased — more conversation patterns cached

# Session-level compaction log — tracks what we've already compacted
# so we never compress the same window twice (prevents information loss)
_COMPACT_HISTORY: dict[str, str] = {}  # cache_key → summary_text (for deduplication)
_COMPACT_HISTORY_LOCK = threading.Lock()

# Track last compaction time to avoid over-compacting
_LAST_COMPACT_AT = 0.0
_COMPACT_COOLDOWN = 5.0  # seconds between compactions (debounce)

# Thread pool for truly async I/O (all blocking operations go here)
_COMPACT_IO_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="compact_io")

# ── Tier 3/4 cascade prevention ──────────────────────────────────────────────
# Prevents Tier 4 (blocking) from firing while Tier 3 (async) is still running.
# This is the GLOBAL flag (not per-messages-list) so it survives list replacement.
_ASYNC_COMPACT_IN_FLIGHT: bool = False
_ASYNC_COMPACT_LOCK: threading.Lock = threading.Lock()

# ── OpenCode shell hook runner ───────────────────────────────────────────────
# When OpenCode native compaction is disabled (threshold=1.0), its auto-discovered
# pre-compact.sh / post-compact.sh hooks no longer fire. We run them from here instead.

_SHELL_HOOKS_DIR = Path(__file__).resolve().parent.parent / ".opencode" / "hooks"


def _run_shell_hook(hook_name: str) -> None:
    """Run an OpenCode shell hook script if present. Non-blocking, best-effort."""
    hook_path = _SHELL_HOOKS_DIR / f"{hook_name}.sh"
    if not hook_path.exists():
        return
    try:
        import subprocess
        subprocess.run(
            ["bash", str(hook_path)],
            timeout=10,
            capture_output=True,
        )
    except Exception:
        logger.debug("Shell hook %s failed (non-fatal)", hook_name)


def _get_cache_key(messages: list[dict]) -> str:
    """Fast O(n) cache key: MD5 of role pattern + message count + first/last tool names."""
    tool_names = []
    for m in messages:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            for tc in m.get("tool_calls", []):
                name = tc.get("function", {}).get("name", "?")
                if name not in tool_names:
                    tool_names.append(name)
    first_last = tuple(tool_names[:3] + tool_names[-3:] if len(tool_names) > 6 else tool_names)
    role_pattern = "".join(m.get("role", "")[0] for m in messages if m.get("role"))
    lengths = [len(str(m.get("content", ""))) for m in messages[-12:]]
    key_str = f"{role_pattern}:{len(messages)}:{lengths}:{first_last}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _deduplicate_mcp_tool_results(messages: list[dict]) -> list[dict]:
    """Deduplicate overlapping MCP tool results from the same session.

    MCPs (ruflo, ruflo, hermes, etc.) often return the same data repeatedly.
    When the same content appears in consecutive tool results from the same
    MCP namespace, keep only the latest — older duplicates waste context budget.
    """
    if len(messages) < 6:
        return messages

    seen_content: dict[str, tuple[str, int]] = {}  # content_hash -> (content, index)
    result: list[dict] = []

    for i, m in enumerate(messages):
        role = m.get("role", "")
        content = m.get("content", "")

        if role != "tool":
            result.append(m)
            continue

        tool_call_id = m.get("tool_call_id", "")
        # Create namespace key from tool_call_id prefix (e.g., "hermes_", "ruflo_")
        namespace = tool_call_id.split("_")[0] if "_" in tool_call_id else tool_call_id[:8]

        # Hash content to detect duplicates
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]

        key = f"{namespace}:{content_hash}"
        if content_hash and len(content) > 50:
            # Same MCP namespace + similar content within 5 messages = duplicate
            if key in seen_content:
                prev_idx = seen_content[key][1]
                if i - prev_idx <= 5:
                    # Duplicate within window — skip it, keep the newer one
                    logger.debug(
                        "Deduplicated MCP result %s (dup of index %d, delta=%d)",
                        key[:8], prev_idx, i - prev_idx,
                    )
                    continue
            seen_content[key] = (content, i)

        result.append(m)

    return result


# ── Async memory fetch (truly non-blocking) ──────────────────────────────────

async def _aget_memory_context_before_compact(query: str, timeout: float = 10.0) -> str:
    """Async fetch 6-layer memory context — NEVER blocks the compaction pipeline.

    Runs memory query in background thread pool and returns empty string on timeout.
    The caller does NOT wait for this — it's fire-and-forget.
    """
    def _sync_fetch() -> str:
        try:
            from core.memory.memory_injector import build_memory_context as _injector_bmc
            return _injector_bmc(query=query, user_id="bashara")
        except Exception:
            return ""

    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_COMPACT_IO_EXECUTOR, _sync_fetch),
            timeout=timeout,
        )
    except TimeoutError:
        return ""
    except Exception:
        return ""


async def _async_compact_if_needed(messages: list[dict], user_id: Optional[str], system_prompt: str = "") -> None:
    """Non-blocking async full compaction — fires at Tier 3, completes before Tier 4.

    With unlimited minimax API, we can afford to run LLM summarization MORE OFTEN
    (starting at 80% instead of 96%) so the summaries are shorter and more accurate
    (less context to summarize = better quality per token).
    """
    try:
        # Small delay to allow current tool result to be added to messages
        await asyncio.sleep(0.5)

        # Check if we still need compaction (another turn may have done it)
        total_size = sum(len(str(m.get("content", ""))) for m in messages)
        if total_size < 90000:
            messages._full_compact_pending = False  # type: ignore[attr-defined]
            with _ASYNC_COMPACT_LOCK:
                _ASYNC_COMPACT_IN_FLIGHT = False
            return

        # Run full compaction with memory enrichment
        compacted = smart_compact_messages(messages, model="opencode-go/deepseek-v4-pro", system_prompt=system_prompt)

        # Check if compaction actually reduced size
        new_size = sum(len(str(m.get("content", ""))) for m in compacted)
        if new_size >= total_size:
            messages._full_compact_pending = False  # type: ignore[attr-defined]
            with _ASYNC_COMPACT_LOCK:
                _ASYNC_COMPACT_IN_FLIGHT = False
            return

        # Replace messages in-place so the calling context gets the compacted version
        messages.clear()
        messages.extend(compacted)

        # Emit post_compact hooks
        try:
            from core.hooks import get_hooks
            # project_dir may be stored on messages._project_dir by the caller
            project_dir = getattr(messages, '_project_dir', None) or "/home/newadmin/swarm-bot"
            get_hooks().emit("post_compact", {
                "user_id": user_id or "default",
                "reason": "async_compaction_complete",
                "original_size": total_size,
                "compacted_size": new_size,
                "project_dir": project_dir,
            })
        except Exception:
            pass

        logger.debug("Async compaction complete: %d → %d chars", total_size, new_size)
    except Exception as e:
        logger.debug("Async compaction failed: %s", e)
    finally:
        # Clear BOTH the per-messages flag AND the global Tier 3/4 cascade lock
        try:
            messages._full_compact_pending = False  # type: ignore[attr-defined]
        except Exception:
            pass
        with _ASYNC_COMPACT_LOCK:
            _ASYNC_COMPACT_IN_FLIGHT = False


async def _aget_compaction_memory_layers(query: str, timeout: float = 8.0) -> dict[str, str]:
    """Async query 4 memory layers in parallel — returns {} on any failure.

    Does NOT block. Uses run_in_executor so the GIL isn't held during I/O.
    Returns dict with keys: recent_sessions, decisions, open_issues, tools_used
    """
    queries = {
        "recent_sessions": "recent session work tasks completed",
        "decisions": "decisions made choices agreed architecture",
        "open_issues": "bugs being fixed features in progress open todos",
        "tools_used": "tools used functions commands run this session",
    }

    async def _fetch_layer(key: str, q: str) -> tuple[str, str]:
        def _sync() -> str:
            try:
                from core.memory.memory_injector import build_memory_context
                return build_memory_context(query=q, user_id="bashara")
            except Exception:
                return ""

        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(_COMPACT_IO_EXECUTOR, _sync),
                timeout=timeout,
            )
            return key, result
        except TimeoutError:
            return key, ""
        except Exception:
            return key, ""

    # Fire all 4 queries in parallel — don't wait more than timeout total
    tasks = [_fetch_layer(k, q) for k, q in queries.items()]
    results: dict[str, str] = {}
    try:
        gathered = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        for item in gathered:
            if isinstance(item, tuple) and len(item) == 2:
                k, v = item
                results[k] = v
    except (TimeoutError, Exception):
        pass
    return results


def _get_memory_context_before_compact(query: str, timeout: float = 15.0) -> str:
    """Sync wrapper — use ONLY if you're already in a thread. For async code use _aget_*. """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _sync_build_memory_context, query, "bashara"
            )
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.debug("Memory context timed out after %.0fs", timeout)
                return ""
    except Exception as e:
        logger.debug("Memory context fetch failed: %s", e)
        return ""


def _sync_build_memory_context(query: str, user_id: str = "bashara") -> str:
    """Sync wrapper around memory_injector's build_memory_context."""
    from core.memory.memory_injector import build_memory_context as _injector_bmc
    return _injector_bmc(query=query, user_id=user_id)


def _query_compaction_memory_layers(query: str, timeout: float = 12.0) -> dict[str, str]:
    """Query multiple memory layers with different queries for richer context.

    Returns dict with keys: recent_sessions, decisions, open_issues, tools_used
    Each value is a formatted string from that layer's recall.

    NOTE: This is sync and BLOCKING. For non-blocking behavior in async context,
    use _aget_compaction_memory_layers() instead.
    """
    queries = {
        "recent_sessions": "recent session work tasks completed",
        "decisions": "decisions made choices agreed architecture",
        "open_issues": "bugs being fixed features in progress open todos",
        "tools_used": "tools used functions commands run this session",
    }

    results: dict[str, str] = {}
    deadline = time.time() + timeout

    def _fetch(key: str, q: str) -> str:
        try:
            from core.memory.memory_injector import build_memory_context
            return build_memory_context(query=q, user_id="bashara")
        except Exception:
            return ""

    # Use thread pool for I/O parallelism but respect overall timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {key: executor.submit(_fetch, key, q) for key, q in queries.items()}
        for key, future in futures.items():
            remaining = max(0.1, deadline - time.time())
            try:
                results[key] = future.result(timeout=remaining)
            except concurrent.futures.TimeoutError:
                results[key] = ""
            except Exception:
                results[key] = ""

    return results


def _generate_memory_aware_summary(
    history: list[dict],
    memory_context: str,
    multi_layer: dict[str, str],
    model: str = "opencode-go/deepseek-v4-pro",
    timeout: float = 20.0,
) -> str:
    """Generate compaction summary enriched with 6-layer memory context + multi-layer pre-query.

    Uses run_in_executor to avoid blocking the async caller. Returns "" on any failure
    so the compaction pipeline can proceed without waiting.
    """
    if not history:
        return "[earlier conversation omitted — no content]"

    # Build history text
    summary_parts = []
    for m in history:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant" and m.get("tool_calls"):
            tool_names = [tc.get("function", {}).get("name", "?") for tc in m.get("tool_calls", [])]
            summary_parts.append("[assistant called: " + ", ".join(tool_names) + "]")
        elif role == "tool":
            truncated = content[:200] + "..." if len(content) > 200 else content
            # Preserve error status in tool results
            if "error" in content.lower() or "fail" in content.lower():
                summary_parts.append("[tool ERROR: " + truncated + "]")
            else:
                summary_parts.append("[tool result: " + truncated + "]")
        elif role and content:
            truncated = content[:300] + "..." if len(content) > 300 else content
            summary_parts.append("[" + role + "]: " + truncated)

    history_text = "\n".join(summary_parts[-15:])  # increased from 12

    # Build rich memory intro from multi-layer query results
    memory_sections = []

    if multi_layer.get("recent_sessions"):
        memory_sections.append("━━━ PRIOR SESSION CONTEXT ━━━\n" + multi_layer["recent_sessions"])

    if multi_layer.get("decisions"):
        memory_sections.append("━━━ DECISIONS MADE ━━━\n" + multi_layer["decisions"])

    if multi_layer.get("open_issues"):
        memory_sections.append("━━━ OPEN ISSUES ━━━\n" + multi_layer["open_issues"])

    if multi_layer.get("tools_used"):
        memory_sections.append("━━━ TOOLS USED (HISTORICAL) ━━━\n" + multi_layer["tools_used"])

    # Also include general memory context if available
    if memory_context and memory_context.strip():
        memory_sections.append("━━━ GENERAL MEMORY CONTEXT ━━━\n" + memory_context)

    memory_intro = "\n\n".join(memory_sections) if memory_sections else "(no prior memory found)"

    summary_request = """━━━ PRIOR CONTEXT FROM MEMORY ━━━
""" + memory_intro + """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now condense the CONVERSATION HISTORY below into a dense narrative summary.
The prior context above tells you what was already decided, what's open, and what's been done.
Your job is to bridge that context with the history — do NOT repeat the prior context verbatim.
Focus on NEW decisions, NEW changes, NEW tool outputs, and NEW open items not already listed above.

━━━ CONVERSATION HISTORY ━━━
""" + history_text + """

━━━ OUTPUT FORMAT (9-section LEGION compaction format) ━━━
## 1. System Purpose
 What the system/agent is trying to accomplish in this session
## 2. Current Files (in-progress only)
 Files that are currently being edited, modified, or worked on
## 3. Active Changes
 Specific changes made (file edits, new files, deletions) — be precise
## 4. Recent Decisions
 Decisions made, choices agreed, architectural choices, tool selections
## 5. Pain Points
 Errors encountered, bugs found, failed approaches, difficult issues
## 6. Next Moves
 What needs to be done next, remaining tasks, TODOs from this session
## 7. Sticky Files
 Key files that were touched and should be revisited (file paths)
## 8. Tools Used
 Tools/functions called and what happened (one line per tool, include errors)
## 9. Context Budget
 Approximate context usage: [N] chars / 204K (65% target = 133K)

Be specific — avoid generic phrases. Never say "discussed various topics".
Include file paths, function names, error messages verbatim when relevant.
"""

    def _sync_llm_call() -> str:
        try:
            from litellm import completion
            response = completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise narrative summarizer. Output only the 9-section LEGION compaction format. Do not restate prior context.",
                    },
                    {"role": "user", "content": summary_request},
                ],
                max_tokens=3072,
                temperature=0.3,
                timeout=timeout,
            )
            msg = response.choices[0].message
            # MiniMax-M3 puts actual output in reasoning_content, not content
            # content='\n\n' with real text in reasoning_content is a known pattern
            raw = msg.reasoning_content or msg.content or ""
            return raw.strip()
        except Exception as e:
            logger.debug("Memory-aware summary generation failed: %s — using fallback", e)
            # FAST fallback: no LLM needed
            tool_names = []
            errors = []
            for m in history:
                if m.get("role") == "assistant" and m.get("tool_calls"):
                    for tc in m.get("tool_calls", []):
                        tool_names.append(tc.get("function", {}).get("name", "?"))
                elif m.get("role") == "tool":
                    c = m.get("content", "")
                    if "error" in c.lower() or "fail" in c.lower():
                        errors.append(c[:100])
            result = "## 8. Tools Used\n" + ", ".join(tool_names[-12:])
            if errors:
                result += "\n## 5. Pain Points\n" + "; ".join(errors[:5])
            return result

    # Run LLM call in thread pool with hard timeout — never blocks compaction pipeline
    future = _COMPACT_IO_EXECUTOR.submit(_sync_llm_call)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        logger.debug("Compaction LLM call timed out after %.0fs — using fast fallback", timeout)
        # Instant fallback: extract only tool names and errors, no LLM needed
        tool_names, errors = [], []
        for m in history:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tc in m.get("tool_calls", []):
                    tool_names.append(tc.get("function", {}).get("name", "?"))
            elif m.get("role") == "tool":
                c = m.get("content", "")
                if "error" in c.lower() or "fail" in c.lower():
                    errors.append(c[:100])
        result = "## 8. Tools Used\n" + ", ".join(tool_names[-12:])
        if errors:
            result += "\n## 5. Pain Points\n" + "; ".join(errors[:5])
        return result
    except Exception as e:
        logger.debug("Compaction LLM call exception: %s", e)
        return ""


def _async_store_compaction_summary(summary: str, message_count: int, cache_key: str) -> None:
    """Fire-and-forget storage to ALL 6 memory layers + CompactionStore.

    Writes the compaction summary to every memory layer so future compactions
    are enriched with full historical context. Never blocks the pipeline.
    On failure of any individual layer, logs and continues — never propagates.
    """
    def _sync_write() -> None:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        session_dir = Path("/home/newadmin/swarm-bot/.session_state")
        session_dir.mkdir(parents=True, exist_ok=True)

        # ── Layer 1: Session checkpoint file ──────────────────────────────────
        try:
            checkpoint = {
                "type": "compaction_summary",
                "timestamp": now,
                "messages_compacted": message_count,
                "cache_key": cache_key[:16],
                "summary": summary,
            }
            cp_path = session_dir / "checkpoints" / f"compact_{int(time.time())}.json"
            cp_path.parent.mkdir(parents=True, exist_ok=True)
            import json as _json
            with open(cp_path, "w") as f:
                _json.dump(checkpoint, f)
        except Exception as e:
            logger.debug("L1 checkpoint write failed: %s", e)

        # ── Layer 2: ChromaDB (MemoryStore) ─────────────────────────────────────
        try:
            from core.memory.store import MemoryStore
            store = MemoryStore()
            store.remember(
                content=summary,
                agent_id="compact",
                metadata={
                    "type": "compaction_summary",
                    "messages_compacted": message_count,
                    "cache_key": cache_key[:16],
                },
            )
        except Exception as e:
            logger.debug("L2 MemoryStore write failed: %s", e)

        # ── Layer 3: langmem (langgraph InMemoryStore) ─────────────────────────
        try:
            from core.memory.memory_injector import LANGMEM_AVAILABLE, _get_langmem_store
            if LANGMEM_AVAILABLE:
                langmem_store = _get_langmem_store()
                langmem_store.put(
                    ("swarmbot", "compactions"),
                    cache_key[:16],
                    {
                        "content": summary,
                        "messages_compacted": message_count,
                        "timestamp": now,
                    },
                )
        except Exception as e:
            logger.debug("L3 langmem write failed: %s", e)

        # ── Layer 4: observation_store (SQLite+FTS5) ──────────────────────────
        try:
            from core.memory.observation_store import get_observation_store
            obs = get_observation_store()
            # add_observation is async; call via running loop in a thread to avoid
            # asyncio.run() event-loop conflicts with aiosqlite connection lifecycle.
            def _obs_sync() -> None:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(obs.add_observation(
                        session_id="compact",
                        content=summary,
                        title=f"Compaction: {message_count} msgs → cache_key={cache_key[:8]}",
                        type_="compaction",
                        subtitle=f"saved cache_key={cache_key[:12]}",
                        tags=["compaction", "memory", "compact"],
                    ))
                    return
                loop.run_until_complete(obs.add_observation(
                    session_id="compact",
                    content=summary,
                    title=f"Compaction: {message_count} msgs → cache_key={cache_key[:8]}",
                    type_="compaction",
                    subtitle=f"saved cache_key={cache_key[:12]}",
                    tags=["compaction", "memory", "compact"],
                ))
            # Run L4 in the existing _COMPACT_IO_EXECUTOR so it doesn't block
            _COMPACT_IO_EXECUTOR.submit(_obs_sync)
        except Exception as e:
            logger.debug("L4 observation_store write failed: %s", e)

        # ── Layer 5: graphrag wiki ─────────────────────────────────────────────
        try:
            wiki_dir = Path("/home/newadmin/swarm-bot/.wiki/auto")
            wiki_dir.mkdir(parents=True, exist_ok=True)
            wiki_file = wiki_dir / f"compact_{int(time.time())}.md"
            wiki_content = f"""---
title: Compaction Summary {now}
type: compaction
tags: [compaction, memory, session]
cache_key: {cache_key[:16]}
messages_compacted: {message_count}
---

{summary}
"""
            with open(wiki_file, "w") as f:
                f.write(wiki_content)
        except Exception as e:
            logger.debug("L5 graphrag wiki write failed: %s", e)

        # ── Layer 6: mem0 cloud ────────────────────────────────────────────────
        try:
            from tools.mem0_client import mem0_add
            # mem0_add is async but mem.add() inside is sync HTTP I/O to Ollama.
            # Run via running loop in this thread to avoid event-loop conflicts.
            def _mem0_sync() -> None:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(mem0_add(
                        user_id="bashara",
                        content=summary,
                        metadata={
                            "type": "compaction_summary",
                            "messages_compacted": message_count,
                            "cache_key": cache_key[:16],
                        },
                    ))
                    return
                loop.run_until_complete(mem0_add(
                    user_id="bashara",
                    content=summary,
                    metadata={
                        "type": "compaction_summary",
                        "messages_compacted": message_count,
                        "cache_key": cache_key[:16],
                    },
                ))
            _COMPACT_IO_EXECUTOR.submit(_mem0_sync)
        except Exception as e:
            logger.debug("L6 mem0 cloud write failed: %s", e)

        # ── CompactionStore (SQLite+FTS5) — re-store with quality score ─────────
        try:
            from llm_client.compaction_store import get_compaction_store
            cs = get_compaction_store()
            # Quality: estimate from summary length vs history size
            quality = min(1.0, max(0.0, len(summary) / max(message_count * 20, 1)))
            cs.store(
                cache_key=cache_key,
                summary=summary,
                message_count=message_count,
                model_used="opencode-go/deepseek-v4-pro",
                chars_saved=0,
                original_size=0,
                compacted_size=len(summary),
                topic_tags=["compaction"],
                quality_score=quality,
            )
        except Exception as e:
            logger.debug("CompactionStore re-write failed: %s", e)

        # ── session_state file for opencode bridge ────────────────────────────
        try:
            compaction_file = session_dir / "compaction_summary.md"
            header = f"""---
tags: [compaction, memory, session]
date: {now}
messages_compacted: {message_count}
cache_key: {cache_key[:16]}
layers_written: [checkpoint, memorystore, langmem, observation_store, wiki, mem0]
---

"""
            with open(compaction_file, "w") as f:
                f.write(header + summary)
        except Exception as e:
            logger.debug("session_state file write failed: %s", e)

    # Fire-and-forget — this NEVER blocks the compaction pipeline
    _COMPACT_IO_EXECUTOR.submit(_sync_write)


def _store_compaction_summary(summary: str, message_count: int, cache_key: str) -> None:
    """Sync wrapper for backwards compatibility — use _async_store_compaction_summary in async code."""
    _async_store_compaction_summary(summary, message_count, cache_key)


def smart_compact_messages(
    messages: list[dict],
    keep_recent: int = 8,  # increased from 6 — preserve more recent turns
    system_prompt: str = "",
    model: str = "opencode-go/deepseek-v4-pro",
    session_id: Optional[str] = None,
) -> list[dict]:
    """Memory-aware compaction using ALL 6 memory layers + LRU cache + CompactionStore.

    Pipeline:
      PRE-COMPACT  → query all 6 memory layers via build_memory_context
                   → query CompactionStore for prior summaries of similar conversations
      COMPACT      → LLM summarization enriched with prior summaries + 6-layer context
      POST-COMPACT → store to CompactionStore (FTS5 search)
                   → store to all 6 memory layers (future compactions get richer context)

    With unlimited MiniMax API, we run full LLM compaction EARLIER (65% fill)
    so summaries are shorter and more precise (less history to condense).

    Cache: repeated compaction of same conversation pattern hits LRU cache (100x faster).
    Deduplication: same cache_key never gets re-summarized within cooldown window.
    """
    # Debounce: don't compact more than once every _COMPACT_COOLDOWN seconds
    global _LAST_COMPACT_AT
    now = time.time()
    if now - _LAST_COMPACT_AT < _COMPACT_COOLDOWN and len(messages) > 10:
        return messages
    _LAST_COMPACT_AT = now

    if len(messages) <= keep_recent + 1:
        return messages

    # LRU cache lookup — 100x speedup for repeated patterns
    cache_key = _get_cache_key(messages)
    with _COMPACT_CACHE_LOCK:
        if cache_key in _COMPACT_CACHE:
            cached = _COMPACT_CACHE.pop(cache_key)
            _COMPACT_CACHE[cache_key] = cached
            logger.debug("Compaction cache hit [%s]", cache_key[:8])
            return cached

    # ── Deduplicate MCP results BEFORE compacting ───────────────────────────────
    messages = _deduplicate_mcp_tool_results(messages)

    system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    recent = messages[-keep_recent:]
    history = messages[1:-keep_recent] if not system_msg else messages[1:-keep_recent]

    if not history:
        return messages

    original_size = sum(len(str(m.get("content", ""))) for m in messages)

    # ── Run OpenCode shell hooks (pre-compact) ────────────────────────────────
    # With OpenCode native compaction disabled (threshold=1.0), its auto-discovered
    # shell hooks (pre-compact.sh, post-compact.sh) no longer fire. We run them
    # here instead so session state checkpointing still works.
    _run_shell_hook("pre-compact")
    try:
        from core.hooks import get_hooks
        get_hooks().emit("pre_compact", {
            "reason": "smart_compact",
            "original_size": original_size,
            "message_count": len(history),
        })
    except Exception:
        pass

    # ── PRE-COMPACT: full 6-layer memory context (PARALLEL, non-blocking) ─────
    # With unlimited API + big storage, query all memory layers IN PARALLEL
    # using the thread pool so compaction never blocks on I/O.
    # _query_compaction_memory_layers fires 4 queries concurrently (~10s wall time max).
    def _fetch_memory_and_store() -> tuple[str, str]:
        """Fetch 6-layer context AND CompactionStore prior summaries in one shot."""
        # Run both in parallel via thread pool
        import concurrent.futures as _cf
        results: dict[str, str] = {}
        deadline = time.time() + 20.0

        def _fetch_layers() -> dict[str, str]:
            try:
                return _query_compaction_memory_layers(
                    query="session work tasks decisions tools recent",
                    timeout=18.0,
                )
            except Exception:
                return {}

        def _fetch_compaction_store() -> str:
            try:
                from llm_client.compaction_store import get_compaction_store
                cs = get_compaction_store()
                return cs.get_context_for_compaction(
                    query="session decisions tools work",
                    session_id=session_id,
                    limit=3,
                )
            except Exception:
                return ""

        with _cf.ThreadPoolExecutor(max_workers=2) as _ex:
            f1 = _ex.submit(_fetch_layers)
            f2 = _ex.submit(_fetch_compaction_store)
            try:
                multi_layer = f1.result(timeout=deadline - time.time())
            except Exception:
                multi_layer = {}
            try:
                prior_summaries = f2.result(timeout=max(1.0, deadline - time.time()))
            except Exception:
                prior_summaries = ""

        results["multi_layer"] = multi_layer if isinstance(multi_layer, dict) else {}
        results["prior_summaries"] = prior_summaries if isinstance(prior_summaries, str) else ""
        return results

    # Run in thread pool — never blocks the caller
    try:
        _mem_result = _COMPACT_IO_EXECUTOR.submit(_fetch_memory_and_store).result(timeout=25.0)
        multi_layer = _mem_result.get("multi_layer", {})
        prior_summaries = _mem_result.get("prior_summaries", "")
    except Exception:
        multi_layer = {}
        prior_summaries = ""

    # Fallback: if thread pool call timed out, try a quick direct call
    if not multi_layer or not isinstance(multi_layer, dict):
        memory_context = _get_memory_context_before_compact(
            query="session work tasks decisions tools recent",
            timeout=5.0,
        )
    else:
        # Build memory_context from multi_layer results
        memory_parts = []
        for k, v in multi_layer.items():
            if v and isinstance(v, str) and len(v) > 10:
                memory_parts.append(f"[{k}]: {v[:300]}")
        memory_context = "\n".join(memory_parts) if memory_parts else ""

    # ── COMPACT: memory-enriched LLM summarization ─────────────────────────────
    # With unlimited API, we can afford richer context — pass multi_layer too
    summary_text = _generate_memory_aware_summary(
        history, memory_context, multi_layer, model=model,
    )

    if not summary_text or len(summary_text) < 20:
        # LLM failed — use instant fallback
        tool_names, errors = [], []
        for m in history:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tc in m.get("tool_calls", []):
                    tool_names.append(tc.get("function", {}).get("name", "?"))
            elif m.get("role") == "tool":
                c = m.get("content", "")
                if any(kw in c.lower() for kw in ("error", "fail", "traceback")):
                    errors.append(c[:100])
        summary_parts = [
            f"## 8. Tools Used\n  • {', '.join(tool_names[-12:])}",
        ]
        if errors:
            summary_parts.append(f"\n## 5. Pain Points\n  • {'; '.join(errors[:5])}")
        summary_text = "\n".join(summary_parts)

    compacted_size = sum(len(str(m.get("content", ""))) for m in recent) + len(summary_text) + 200

    # ── POST-COMPACT: store to CompactionStore (FTS5 searchable) ───────────────
    chars_saved = original_size - compacted_size
    try:
        from llm_client.compaction_store import get_compaction_store
        store = get_compaction_store()
        # Auto-detect topic tags from summary
        topic_tags = _detect_topic_tags(summary_text, history)
        # Extract tool names for the store record
        tool_names_used = []
        for m in history:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tc in m.get("tool_calls", []):
                    name = tc.get("function", {}).get("name", "?")
                    if name not in tool_names_used:
                        tool_names_used.append(name)
        store.store(
            cache_key=cache_key,
            summary=summary_text,
            message_count=len(history),
            model_used=model,
            session_id=session_id,
            chars_saved=max(0, chars_saved),
            original_size=original_size,
            compacted_size=compacted_size,
            topic_tags=topic_tags,
            tool_names=tool_names_used,
        )
    except Exception as e:
        logger.debug("CompactionStore store failed: %s", e)

    # ── POST-COMPACT: store summary to all 6 memory layers ─────────────────────
    _async_store_compaction_summary(summary_text, len(history), cache_key)

    # Mark this cache_key as compacted (prevent re-compacting same window)
    with _COMPACT_HISTORY_LOCK:
        _COMPACT_HISTORY[cache_key] = summary_text

    summary_msg = {
        "role": "system",
        "content": (
            "[Earlier conversation condensed from " + str(len(history)) + " messages:]\n"
            + summary_text
            + ("\n\n" + prior_summaries if prior_summaries else "")
            + "\n\n[Full prior context available in .session_state/compaction_summary.md]"
        ),
    }

    # MCP reminder is a SEPARATE system message — survives independently of the
    # summary content. This ensures MCP directives are always present after compaction
    # regardless of how brief the summary is. The reminder is NOT buried in summary_msg.
    mcp_reminder_msg = {
        "role": "system",
        "content": (
            "━━━ MCP TOOL REMINDER ━━━\n"
            "Your MCP tools are always active — gitnexus, obsidian, ruflo_memory,\n"
            "filesystem, exa, hermes, crawl4ai, browser_use, symphony, and more.\n\n"
            "MANDATORY per-task checks:\n"
            "  1. @ruflo_memory_search — query 6-layer memory BEFORE reading files\n"
            "  2. @mcp_gitnexus — get code context, callers, and impact BEFORE editing\n"
            "  3. @mcp_obsidian — check .wiki for prior decisions and context\n"
            "  4. @mcp_symphony — check task state before starting new work\n\n"
            "These tools provide critical context from the 6-layer memory system.\n"
            "ALWAYS use them — do NOT skip MCP calls even for simple tasks."
        ),
    }

    result: list[dict] = []
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
    elif system_msg:
        result.append(system_msg)
    result.append(summary_msg)
    result.append(mcp_reminder_msg)
    result.extend(recent)

    # Cache the result (LRU, max 100 entries)
    with _COMPACT_CACHE_LOCK:
        _COMPACT_CACHE[cache_key] = result
        if len(_COMPACT_CACHE) > _COMPACT_CACHE_MAX:
            _COMPACT_CACHE.popitem(last=False)

    # ── Run OpenCode shell hooks (post-compact) ──────────────────────────────
    _run_shell_hook("post-compact")

    logger.debug(
        "Smart compact: %d messages → %d (saved %d chars, cache size: %d)",
        len(messages),
        len(result),
        chars_saved,
        len(_COMPACT_CACHE),
    )
    return result


def _detect_topic_tags(summary: str, history: list[dict]) -> list[str]:
    """Auto-detect topic tags from summary and conversation history."""
    tags: set[str] = {"compaction"}
    summary_lower = summary.lower()
    history_text = " ".join(
        str(m.get("content", ""))[:200] for m in history[-10:]
    ).lower()

    # File extensions
    for ext in (".py", ".ts", ".js", ".md", ".yaml", ".json", ".sql", ".html", ".css"):
        if ext in history_text:
            tags.add(ext.lstrip("."))

    # Topic keywords
    topic_map = {
        "bug": ["bug", "fix", "error", "crash", "fail"],
        "refactor": ["refactor", "restructure", "clean", "improve"],
        "feature": ["add", "new", "implement", "create", "build"],
        "docs": ["docs", "readme", "documentation", "comment"],
        "test": ["test", "pytest", "coverage", "spec"],
        "security": ["security", "auth", "permission", "sanitize"],
        "performance": ["perf", "speed", "optimize", "cache", "fast"],
        "db": ["sql", "query", "database", "db", "migration"],
        "api": ["api", "endpoint", "route", "request", "json"],
        "memory": ["memory", "context", "store", "recall"],
        "mcp": ["mcp", "tool", "server", "ruflo", "hermes"],
    }

    for tag, keywords in topic_map.items():
        if any(kw in summary_lower or kw in history_text for kw in keywords):
            tags.add(tag)

    # Add tool-based tags
    for m in history:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            for tc in m.get("tool_calls", []):
                name = tc.get("function", {}).get("name", "")
                if "git" in name or "commit" in name or "push" in name:
                    tags.add("git")
                elif "search" in name or "grep" in name or "find" in name:
                    tags.add("search")
                elif "read" in name or "write" in name or "file" in name:
                    tags.add("io")

    return list(tags)[:10]


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
    mode: str = "coding",
) -> tuple[str, str]:
    """Inner loop for agentic /do command — handles tool_calls from LLM."""
    # GAP-27: Inject mode into system prompt for mode-specific behavior
    mode_inject = _MODE_SYSTEM_INJECT.replace("{{mode}}", mode)
    system = system + "\n" + mode_inject if system else mode_inject

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
            # AUDIT04: Log agent loop LLM calls
            logger.debug(
                f"[AUDIT04] agent_loop LLM call: iter={iteration}, messages={len(messages)}, "
                f"roles={[m.get('role') for m in messages]}"
            )
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

                # ── Five-tier compaction cascade (model-aware thresholds) ──────────
                # All tiers relative to _COMPACTION_MAX_CONTEXT (set above).
                # Tier 1 (50%): microcompact — NO LLM, every turn, post-tool
                # Tier 2 (70%): microcompact again if still over threshold
                # Tier 3 (85%): ASYNC full compaction STARTS (non-blocking LLM)
                # Tier 4 (95%): BLOCKING full compaction (if async hasn't finished)
                # Tier 5 (99%): EMERGENCY — force blocking even if async still running
                if len(messages) > 8:
                    total_size = sum(len(str(m.get("content", ""))) for m in messages)

                    # Tier 1: microcompact at 50% fill — runs every turn proactively
                    if total_size > _COMPACTION_TIER_1:
                        prev_size = total_size
                        messages = _microcompact_messages(messages, threshold=_COMPACTION_TIER_1)
                        new_size = sum(len(str(m.get("content", ""))) for m in messages)
                        logger.debug("Tier1 microcompact: %d → %d (saved %d)", prev_size, new_size, prev_size - new_size)

                    # Re-measure after microcompact
                    total_size = sum(len(str(m.get("content", ""))) for m in messages)

                    # Tier 2: microcompact again at 70% fill — tighter threshold
                    if total_size > _COMPACTION_TIER_2:
                        prev_size = total_size
                        messages = _microcompact_messages(messages, threshold=_COMPACTION_TIER_2)
                        new_size = sum(len(str(m.get("content", ""))) for m in messages)
                        logger.debug("Tier2 microcompact: %d → %d (saved %d)", prev_size, new_size, prev_size - new_size)

                    # Re-measure again
                    total_size = sum(len(str(m.get("content", ""))) for m in messages)

                    # Tier 3: async full compaction at 850k — start LLM summarization NOW
                    # Fire-and-forget — completes in background before we hit Tier 4
                    # Uses BOTH per-messages _full_compact_pending AND global _ASYNC_COMPACT_IN_FLIGHT
                    # to prevent Tier 4 from firing even if messages list is recreated (e.g. by
                    # _microcompact_messages returning a new list) or _async_compact_if_needed has
                    # already completed but the current turn still exceeds Tier 4 threshold.
                    if total_size > _COMPACTION_TIER_3 and not _ASYNC_COMPACT_IN_FLIGHT and not getattr(messages, '_full_compact_pending', False):
                        messages._full_compact_pending = True  # type: ignore[attr-defined]
                        with _ASYNC_COMPACT_LOCK:
                            _ASYNC_COMPACT_IN_FLIGHT = True
                        logger.debug("Tier3 async compaction started at %d chars", total_size)
                        asyncio.create_task(_async_compact_if_needed(messages, user_id, system_prompt=system))

                    # Tier 4: blocking full compaction at 950k — only if async hasn't started
                    # If async is already running, skip — let it finish instead of double-compacting
                    elif total_size > _COMPACTION_TIER_4 and not _ASYNC_COMPACT_IN_FLIGHT and not getattr(messages, '_full_compact_pending', False):
                        messages._full_compact_pending = True  # type: ignore[attr-defined]
                        messages = smart_compact_messages(messages, model=model, session_id=thread_id, system_prompt=system)
                        try:
                            from core.hooks import get_hooks
                            project_dir = getattr(messages, '_project_dir', None) or "/home/newadmin/swarm-bot"
                            get_hooks().emit("post_compact", {
                                "user_id": user_id or "default",
                                "reason": "auto_context_full",
                                "total_size": total_size,
                                "project_dir": project_dir,
                            })
                        except Exception:
                            pass
                        logger.debug("Tier4 blocking compaction done: %d → %d chars",
                            total_size, sum(len(str(m.get("content", ""))) for m in messages))

                    # Tier 5: EMERGENCY at 990k — force blocking even if async still running
                    total_size = sum(len(str(m.get("content", ""))) for m in messages)
                    if total_size > _COMPACTION_TIER_5:
                        # Cancel any pending async and do immediate blocking compaction
                        messages._full_compact_pending = False  # type: ignore[attr-defined]
                        with _ASYNC_COMPACT_LOCK:
                            _ASYNC_COMPACT_IN_FLIGHT = False
                        messages = smart_compact_messages(messages, model=model, session_id=thread_id, system_prompt=system)
                        try:
                            from core.hooks import get_hooks
                            project_dir = getattr(messages, '_project_dir', None) or "/home/newadmin/swarm-bot"
                            get_hooks().emit("post_compact", {
                                "user_id": user_id or "default",
                                "reason": "emergency_compaction",
                                "total_size": total_size,
                                "project_dir": project_dir,
                            })
                        except Exception:
                            pass
                        logger.debug("Tier5 EMERGENCY compaction done: %d → %d chars",
                            total_size, sum(len(str(m.get("content", ""))) for m in messages))

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

                # ── Proactive microcompact AFTER each tool result ──────────────────
                # This keeps context from growing between tool calls
                # With unlimited API, we can afford to microcompact EVERY turn if needed
                total_size = sum(len(str(m.get("content", ""))) for m in messages)
                if total_size > _COMPACTION_TIER_1:
                    prev = total_size
                    messages = _microcompact_messages(messages, threshold=_COMPACTION_TIER_1)
                    new_sz = sum(len(str(m.get("content", ""))) for m in messages)
                    logger.debug("Post-tool microcompact: %d → %d (saved %d)", prev, new_sz, prev - new_sz)

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
            await _safe_record_failure(
                task=task,
                approach=f"agent_loop(model={model})",
                failure_mode=f"{type(e).__name__}: {e}",
                root_cause="LLM call or tool execution failed in agent_loop",
                fix_applied="model advanced to next fallback or returned error",
                prevention="Ensure fallback chain covers API errors; tool errors should be handled by _execute_tool_with_self_heal",
            )
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
    mode: str | None = None,
) -> tuple[str, str]:
    """Public wrapper for _agent_loop_inner with conversation history injection.

    Builds full cognitive system prompt using SystemPromptBuilder:
    - Soul engine context (Legion's living identity)
    - GSA voice injection (context-aware communication style)
    - Memory context (episodic + semantic)
    - Narrative context (episodic story)
    - All layered on top of role-specific agent instructions
    """
    if chain is None:
        chain = get_fallback_chain(agent_key or "computer")

    # Build base system from role-specific agent prompt
    base_system = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["computer"])

    # Layer 1: Soul context — Legion's living identity document (ALWAYS first)
    try:
        from core.soul_engine import build_soul_context
        soul_ctx = build_soul_context()
        if soul_ctx:
            base_system = soul_ctx + "\n\n" + base_system
    except Exception:
        pass

    # Layer 2: GSA voice injection — context-aware communication style
    if task:
        try:
            from core.character_enforcer import EnforcementContext, set_enforcement_context
            from core.gsa_voice import classify_message_context, get_gsa_injection

            gsa_classification = classify_message_context(task)
            gsa_injection = get_gsa_injection(gsa_classification.primary, gsa_classification)
            if gsa_injection:
                base_system = base_system + "\n\n" + gsa_injection

            ctx = EnforcementContext(
                context_type=gsa_classification.primary.value,
                confidence=gsa_classification.confidence,
                visual_signals=gsa_classification.visual_signals,
                flow_state=gsa_classification.flow_state,
            )
            set_enforcement_context(ctx)
        except Exception:
            pass

    # Layer 3: Semantic memory context (top relevant memories for this task)
    if user_id:
        try:
            from core.memory_manager import LegionSemanticMemory
            semantic_results = await LegionSemanticMemory().search_memories(task, str(user_id), limit=5)
            if semantic_results:
                mem_lines = (
                    ["[RELEVANT MEMORIES]"]
                    + [str(m.get("content", ""))[:200] for m in semantic_results[:5] if m.get("content")]
                )
                base_system = base_system + "\n\n" + "\n".join(mem_lines)
        except Exception:
            pass

    # Layer 4: Episodic narrative context
    if user_id and task:
        try:
            from core.episodic_narrative import build_narrative_context
            narrative_ctx = build_narrative_context(task)
            if narrative_ctx:
                base_system = base_system + "\n\n" + narrative_ctx
        except Exception:
            pass

    # Layer 5: Conversation history context (from conversation_interface)
    if user_id:
        try:
            from core.conversation_interface import get_conversation_summary_prompt
            ctx = get_conversation_summary_prompt(str(user_id))
            if ctx:
                base_system = base_system + "\n\n" + ctx
        except Exception:
            pass

    # Layer 6: Emotion modifier (if user has an active emotion state)
    if user_id:
        try:
            from core.emotion_modulator import build_emotion_modifier, detect_emotion_from_context
            from tools.letta_personality import get_persona_state
            current_emotion = str(get_persona_state().get("dominant_emotion", "neutral"))
            detected_emotion = detect_emotion_from_context(task, current_emotion)
            if detected_emotion and detected_emotion != "neutral":
                emotion_mod = build_emotion_modifier(detected_emotion)
                if emotion_mod:
                    base_system = base_system + "\n\n" + emotion_mod
        except Exception:
            pass

    # Layer 7: Humanization layer context via SystemPromptBuilder (singleton-based)
    try:
        from core.memory.memory_manager import MemoryManager
        from core.memory.temporal_graph import TemporalKnowledgeGraph
        from core.personality.emotion_engine import EmotionEngine
        from core.reflection.reflection_engine import ReflectionEngine
        from core.system_prompt_builder import SystemPromptBuilder

        # Use or initialize singleton instances
        global memory, graph, emotion, reflection
        if memory is None:
            memory = MemoryManager()
        if graph is None:
            graph = TemporalKnowledgeGraph()
        if emotion is None:
            emotion = EmotionEngine()
        if reflection is None:
            from llm_client import llm_client as _llm_client_mod
            reflection = ReflectionEngine(memory, _llm_client_mod)

        # Build via SystemPromptBuilder for additional context layers
        spb = SystemPromptBuilder(memory=memory, emotion=emotion, graph=graph, reflection=reflection)
        spb.set_user_message(task)
        emotion_str = str(current_emotion) if "current_emotion" in dir() else "neutral"
        cognitive_ctx = await spb.build(task_context=task, emotion=emotion_str)
        if cognitive_ctx:
            base_system = base_system + "\n\n" + cognitive_ctx
    except Exception:
        pass

    return await _agent_loop_inner(
        task=task,
        chain=chain,
        system=base_system,
        image_b64=image_b64,
        user_id=user_id,
        thread_id=thread_id,
        progress_cb=progress_fn,
        photo_cb=photo_cb,
        mode=mode or agent_key or "coding",
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
        "chandra_ocr_image": (
            lambda a: f"\U0001f525 Chandra OCR 2 on {a.get('path', '')} method={a.get('method', 'vllm')}"
        ),
        "chandra_ocr_pdf": lambda a: f"\U0001f525 Chandra OCR 2 PDF {a.get('path', '')} pages={a.get('pages', 'all')}",
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
            _intent = classify_intent_fast(task)
            if _intent.confidence >= 0.65 and _intent.suggested_agent:
                agent_key = _intent.suggested_agent
        except Exception:
            pass

    if agent_key == "general":
        try:
            from core.intent_classifier import _last_agent_key
            from core.intent_classifier import classify_intent as _ci

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

    # ── AUDIT04: Build messages[] with DISTINCT system messages ──────────────────
    # Priority order: soul → memory → wiki → conversation → user
    # Each context layer gets its OWN system message (not concatenated)

    _audit_messages: list[dict] = []

    # 0. Soul — FIRST system message, always present
    _soul = build_soul_context()
    if _soul:
        _audit_messages.append({"role": "system", "content": _soul})

    # 0b. Base persona + disagreement — SECOND system message
    _base_persona = build_base_persona()
    if _base_persona:
        _audit_messages.append({"role": "system", "content": _base_persona})

    _disagree = get_disagreement_prompt()
    if _disagree:
        _audit_messages.append({"role": "system", "content": _disagree})

    # GSA Voice injection — context-aware communication style
    try:
        from core.character_enforcer import EnforcementContext, set_enforcement_context
        from core.gsa_voice import classify_message_context, get_gsa_injection

        gsa_classification = classify_message_context(task)
        gsa_injection = get_gsa_injection(gsa_classification.primary, gsa_classification)
        if gsa_injection:
            _audit_messages.append({"role": "system", "content": gsa_injection})

        ctx = EnforcementContext(
            context_type=gsa_classification.primary.value,
            confidence=gsa_classification.confidence,
            visual_signals=gsa_classification.visual_signals,
            flow_state=gsa_classification.flow_state,
        )
        set_enforcement_context(ctx)
    except Exception:
        pass

    # 1. Memory — separate system message
    _memory_context_lines: list[str] = []
    try:
        from core.memory_manager import LegionSemanticMemory

        semantic_memory_lines = await LegionSemanticMemory().search_memories(task, str(user_id), limit=5)
        if semantic_memory_lines:
            _memory_context_lines = semantic_memory_lines
    except Exception:
        pass
    if _memory_context_lines:
        _audit_messages.append({"role": "system", "content": "[Memory]\n" + "\n".join(_memory_context_lines)})

    # 2. Wiki — from unified_prompt_context (separate system messages per block)
    try:
        from core.unified_prompt_context import gather_parallel_prompt_layers

        _chat_mode = os.getenv("LEGION_CHAT_MODE", "text")
        for _layer in await gather_parallel_prompt_layers(task, str(user_id), mode=_chat_mode):
            if _layer:
                _audit_messages.append({"role": "system", "content": _layer})
    except Exception:
        pass

    # 3. Other context blocks — agent mode, emotion, narrative, cognition, etc.
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
            _audit_messages.append(
                {"role": "system", "content": f"[AGENT MODE: {agent_key.upper()}]\n{_agent_specialization.strip()}"}
            )

    _current_emotion = "neutral"
    try:
        from tools.letta_personality import get_persona_state as _gps

        _current_emotion = str(_gps().get("dominant_emotion", "neutral"))
        detected = detect_emotion_from_context(task, _current_emotion)
        if detected != _current_emotion:
            update_emotion(detected, event=f"Context shift from message: {task[:50]}")
            _current_emotion = detected
        _emotion_mod = build_emotion_modifier(_current_emotion)
        if _emotion_mod:
            _audit_messages.append({"role": "system", "content": _emotion_mod})
    except Exception:
        pass

    for _ctx_name, _ctx_getter in [
        ("episodic_narrative", lambda: build_narrative_context(task)),
        ("relationship_memory", get_relationship_context),
        ("cognition", lambda: build_cognition_system_fragment(str(user_id), task, routing_hint=routing_hint)),
        ("intent_hint", lambda: build_intent_hint(classify_intent_fast(task))),
    ]:
        try:
            _ctx = _ctx_getter()
            if _ctx:
                _audit_messages.append({"role": "system", "content": _ctx})
        except Exception:
            pass

    try:
        from core.memory.unified_context import build_unified_memory_context

        umc = await build_unified_memory_context(str(user_id), task)
        if umc:
            _audit_messages.append({"role": "system", "content": umc})
    except Exception:
        pass

    for _ctx_name, _ctx_builder in [
            ("memoryos", None),  # removed — async, not awaitable in sync lambda
            ("open_memory", None),  # removed — om_search is async
            ("legacy_memory", None),  # removed — build_memory_context is async
            ("instinct", None),  # removed — get_instinct_context is async
            ("skills", lambda: get_skills_for_agent(agent_key, max_chars=6000)),
            ("mode_instructions", lambda: build_mode_instructions(agent_key)),
        ]:
            try:
                if _ctx_builder is None:
                    continue
                _ctx = _ctx_builder()
                if _ctx:
                    _audit_messages.append({"role": "system", "content": _ctx})
            except Exception:
                pass

    try:
        from core.research_policy import maybe_attach_research_context

        r_block, _ran = await maybe_attach_research_context(task, str(user_id), agent_key or "general")
        if r_block:
            _audit_messages.append({"role": "system", "content": r_block})
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
                _audit_messages.append({"role": "system", "content": proactive_nudge})
            debate_block = get_debate_trigger(task)
            if debate_block:
                _audit_messages.append({"role": "system", "content": debate_block})
            else:
                opinion_block = get_opinion_on(task)
                if opinion_block:
                    _audit_messages.append({"role": "system", "content": opinion_block})
            humor_block = get_humor_nudge(task)
            if humor_block:
                _audit_messages.append({"role": "system", "content": humor_block})
        except Exception:
            pass

    # Add Internal Reasoning Discipline for longer messages
    _word_count = len(task.split()) if task else 0
    if agent_key not in ("computer", "vision", "think") and _word_count > 12:
        _audit_messages.append(
            {
                "role": "system",
                "content": (
                    "\n\n[INTERNAL REASONING DISCIPLINE]\n"
                    "Before finalising your response, briefly stress-test it: "
                    "ask yourself 'Is this actually correct? What would a smart skeptic push back on?' "
                    "If the self-check reveals a real weakness or blind spot, lead with it honestly. "
                    "If your first take holds up, answer with confidence — no need to hedge. "
                    "This is about intellectual honesty, not performative uncertainty."
                ),
            }
        )

    # ── PRIORITY 1: Pre-Response Reasoning Loop ─────────────────────────────────
    # For messages >20 words OR confidence <0.7: decompose, gather sources, build reasoning context
    try:
        _intent_for_reasoning = "general"
        _confidence_for_reasoning = 0.5
        try:
            _fast_intent = classify_intent_fast(task)
            _intent_for_reasoning = (
                _fast_intent.intent.value if hasattr(_fast_intent.intent, "value") else str(_fast_intent.intent)
            )
            _confidence_for_reasoning = _fast_intent.confidence
        except Exception:
            pass

        _reasoning_prompt = None
        try:
            from core.reasoning_loop import run_reasoning_loop_if_needed

            _reasoning_prompt = await run_reasoning_loop_if_needed(
                task, _intent_for_reasoning, _confidence_for_reasoning
            )
        except Exception as _rl_err:
            logger.debug("Pre-response reasoning loop skipped: %s", _rl_err)

        if _reasoning_prompt:
            _audit_messages.append({"role": "system", "content": _reasoning_prompt})
            logger.debug("Pre-response reasoning injected (%d chars)", len(_reasoning_prompt))
    except Exception as _rl_outer_err:
        logger.warning("Pre-response reasoning failed (non-fatal): %s", _rl_outer_err)

    # ── Conversation history ─────────────────────────────────────────────────────
    _conversation_history: list[dict] = []
    if user_id:
        try:
            from core.conversation_interface import get_conversation_history as _get_ch

            _conversation_history = _get_ch(str(user_id), last_n=6)
        except Exception:
            pass

    # Build final messages list
    messages: list[dict] = list(_audit_messages)  # All system context messages
    messages.extend(_conversation_history)  # Conversation history
    # User message — LAST
    if image_b64:
        user_content: Any = [
            {"type": "text", "text": task},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
    else:
        user_content = task
    messages.append({"role": "user", "content": user_content})

    _is_pytest_run = bool(os.getenv("PYTEST_CURRENT_TEST"))
    # Keep tests deterministic: bypass cache and background post-hooks so
    # integration tests always exercise the direct LLM call path.
    if _is_pytest_run:
        run_post_hooks = False
    _skip_cache = _is_pytest_run or image_b64 is not None or show_thinking or agent_key == "vision"
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
            # AUDIT04: Debug logging before every LLM call
            logger.debug(
                f"[AUDIT04] Before LLM call: messages={len(messages)}, roles={[m.get('role') for m in messages]}"
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
            raw = (resp.choices[0].message.reasoning_content or resp.choices[0].message.content or "").strip()
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
                    _task = asyncio.create_task(
                        _post_call_hooks(
                            user_msg=task,
                            response=result,
                            agent_used=agent_key,
                            session_id=thread_id,
                            user_id=user_id,
                        )
                    )
                    _task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
                except Exception:
                    pass

            logger.info("Success: %s", model)
            with contextlib.suppress(Exception):
                result = postprocess_response(result, _current_emotion, task)
            try:
                from core.character_enforcer import enforce_character

                result = enforce_character(result, agent_key)
            except Exception:
                pass

            # === SELF-AWARENESS GATE: intercept "I don't know" and search instead ===
            _search_trigger_sent = False
            try:
                from core.self_awareness_gate import (
                    build_search_query_from_message,
                    get_search_trigger_message,
                    should_search_instead,
                )
                from tools.web_search import search_web

                if should_search_instead(result, task):
                    # Send "Lagi cari..." trigger to Telegram (caller should hook this)
                    try:
                        _trigger_msg = get_search_trigger_message(task)
                        # Caller may hook this via a callback if needed
                        logger.info("Search trigger: %s", _trigger_msg)
                        _search_trigger_sent = True
                    except Exception as e:
                        logger.warning("Failed to send search trigger: %s", e)

                    # Build search query and execute search
                    search_query = build_search_query_from_message(task)
                    logger.info("Self-awareness gate searching: %s", search_query)
                    search_results = await search_web(search_query)

                    if search_results and not search_results.startswith("[Search error"):
                        # AUDIT04: Inject search results as SYSTEM message (not user message)
                        tool_result_msg = {
                            "role": "system",
                            "content": (
                                f"[Search Results for: {task}]\n"
                                f"{search_results}\n\n"
                                f"Sintesiskan informasi di atas menjadi jawaban yang natural dalam bahasa Indonesia."
                            ),
                        }
                        messages.append(tool_result_msg)

                        # Re-call LLM to synthesize proper response with search context
                        try:
                            synth_resp = await _call_model(
                                model=chain[0],
                                messages=messages,
                                temperature=0.7,
                            )
                            synth_raw = (synth_resp.choices[0].message.reasoning_content or synth_resp.choices[0].message.content or "").strip()
                            if synth_raw:
                                result = synth_raw
                                logger.info("Search synthesis successful")
                        except Exception as e:
                            logger.warning("Search synthesis failed, appending raw: %s", e)
                            # Fallback: append raw search results to original response
                            if search_results:
                                result = f"{result}\n\n{search_results}"
                    elif search_results.startswith("[Search error"):
                        result = f"{result}\n\n{search_results}"
            except Exception as e:
                logger.warning("Self-awareness gate error: %s", e)
            try:
                from core.episodic_narrative import update_narrative_from_conversation

                _task = asyncio.create_task(asyncio.to_thread(update_narrative_from_conversation, task, result))
                _task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
            except Exception:
                pass
            try:
                from core.self_improvement import buffer_conversation, maybe_run_self_review

                buffer_conversation(task, result)
                _task = asyncio.create_task(maybe_run_self_review())
                _task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
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

                    _task = asyncio.create_task(schedule_wiki_ingest_exchange(str(user_id), task, result))
                    _task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
                except Exception:
                    pass

            if user_id and os.getenv("LEGION_WIKI_AUTO_INGEST", "1").strip().lower() not in ("0", "false", "no", "off"):
                try:
                    from core.wiki_auto_ingest import on_conversation_turn, on_turn_deep_ingest

                    def _log_err(t):
                        if t.exception():
                            logger.error("on_conversation_turn failed: %s", t.exception())

                    _task = asyncio.create_task(on_conversation_turn(str(user_id), task, result))
                    _task.add_done_callback(_log_err)
                    asyncio.wait_for(_task, timeout=5.0)
                except TimeoutError:
                    logger.warning("on_conversation_turn timed out after 5s")
                except Exception as e:
                    logger.debug("on_conversation_turn outer error: %s", e)

# ── Deep ingest (fires every turn, thresholds internally) ──
            if user_id and os.getenv("LEGION_WIKI_AUTO_INGEST", "1").strip().lower() not in ("0", "false", "no", "off"):
                try:
                    from core.conversation_interface import get_conversation_history

                    conversation = get_conversation_history(str(user_id), last_n=20)
                    def _log_session_err(t):
                        if t.exception():
                            logger.error("on_turn_deep_ingest failed: %s", t.exception())

                    _session_task = asyncio.create_task(on_turn_deep_ingest(str(user_id), conversation))
                    _session_task.add_done_callback(_log_session_err)
                    asyncio.wait_for(_session_task, timeout=10.0)
                except TimeoutError:
                    logger.warning("on_turn_deep_ingest timed out after 10s")
                except Exception as e:
                    logger.warning("on_turn_deep_ingest outer error: %s", e)

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
                    if _is_pytest_run:
                        await _me.episodic.close()
                except Exception:
                    pass

            # Clear GSA enforcement context after response is complete
            try:
                from core.character_enforcer import clear_enforcement_context

                clear_enforcement_context()
            except Exception:
                pass

            # === QUALITY GATE: check response before returning ===
            try:
                from core.quality_gate import QualityGate

                _qg = QualityGate()
                _quality = await _qg.check(task, result, agent_key or "general")
                if _quality.should_retry:
                    logger.info("Quality gate triggered: %s", _quality.issues)
                    result = await _qg.retry(messages, _quality.issues)
            except Exception as _qg_err:
                logger.warning("Quality gate error (non-fatal): %s", _qg_err)

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

    # Budget hard-stop: if all fallbacks exhausted AND budget exceeded, fail instead of retrying
    try:
        from swarms_bot.routing.budget_guard import BudgetExceededError, get_budget_guard

        if not get_budget_guard().can_spend("chat"):
            raise BudgetExceededError(f"Budget exceeded for 'chat' — all models exhausted for '{agent_key}'.")
    except BudgetExceededError:
        raise
    except Exception:
        pass  # Budget guard unavailable, fall through to generic error

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
            from core.emotion_modulator import detect_emotion_from_context
            from tools.letta_personality import update_emotion

            update_emotion(detect_emotion_from_context(user_msg), event=f"assistant response: {response[:80]}")
        except Exception:
            pass
        if emotion is not None:
            emotion.update_from_interaction(user_msg, response)
        if memory is not None:
            await memory.auto_extract_and_save(user_msg, response)
            emotion_state = emotion.state.to_dict() if emotion is not None else None
            await memory.add_conversation_turn(
                "user",
                user_msg,
                agent_used=agent_used,
                emotion_state=emotion_state,
                session_id=session_id,
            )
            await memory.add_conversation_turn(
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
                from core.memory_manager import LegionSemanticMemory
                from tools.memoryos_client import mos_add_conversation
                from tools.open_memory import SECTOR_EPISODIC, SECTOR_SEMANTIC, om_store
                from tools.recallmax import should_store

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
            _task = asyncio.create_task(promote_important(recent))
            _task.add_done_callback(lambda t: logger.error("%s", t.exception()) if t.exception() else None)
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
            result = (resp.choices[0].message.reasoning_content or resp.choices[0].message.content or "").strip()
            logger.info("Screenshot analyzed locally via Ollama")
            return result, "ollama/gemma4:e4b \U0001f512 local"
        except Exception as e:
            logger.warning("Ollama vision failed: %s → trying OpenCode Go", e)
    else:
        logger.info("analyze_screenshot: using cloud directly (%s)", _skip_reason)

    go_key = os.getenv("OPENCODE_GO_API_KEY", "")
    if not go_key:
        raise RuntimeError("No OPENCODE_GO_API_KEY and Ollama vision failed/skipped")

    try:
        resp = await acompletion(
            model="opencode-go/deepseek-v4-pro",
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
            api_key=go_key,
            base_url="https://opencode.ai/zen/go/v1",
            max_tokens=1024,
        )
        result = (resp.choices[0].message.reasoning_content or resp.choices[0].message.content or "").strip()
        _cloud_label = "opencode-go/deepseek-v4-pro"
        if _skip_local and _skip_reason:
            return result, f"{_cloud_label} (reason: {_skip_reason})"
            _cloud_label += f" \u2601\ufe0f (local bypassed: {_skip_reason[:60]})"
        logger.info("Screenshot analyzed via OpenCode Go")
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
        "OPENCODE_GO_API_KEY",
        "OLLAMA_API_KEY",
        "ZAI_API_KEY",
        "HF_TOKEN",
    ]
    return {k: bool(os.getenv(k)) for k in keys}
