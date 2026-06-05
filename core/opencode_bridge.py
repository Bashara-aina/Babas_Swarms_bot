"""core/opencode_bridge.py — Telegram → OpenCode bridge.

Memory architecture:
  Session start : build_persistent_context() → memory_inject.md (7 layers, once)
  Per task     : build_memory_context()      → recalled_context.md (6-layer recall)
  Post-compact : _recalled_context_refresh_hook → remembered_context.md (freshest recall)
  Compaction   : compaction_summary.md written by smart_compact_messages process
  All files injected via -f so OpenCode sees them as file context.
  GitNexus context is embedded in the prompt text (not via -f).
  Files are freshness-checked (<24h) before injection to prevent stale memory.

Memory injection priority: remembered > recalled > memory_inject > compaction

MCP integration:
  GitNexus MCP: query via build_gitnexus_prompt_context() at task runtime
  Obsidian MCP: wiki auto-ingest via on_turn_deep_ingest() after every LLM response
  All other MCPs: accessed through their respective _bridge modules
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DIRECTIVES_RE = re.compile(r"@(legion|claude)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)

# ── Per-session singleton state ─────────────────────────────────────────────────
# Ensures persistent context is built ONCE at session start, then reused.
# Reset on bot restart (module reimport), which is the correct behavior.
_session_memory_initialized = False


def _get_session_dirs(project_dir: str) -> tuple[Path, Path]:
    """Return (session_dir, wiki_dir) for a project root."""
    session_dir = Path(project_dir) / ".session_state"
    wiki_dir = Path(project_dir) / ".wiki"
    return session_dir, wiki_dir


async def _ensure_session_memory(project_dir: str, force: bool = False) -> bool:
    """
    Build the 7-layer persistent context ONCE at session start.
    Writes .session_state/memory_inject.md and .session_state/persistent_memory_context.md.
    Safe to call multiple times — only builds on first invocation per session.
    """
    global _session_memory_initialized
    if _session_memory_initialized and not force:
        return True

    session_dir, wiki_dir = _get_session_dirs(project_dir)
    try:
        from core.memory.autoinject import build_persistent_context
        # Pass wiki_dir so autoinject can read recent Obsidian notes
        ctx = build_persistent_context(
            query="project work coding AI agent tasks decisions",
            user_id="bashara",
            include_layers=list(range(1, 8)),
        )
        logger.info("7-layer persistent context built: %d chars", len(ctx))
        _session_memory_initialized = True
        return True
    except Exception as e:
        logger.warning("Persistent context build failed (non-fatal): %s", e)
        # Still mark initialized so we don't retry every task
        _session_memory_initialized = True
        return False


def _inject_memory_files(
    session_dir: Path,
    context_files: list[str],
) -> None:
    """
    Inject all available memory context files into the OpenCode subprocess.
    Priority order (first file wins for header conflicts):
      1. memory_inject.md       — session-level 7-layer persistent context (authoritative)
      2. compaction_summary.md  — last compaction checkpoint (if exists)
      3. remembered_context.md — post-compaction fresh 6-layer recall
      4. recalled_context.md    — per-task 6-layer semantic recall

    All four files are ALWAYS injected when present and fresh (<24h).
    The priority only determines which file's header/format wins conflicts.
    """
    logger.debug("[MEMORY_INJECT] Scanning session dir: %s", session_dir)

    # Priority order — first file wins for header/style conflicts.
    # Higher-priority = more authoritative project context, shown first.
    # Order: memory_inject (authoritative persistent) → compaction_summary
    #        (checkpoint) → remembered_context (post-compact recall) →
    #        recalled_context (per-task recall).
    # NOTE: All files are ALWAYS injected and concatenated — the priority
    # only determines header/style conflicts, not whether to inject.
    files_to_check = [
        ("memory_inject.md", "session-level 7-layer persistent context"),
        ("compaction_summary.md", "compaction checkpoint"),
        ("remembered_context.md", "post-compaction fresh recall"),
        ("recalled_context.md", "per-task 6-layer semantic recall"),
    ]

    injected_count = 0
    for filename, description in files_to_check:
        filepath = session_dir / filename
        if not filepath.exists():
            logger.debug("[MEMORY_INJECT] SKIP %s — does not exist", filename)
            continue

        size = filepath.stat().st_size
        if size == 0:
            logger.debug("[MEMORY_INJECT] SKIP %s — zero bytes", filename)
            continue

        # Freshness check: skip files older than 24h to avoid stale memory
        age_seconds = time.time() - filepath.stat().st_mtime
        age_hours = age_seconds / 3600
        if age_hours >= 24:
            logger.warning(
                "[MEMORY_INJECT] SKIP %s — stale (%.1fh old). description=%s size=%d",
                filename, age_hours, description, size,
            )
            continue

        context_files.append(str(filepath))
        logger.info(
            "[MEMORY_INJECT] INJECT %s (%s) — %d bytes, %.1fh fresh",
            filename, description, size, age_hours,
        )
        injected_count += 1

    logger.debug("[MEMORY_INJECT] Total files injected: %d", injected_count)


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
    """Execute a task via opencode CLI and return the result.

    Memory architecture (3-tier injection):
      TIER 1 — Session init  : _ensure_session_memory() writes memory_inject.md (7 layers)
                                  Called once at first task; cached for all subsequent tasks.
      TIER 2 — Per task recall: build_memory_context() writes recalled_context.md (6 layers)
                                  Called every task to pull fresh recall from all memory systems.
      TIER 3 — Compaction     : compaction_summary.md written by smart_compaction process.
                                  Injected if present (always after compaction).
      GITNEXUS: context file injected via -f (prompt-level, not embedded).
    All three tiers are injected via -f flags so OpenCode sees them as file context,
    not embedded in the prompt text.
    """
    project_dir = project_dir or "/home/newadmin/swarm-bot"
    model = os.getenv("LEGION_DEFAULT_MODEL", "minimax-coding-plan/MiniMax-M3")
    prompt_with_context = prompt
    context_files: list[str] = []
    session_dir = Path(project_dir) / ".session_state"

    # ── Ensure post_compact hooks are registered ────────────────────────────
    # Normally done at bot startup via start_background_tasks() → on_startup().
    # OpenCode bridge runs in a subprocess without bot lifecycle, so we call
    # register_builtin_hooks() here to ensure _recalled_context_refresh_hook
    # fires after compactions and keeps remembered_context.md fresh.
    from core.builtin_hooks import register_builtin_hooks
    register_builtin_hooks()

    # ── TIER 1: Session-level persistent memory (one-time init at session start)
    # Runs on first task; cached for all subsequent tasks via _session_memory_initialized flag.
    if os.getenv("LEGION_MEMORY_INJECT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        await _ensure_session_memory(project_dir)

    # ── TIER 2: Per-task 6-layer semantic recall
    # Note: We pass session_dir to _inject_memory_files below (not context_files list)
    # to avoid double-injecting recalled_context.md.  _inject_memory_files handles
    # all three files based on what exists on disk.
    recalled_file = session_dir / "recalled_context.md"
    if os.getenv("LEGION_MEMORY_INJECT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.memory.memory_injector import build_memory_context

            # Build fresh 6-layer memory context.
            # Writes to recalled_context.md (priority 2). We also write to
            # remembered_context.md (priority 1) so it stays fresh between
            # compactions — otherwise it goes stale (≥24h) and gets skipped,
            # losing the best memory context until the next compaction fires.
            query = task_desc or prompt[:100]
            ctx = build_memory_context(query=query, user_id="bashara", project_dir=project_dir)

            if ctx:
                # ── MCP tool reminder ──────────────────────────────────────────
                # Baked into per-task context so it survives OpenCode's own
                # compaction and is always present when OpenCode auto-calls tools.
                mcp_reminder = """
