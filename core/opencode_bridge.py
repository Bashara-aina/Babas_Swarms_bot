"""core/opencode_bridge.py — Telegram → OpenCode bridge."""

import asyncio
import os
from datetime import datetime


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
    model = model or os.getenv("LEGION_DEFAULT_MODEL", "openrouter/anthropic/claude-sonnet-4-5")

    cmd = ["opencode", "run", prompt]
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

    return stdout.decode()


def extract_report(opencode_output: str) -> str:
    """Extract the LEGION TASK COMPLETE block from opencode output."""
    marker = "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if marker in opencode_output:
        idx = opencode_output.rfind(marker)
        report = opencode_output[idx - 500 :] if idx > 500 else opencode_output
        return report[:4000]
    return opencode_output[-2000:] if len(opencode_output) > 2000 else opencode_output
