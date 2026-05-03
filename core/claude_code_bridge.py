"""Bidirectional bridge between Claude Code and OpenCode/LegionBot."""
from __future__ import annotations

import asyncio
import os
import re
import shutil
from pathlib import Path
from typing import Any

CLAUDE_CODE_CLI = shutil.which("claude") or str(Path.home() / ".claude/bin/claude")
OPENCODE_CLI = "/home/newadmin/.opencode/bin/opencode"

async def run_claude_task(
    prompt: str,
    timeout: int = 180,
    model: str | None = None,
) -> dict[str, Any]:
    """Run a task via Claude Code CLI and return result."""
    import time
    full_prompt = f"{prompt}\n\nRespond concisely. End with RESULT: <your answer>."
    if os.getenv("LEGION_GITNEXUS_PROMPT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.gitnexus_bridge import build_gitnexus_prompt_context

            gitnexus_ctx = await build_gitnexus_prompt_context(prompt, max_chars=1600)
            if gitnexus_ctx:
                full_prompt = f"{gitnexus_ctx}\n\n{full_prompt}"
        except Exception:
            full_prompt = f"{prompt}\n\nRespond concisely. End with RESULT: <your answer>."
    started = time.monotonic()

    try:
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_CODE_CLI, "-p", full_prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return {"output": "", "error": f"timeout after {timeout}s", "latency_ms": 0, "success": False}

        latency_ms = (time.monotonic() - started) * 1000
        return {
            "output": stdout.decode()[:2000] if stdout else "",
            "error": stderr.decode()[:500] if stderr else "",
            "latency_ms": latency_ms,
            "success": proc.returncode == 0,
        }
    except FileNotFoundError:
        return {"output": "", "error": f"claude CLI not found at {CLAUDE_CODE_CLI}", "latency_ms": 0, "success": False}
    except Exception as exc:
        return {"output": "", "error": str(exc), "latency_ms": 0, "success": False}

DIRECTIVE_RE = re.compile(r"@claude[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)

def extract_claude_directive(text: str) -> str | None:
    """Extract @claude directive from text."""
    m = DIRECTIVE_RE.search(text)
    return m.group(1).strip() if m else None

async def spawn_claude_from_opencode(
    task_result: str,
    depth: int = 0,
    max_depth: int = 3,
) -> dict[str, Any]:
    """Check OpenCode result for @claude directive, spawn Claude Code if found."""
    directive = extract_claude_directive(task_result)
    if not directive:
        return {"spawned": False, "reason": "no @claude directive found"}

    if depth >= max_depth:
        return {"spawned": False, "reason": f"max depth {max_depth} reached"}

    result = await run_claude_task(f"Execute this sub-task: {directive}", timeout=120)
    return {
        "spawned": True,
        "directive": directive,
        "result": result,
        "depth": depth,
    }
