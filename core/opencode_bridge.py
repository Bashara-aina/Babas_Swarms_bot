"""core/opencode_bridge.py — Telegram → OpenCode bridge."""

import asyncio
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

DIRECTIVES_RE = re.compile(r"@(legion|claude)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)


def extract_directives(text: str) -> list[tuple[str, str]]:
    """Extract @legion and @claude directives from text."""
    return [(m.group(1).lower(), m.group(2).strip()) for m in DIRECTIVES_RE.finditer(text)]


def build_opencode_prompt(telegram_msg: str, project: str, user: str) -> str:
    """Construct the full prompt passed to opencode CLI."""
    return f"""
You are Legion, Bashara's autonomous coding agent.
Triggered by Telegram message from: {user}
Target project: {project}
Time: {datetime.now().isoformat()}

INSTRUCTION FROM BASHARA:
{telegram_msg}

EXECUTE:
Follow the full LEGION MASTER PROMPT pipeline:
STAGE 0 (Understand) → STAGE 1 (Plan) → STAGE 2 (Implement) →
STAGE 3 (Verify) → STAGE 4 (Commit) → STAGE 5 (Report)

End your response with the REPORT FORMAT exactly as specified.
The report will be forwarded to Bashara's Telegram.
"""


async def run_opencode_task(
    prompt: str,
    project_dir: str | None = None,
    agent: str | None = None,
    model: str | None = None,
    timeout: int = 1800,
) -> str:
    """Execute a task via opencode CLI and return the result."""
    project_dir = project_dir or "/home/newadmin/swarm-bot"
    model = model or os.getenv("LEGION_DEFAULT_MODEL", "minimax-coding-plan/MiniMax-M2.7")

    cmd = ["/home/newadmin/.opencode/bin/opencode", "run", prompt]
    if agent:
        cmd.extend(["--agent", agent])
    cmd.extend(["--model", model])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=project_dir,
        env={
            **os.environ,
            "OPENCODE_DISABLE_AUTOUPDATE": "true",
        },
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return f"⛔ opencode task timed out after {timeout}s"

    if process.returncode != 0:
        await process.wait()
        return f"⛔ opencode error:\n{stderr.decode()[:2000]}"

    # Direct write of session summary after subprocess completes
    try:
        from core.wiki_bridge import opencode_write_session_summary

        await opencode_write_session_summary(
            session_id=f"task-{uuid.uuid4().hex[:8]}",
            task_description="opencode-task",
            actions_taken="",
            outcome=stdout.decode()[:2000],
        )
    except Exception:
        pass  # wiki bridge may be unavailable

    # Check for cross-system directives
    output = stdout.decode()
    try:
        callback_result = await handle_cross_system_callbacks(output)
        # Log callback results for debugging
        if callback_result.get("callbacks"):
            logger.info("cross-system callbacks triggered: %s", callback_result)
    except Exception:
        pass  # non-fatal

    return output


def extract_report(opencode_output: str) -> str:
    """Extract the LEGION TASK COMPLETE block from opencode output."""
    marker = "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if marker in opencode_output:
        idx = opencode_output.rfind(marker)
        report = opencode_output[idx - 500 :] if idx > 500 else opencode_output
        return report[:4000]
    return opencode_output[-2000:] if len(opencode_output) > 2000 else opencode_output


async def handle_cross_system_callbacks(
    text: str,
    depth: int = 0,
    max_depth: int = 3,
) -> dict[str, Any]:
    """Parse cross-system directives and spawn appropriate agents."""
    results = []
    directives = extract_directives(text)

    for directive_type, directive_value in directives:
        if directive_type == "claude":
            try:
                from core.claude_code_bridge import spawn_claude_from_opencode
                result = await spawn_claude_from_opencode(text, depth=depth, max_depth=max_depth)
                results.append({"type": "claude", **result})
            except Exception as exc:
                results.append({"type": "claude", "error": str(exc)})
        elif directive_type == "legion":
            try:
                from core.legion_callback_bridge import LegionCallbackBridge
                bridge = LegionCallbackBridge()
                result = await bridge.handle_legion_callback(text, depth=depth)
                results.append({"type": "legion", **result})
            except Exception as exc:
                results.append({"type": "legion", "error": str(exc)})

    return {"callbacks": results}