━━━ MCP TOOL REMINDER ━━━
MCP tools are always active — gitnexus, obsidian, ruflo_memory,
filesystem, exa, hermes, crawl4ai, browser_use, symphony, and more.

MANDATORY per-task checks BEFORE reading files or making changes:
  1. @ruflo_memory_search — query 6-layer memory for prior context
  2. @mcp_gitnexus — get code context, callers, impact BEFORE editing
  3. @mcp_obsidian — check .wiki for prior decisions and patterns
  4. @mcp_symphony — check task state before starting new work

Always use these tools — do NOT skip MCP calls even for simple tasks.
"""
                ctx_with_reminder = ctx + mcp_reminder

                # Write to priority 2 (per-task recall)
                session_dir.mkdir(parents=True, exist_ok=True)
                with open(recalled_file, "w") as f:
                    f.write(ctx_with_reminder)
                # Also write to priority 1 (post-compaction fresh recall)
                # This ensures priority 1 stays fresh without waiting for compaction
                remembered_file = session_dir / "remembered_context.md"
                with open(remembered_file, "w") as f:
                    f.write(ctx_with_reminder)
                logger.debug(
                    "Memory context refreshed: remembered=%s recalled=%s (%d chars)",
                    remembered_file, recalled_file, len(ctx_with_reminder),
                )
        except Exception as e:
            logger.debug("Memory context injection skipped: %s", e)

    # ── Inject all memory files (tiers 1+2+3 via _inject_memory_files, which reads
    # session_dir and appends whichever files exist — no list pre-population needed)
    _inject_memory_files(session_dir, context_files)

    # ── GITNEXUS context ───────────────────────────────────────────────────
    if os.getenv("LEGION_GITNEXUS_PROMPT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.gitnexus_bridge import build_gitnexus_prompt_context

            gitnexus_ctx = await build_gitnexus_prompt_context(prompt, max_chars=1800)
            if gitnexus_ctx:
                prompt_with_context = f"{gitnexus_ctx}\n\n{prompt}"
        except Exception:
            pass

    cmd = ["/home/newadmin/.opencode/bin/opencode", "run", "--dangerously-skip-permissions"]
    if agent:
        cmd.extend(["--agent", agent])
    cmd.extend(["--model", model])
    if context_files:
        for cf in context_files:
            cmd.extend(["-f", cf])
    cmd.append(prompt_with_context)

    # Log what we're passing to OpenCode for debugging
    file_args = [a for a in cmd if a.startswith("-f")]
    logger.info(
        "[OPENCODE LAUNCH] agent=%s model=%s files=%d prompt_chars=%d gitnexus=%s cmd=%s",
        agent or "general",
        model,
        len(file_args),
        len(prompt_with_context),
        "yes" if gitnexus_ctx else "no",
        " ".join(cmd[:4]) + " ...",
    )

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

    # Emit task lifecycle hooks so registered handlers (e.g. opencode_session_end_hook)
    # automatically ingest this task into the wiki brain. The _opencode_session_started
    # flag must be set so opencode_session_end_hook's guard passes.
    try:
        from core.hooks import get_hooks
        hooks = get_hooks()
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task_ctx = {
            "task": task_desc or prompt[:200],
            "sessionId": task_id,
            "actions_taken": "",
            "outcome": stdout.decode()[:2000],
            "_opencode_session_started": True,  # enables opencode_session_end_hook wiki write
        }
        await hooks.emit("post_task", task_ctx)
        await hooks.emit("task_success", task_ctx)
    except Exception:
        pass  # hooks may be unavailable

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

    Memory architecture mirrors run_opencode_task (3-tier injection).
    Yields dicts with keys: type (event|data|error|done), content, raw.
    type="done" marks final output with full stdout.
    """
    project_dir = project_dir or "/home/newadmin/swarm-bot"
    model = os.getenv("LEGION_DEFAULT_MODEL", "minimax-coding-plan/MiniMax-M3")
    prompt_with_context = prompt
    context_files: list[str] = []
    session_dir = Path(project_dir) / ".session_state"

    # ── Ensure post_compact hooks are registered ────────────────────────────
    from core.builtin_hooks import register_builtin_hooks
    register_builtin_hooks()

    # ── TIER 1: Session-level persistent memory (one-time init at session start)
    if os.getenv("LEGION_MEMORY_INJECT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        await _ensure_session_memory(project_dir)

    # ── TIER 2: Per-task 6-layer semantic recall (trigger build, let _inject handle file)
    recalled_file = session_dir / "recalled_context.md"
    if os.getenv("LEGION_MEMORY_INJECT_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
        try:
            from core.memory.memory_injector import build_memory_context

            # Build fresh 6-layer memory context.
            # Writes to recalled_context.md (priority 2). We also write to
            # remembered_context.md (priority 1) so it stays fresh between
            # compactions — otherwise it goes stale (≥24h) and gets skipped.
            query = prompt[:100]
            ctx = build_memory_context(query=query, user_id="bashara", project_dir=project_dir)

            if ctx:
                # ── MCP tool reminder ──────────────────────────────────────────
                # Baked into per-task context so it survives OpenCode's own
                # compaction and is always present when OpenCode auto-calls tools.
                mcp_reminder = """
━━━ MCP TOOL REMINDER ━━━
MCP tools are always active — gitnexus, obsidian, ruflo_memory,
filesystem, exa, hermes, crawl4ai, browser_use, symphony, and more.

MANDATORY per-task checks BEFORE reading files or making changes:
  1. @ruflo_memory_search — query 6-layer memory for prior context
  2. @mcp_gitnexus — get code context, callers, impact BEFORE editing
  3. @mcp_obsidian — check .wiki for prior decisions and patterns
  4. @mcp_symphony — check task state before starting new work

Always use these tools — do NOT skip MCP calls even for simple tasks.
"""
                ctx_with_reminder = ctx + mcp_reminder

                session_dir.mkdir(parents=True, exist_ok=True)
                with open(recalled_file, "w") as f:
                    f.write(ctx_with_reminder)
                remembered_file = session_dir / "remembered_context.md"
                with open(remembered_file, "w") as f:
                    f.write(ctx_with_reminder)
                logger.debug(
                    "Memory context refreshed: remembered=%s recalled=%s (%d chars)",
                    remembered_file, recalled_file, len(ctx_with_reminder),
                )
        except Exception as e:
            logger.debug("Memory context injection skipped: %s", e)

    # ── Inject all memory files (tiers 1+2+3 via _inject_memory_files)
    _inject_memory_files(session_dir, context_files)

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
