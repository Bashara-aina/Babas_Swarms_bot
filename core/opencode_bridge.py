"""core/opencode_bridge.py — Telegram → OpenCode bridge."""

import asyncio
import json
import logging
import os
import re
import uuid
from collections.abc import AsyncGenerator
from typing import Any

logger = logging.getLogger(__name__)

DIRECTIVES_RE = re.compile(r"@(legion|claude)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)


def extract_directives(text: str) -> list[tuple[str, str]]:
    """Extract @legion and @claude directives from text."""
    return [(m.group(1).lower(), m.group(2).strip()) for m in DIRECTIVES_RE.finditer(text)]


async def run_opencode_task(
    prompt: str,
    project_dir: str | None = None,
    agent: str | None = None,
    timeout: int = 1800,
    task_desc: str | None = None,
) -> str:
    """Execute a task via opencode CLI and return the result."""
    project_dir = project_dir or "/home/newadmin/swarm-bot"
    model = os.getenv("LEGION_DEFAULT_MODEL", "minimax-coding-plan/MiniMax-M2.7")
    prompt_with_context = prompt
    context_files: list[str] = []

    # ── Memory context injection ─────────────────────────────────────────────
    if os.getenv("LEGION_MEMORY_INJECT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.memory.memory_injector import build_memory_context
            from pathlib import Path

            session_dir = Path(project_dir) / ".session_state"
            remembered_file = session_dir / "remembered_context.md"

            # Build fresh memory context (writes to remembered_context.md)
            query = task_desc or prompt[:100]
            ctx = build_memory_context(query=query, user_id="bashara")

            if ctx and remembered_file.exists():
                context_files.append(str(remembered_file))
                logger.debug("Memory context ready: %s (%d chars)", remembered_file, len(ctx))

            # Also inject compaction_summary.md if it exists — from smart_compact_messages
            compaction_file = session_dir / "compaction_summary.md"
            if compaction_file.exists() and compaction_file.stat().st_size > 0:
                context_files.append(str(compaction_file))
                logger.debug("Compaction summary injected: %s (%d bytes)", compaction_file, compaction_file.stat().st_size)
        except Exception as e:
            logger.debug("Memory context injection skipped: %s", e)
    # ── GitNexus context ───────────────────────────────────────────────────
    if os.getenv("LEGION_GITNEXUS_PROMPT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.gitnexus_bridge import build_gitnexus_prompt_context

            gitnexus_ctx = await build_gitnexus_prompt_context(prompt, max_chars=1800)
            if gitnexus_ctx:
                prompt_with_context = f"{gitnexus_ctx}\n\n{prompt}"
        except Exception:
            pass

    cmd = ["/home/newadmin/.opencode/bin/opencode", "run"]
    if agent:
        cmd.extend(["--agent", agent])
    cmd.extend(["--model", model])
    if context_files:
        for cf in context_files:
            cmd.extend(["-f", cf])
    cmd.append(prompt_with_context)

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
    except TimeoutError:
        process.kill()
        await process.wait()
        return f"⛔ opencode task timed out after {timeout}s"

    if process.returncode != 0:
        await process.wait()
        err_text = ANSI_RE.sub("", stderr.decode())
        return f"⛔ opencode error:\n{err_text[:2000]}"

    # Direct write of session summary after subprocess completes
    try:
        from core.wiki_bridge import opencode_write_session_summary

        await opencode_write_session_summary(
            session_id=f"task-{uuid.uuid4().hex[:8]}",
            task_description=task_desc or prompt[:200],
            actions_taken="",
            outcome=stdout.decode()[:2000],
        )
    except Exception:
        pass  # wiki bridge may be unavailable

    # GAP-12 FIX: Integrate ContextHealthMonitor into OpenCode flow
    # Run checkpoint after long-running opencode tasks to maintain session continuity
    try:
        if int(os.getenv("LEGION_CONTEXT_HEALTH_ENABLED", "1")):
            from core.context_health import get_context_monitor
            monitor = get_context_monitor("/home/newadmin/swarm-bot")
            health = monitor.assess()
            if monitor.should_checkpoint(health):
                await monitor.run_checkpoint(  # type: ignore[reportCallIssue]
                    session_description=f"opencode: {task_desc or prompt[:100]}",
                    task=f"OpenCode task: {prompt[:200]}",
                )
    except Exception:
        pass  # non-fatal, checkpoint is advisory

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


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def extract_report(opencode_output: str) -> str:
    """Extract the final report section from opencode output.

    Strips ANSI color codes first, then looks for markdown report headers
    near the end of output. Falls back to the tail if no markers found.
    """
    text = ANSI_RE.sub("", opencode_output)
    lines = text.split("\n")

    if len(text) < 500:
        return text[:4000]

    report_indicators = [
        "## REPORT",
        "## Summary",
        "## Result",
        "## Findings",
        "## Output",
        "## Conclusion",
        "## Recommendation",
        "## Next Steps",
        "LEGION TASK COMPLETE",
    ]

    report_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i >= len(lines) - 40 and any(stripped.startswith(ind) for ind in report_indicators):
            report_start = i
            break

    if report_start >= 0:
        report_section = "\n".join(lines[report_start:])
        return report_section[:4000]

    return text[-1500:] if len(text) > 1500 else text


SSE_DATA_RE = re.compile(r"^data: (.+)$")
SSE_EVENT_RE = re.compile(r"^event: (.+)$")


async def stream_opencode_task(
    prompt: str,
    project_dir: str | None = None,
    agent: str | None = None,
    timeout: int = 1800,
) -> AsyncGenerator[dict[str, Any]]:
    """Stream OpenCode output as SSE events.

    Yields dicts with keys: type (event|data|error|done), content, raw.
    type="done" marks final output with full stdout.
    """
    project_dir = project_dir or "/home/newadmin/swarm-bot"
    model = os.getenv("LEGION_DEFAULT_MODEL", "minimax-coding-plan/MiniMax-M2.7")
    prompt_with_context = prompt
    context_files: list[str] = []

    # ── Memory context injection ─────────────────────────────────────────────
    if os.getenv("LEGION_MEMORY_INJECT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.memory.memory_injector import build_memory_context
            from pathlib import Path

            session_dir = Path(project_dir) / ".session_state"
            remembered_file = session_dir / "remembered_context.md"

            query = prompt[:100]
            ctx = build_memory_context(query=query, user_id="bashara")

            if ctx and remembered_file.exists():
                context_files.append(str(remembered_file))
                logger.debug("Memory context ready: %s (%d chars)", remembered_file, len(ctx))
        except Exception as e:
            logger.debug("Memory context injection skipped: %s", e)

    # ── GitNexus context ───────────────────────────────────────────────────
    if os.getenv("LEGION_GITNEXUS_PROMPT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.gitnexus_bridge import build_gitnexus_prompt_context

            gitnexus_ctx = await build_gitnexus_prompt_context(prompt, max_chars=1800)
            if gitnexus_ctx:
                prompt_with_context = f"{gitnexus_ctx}\n\n{prompt}"
        except Exception:
            pass

    cmd = ["/home/newadmin/.opencode/bin/opencode", "run", "--stream"]
    if agent:
        cmd.extend(["--agent", agent])
    cmd.extend(["--model", model])
    if context_files:
        for cf in context_files:
            cmd.extend(["-f", cf])
    cmd.append(prompt_with_context)

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

    stderr_text = ""
    buffer = ""

    try:
        while True:
            try:
                chunk = await asyncio.wait_for(
                    process.stdout.read(1024),  # type: ignore[reportOptionalMemberAccess]
                    timeout=timeout,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                yield {"type": "error", "content": f"opencode stream timed out after {timeout}s", "raw": ""}
                return

            if not chunk:
                break

            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.rstrip("\r")

                sse_data = SSE_DATA_RE.match(line)
                sse_event = SSE_EVENT_RE.match(line)

                if sse_data:
                    raw = sse_data.group(1)
                    try:
                        content = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        content = raw
                    yield {"type": "data", "content": content, "raw": raw}
                elif sse_event:
                    yield {"type": "event", "content": sse_event.group(1), "raw": line}

        returncode = await process.wait()

        if returncode != 0:
            stderr_bytes = await asyncio.wait_for(process.stderr.read(), timeout=5)  # type: ignore[reportOptionalMemberAccess]
            stderr_text = ANSI_RE.sub("", stderr_bytes.decode())
            yield {"type": "error", "content": f"opencode exited {returncode}: {stderr_text[:500]}", "raw": stderr_text}
        else:
            yield {"type": "done", "content": None, "raw": ""}

    except Exception as exc:
        process.kill()
        await process.wait()
        yield {"type": "error", "content": str(exc), "raw": ""}


async def handle_cross_system_callbacks(
    text: str,
    depth: int = 0,
    max_depth: int = 3,
) -> dict[str, Any]:
    """Parse cross-system directives and spawn appropriate agents."""
    results = []
    directives = extract_directives(text)

    for directive_type, _directive_value in directives:
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
