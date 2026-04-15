"""core/memory/observation_capture.py — Hook integration for observation capture.

Hook events this module responds to:
  post_tool_use    — capture tool executions as observations
  command_received — capture commands with context
  post_llm_call    — capture LLM call metadata

This module does ZERO blocking work. All writes go through
observation_queue (fire-and-forget).

Observation types (taxonomy from claude-mem):
  decision  — architectural choices, tool selection rationale
  bugfix    — debugging findings, fix decisions
  feature   — new capabilities implemented
  refactor  — code restructuring
  discovery — interesting findings, learnings
  change    — modifications to existing systems

Privacy: <private> tags are stripped at write time in observation_store.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .observation_queue import Observation, get_observation_queue
from .observation_store import _should_skip_path

logger = logging.getLogger(__name__)

# Tools that are noise — skip observation capture
_SKIP_TOOLS = frozenset({
    "TodoWrite", "AskUserQuestion", "WebSearch", "WebFetch",
    "Glob", "Grep", "Read", "Bash",
    "mcp__github__get_pull_request",
    "mcp__github__list_issues",
})

# File extensions that indicate code changes
_CODE_EXTENSIONS = frozenset({
    ".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".swift", ".kt", ".scala",
    ".rb", ".php", ".html", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".md", ".txt", ".rst", ".tex",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".graphql", ".prisma",
    ".dockerfile", ".dockerignore",
    ".gitignore", ".env.example",
})


def _extract_files_from_tool(ctx: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Extract files_read and files_modified from a tool use context."""
    tool_name = ctx.get("tool", "")
    args = ctx.get("tool_args", {})
    result = ctx.get("tool_result", {})

    files_read: list[str] = []
    files_modified: list[str] = []

    # Read operations
    if tool_name in ("Read", "Glob", "Grep"):
        if "file_path" in args:
            files_read.append(str(args["file_path"]))
        if "path" in args:
            files_read.append(str(args["path"]))
        if "pattern" in args and "path" in args:
            files_read.append(str(args["path"]))

    # Write operations
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        if "file_path" in args:
            files_modified.append(str(args["file_path"]))

    # Bash operations that create/modify files
    if tool_name == "Bash":
        cmd = args.get("command", "")
        if ">" in cmd and "echo" in cmd:
            # echo ... > file
            parts = cmd.split(">")
            if len(parts) > 1:
                path = parts[1].strip().split()[0]
                if path and not path.startswith("-"):
                    files_modified.append(path)

    # From tool result — extract paths mentioned in output
    if isinstance(result, str):
        # Look for file paths in output (common patterns)
        path_pattern = re.findall(r"[\w\-\./]+(?:\.[a-zA-Z0-9]+)", result)
        for p in path_pattern:
            if any(p.endswith(ext) for ext in _CODE_EXTENSIONS):
                if p not in files_modified:
                    files_modified.append(p)

    # Filter noise
    files_read = [f for f in files_read if not _should_skip_path(f)]
    files_modified = [f for f in files_modified if not _should_skip_path(f)]

    return files_read, files_modified


def _classify_from_context(ctx: dict[str, Any]) -> str:
    """Classify observation type from hook context."""
    content = ctx.get("content", "") or ctx.get("prompt", "") or ""
    content_lower = content.lower()
    tool = ctx.get("tool", "")

    # Tool-specific classification
    if tool in ("Write", "Edit"):
        if "refactor" in content_lower or "restructure" in content_lower:
            return "refactor"
        return "feature"
    if tool == "Bash":
        if "fix" in content_lower or "patch" in content_lower:
            return "bugfix"
        if "test" in content_lower:
            return "discovery"
    if "error" in content_lower or "exception" in content_lower:
        return "bugfix"
    if any(k in content_lower for k in ["decide", "choose", "instead", "opted", "went with"]):
        return "decision"
    if any(k in content_lower for k in ["discovered", "found that", "interesting"]):
        return "discovery"

    return "discovery"


async def capture_tool_use(ctx: dict[str, Any]) -> dict[str, Any]:
    """Hook handler: post_tool_use — queue observation for non-blocking capture.

    This is the primary capture path. It extracts tool use context,
    classifies the observation type, and fires it to the async queue.
    Returns ctx unchanged (non-blocking).
    """
    tool = ctx.get("tool", "")
    if tool in _SKIP_TOOLS:
        return ctx

    session_id = ctx.get("session_id", "default")
    content = ctx.get("content", "") or ctx.get("prompt", "") or ""
    if not content:
        return ctx

    files_read, files_modified = _extract_files_from_tool(ctx)
    obs_type = _classify_from_context(ctx)

    # Build a narrative from the tool interaction
    tool_name = ctx.get("tool", "unknown")
    tool_args = ctx.get("tool_args", {})
    tool_result = ctx.get("tool_result", "")

    narrative_parts = [f"Used tool: {tool_name}"]
    if tool_args:
        # Truncate args for narrative
        args_str = str(tool_args)[:300]
        narrative_parts.append(f"Args: {args_str}")
    if tool_result:
        result_preview = str(tool_result)[:500]
        narrative_parts.append(f"Result: {result_preview}")

    narrative = "\n".join(narrative_parts)

    # Title from content — first meaningful line
    title = content.split("\n")[0][:120].strip() if content else f"Tool use: {tool_name}"

    obs = Observation(
        session_id=session_id,
        content=content,
        title=title,
        type=obs_type,
        narrative=narrative,
        files_read=files_read,
        files_modified=files_modified,
        tags=[tool_name.lower()],
    )

    queue = get_observation_queue()
    queue.enqueue(obs)
    return ctx


async def capture_command(ctx: dict[str, Any]) -> dict[str, Any]:
    """Hook handler: command_received — queue observation for command context."""
    session_id = ctx.get("session_id", "default")
    command = ctx.get("command", "")
    if not command:
        return ctx

    obs = Observation(
        session_id=session_id,
        content=f"Command received: {command}",
        title=f"/{command}" if not command.startswith("/") else command,
        type="discovery",
        narrative=f"User issued command: {command}",
    )

    queue = get_observation_queue()
    queue.enqueue(obs)
    return ctx


async def capture_decision(ctx: dict[str, Any]) -> dict[str, Any]:
    """Hook handler: post_llm_call — queue observation when LLM makes a decision.

    Detects decision language in LLM responses and queues them as decision observations.
    """
    if not ctx.get("success", True):
        return ctx

    response = ctx.get("response", "") or ctx.get("content", "") or ""
    if not response:
        return ctx

    decision_signals = [
        "instead of", "choosing", "decided to", "opted for",
        "went with", "rejected", "the approach is to",
        "best approach", "better to",
    ]

    response_lower = response.lower()
    if not any(signal in response_lower for signal in decision_signals):
        return ctx

    session_id = ctx.get("session_id", "default")

    # Extract the decision text — first sentence or paragraph
    sentences = response.split(".")
    decision_text = sentences[0] if sentences else response[:500]

    obs = Observation(
        session_id=session_id,
        content=decision_text,
        title=f"Decision: {decision_text[:100]}",
        type="decision",
        narrative=response[:1000],
    )

    queue = get_observation_queue()
    queue.enqueue(obs)
    return ctx


def register_observation_hooks() -> None:
    """Register all observation capture hooks on the global HookSystem."""
    from core.hooks import get_hooks

    hooks = get_hooks()
    hooks.register("post_tool_use", capture_tool_use, name="observation_capture_tool")
    hooks.register("command_received", capture_command, name="observation_capture_command")
    hooks.register("post_llm_call", capture_decision, name="observation_capture_decision")
    logger.info("Observation capture hooks registered")
