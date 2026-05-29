"""Session teardown for the Autonomy Layer.

Implements Part X of the Autonomy Layer master prompt v2:
  - Auto-detect session end signals
  - Run teardown sequence silently
  - Announce with one line only
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ruflo_available = True
_mcp_client = None

try:
    from core.mcp_client import MCPClient
    _mcp_client = MCPClient()
except Exception:
    ruflo_available = False

GOODBYE_SIGNALS = [
    "done", "bye", "that's all", "thanks", "selesai", "makasih",
    "ok done", "goodbye", "exit", "quit", "stop",
]


async def _call_ruflo(tool: str, args: dict | None = None) -> dict:
    if not ruflo_available or _mcp_client is None:
        return {}
    try:
        result = await _mcp_client.call_tool("ruflo", tool, args or {})
        # call_tool returns str (JSON text or error message), not a list
        if isinstance(result, str) and result.startswith("{"):
            import json
            return json.loads(result)
        return {}
    except Exception as e:
        logger.debug("ruflo %s failed: %s", tool, e)
        return {}


def detect_goodbye(message: str) -> bool:
    """Check if message is a goodbye signal."""
    msg_lower = message.lower().strip().rstrip("!?.")
    return any(signal == msg_lower for signal in GOODBYE_SIGNALS)


async def run_teardown_sequence(
    session_summary: str,
    task_count: int,
    detected_projects: list[str],
    has_code_changes: bool = False,
    uncommitted_files: list[str] | None = None,
) -> str:
    """Run the full teardown sequence silently (< 10 seconds).

    Returns the one-line announcement message.
    """
    start = asyncio.get_event_loop().time()
    ts = datetime.now().strftime("%Y%m%d-%H%M")

    # STEP 1: Save ruflo session
    await _call_ruflo("session_save", {
        "name": f"auto-{ts}",
        "includeMemory": True,
    })

    # STEP 2: Export session backup
    await _call_ruflo("session_backup", {
        "name": f"auto-{ts}",
        "format": "json",
        "destination": "~/.legion/sessions/",
    })

    # STEP 3: Write obsidian daily note (via direct write — MCP append_to_note
    # requires vault path env, fallback to obsidian_autosync which writes directly)
    try:
        from core.legion_session import get_session_metrics
        from core.memory.obsidian_autosync import write_daily_session_log, write_memory_block

        metrics = get_session_metrics()
        write_daily_session_log(
            session_name=f"legion-{ts}",
            tasks_completed=metrics.accomplished,
            key_decisions=metrics.decisions,
            files_changed=metrics.files_changed,
            user_message=session_summary[:200],
            memory_layers_used=7,
        )
        # Write any flagged memories
        for decision in metrics.decisions[:3]:
            if len(decision) > 20:
                write_memory_block(
                    content=decision,
                    title=f"decision-{ts}",
                    tags=["auto-saved", "decision"],
                    memory_type="semantic",
                    importance=0.7,
                )
    except Exception as e:
        logger.debug("obsidian daily note write failed: %s", e)

    # STEP 4: mem0 add
    try:
        from tools.mem0_client import mem0_add
        today_str = datetime.now().strftime("%Y-%m-%d")
        meta = {
            "type": "session",
            "date": today_str,
            "projects": detected_projects,
        }
        await mem0_add("bashara", session_summary, meta)
    except Exception as e:
        logger.debug("mem0 add failed: %s", e)

    # STEP 5: Memory consolidation worker
    await _call_ruflo("hooks_worker-dispatch", {
        "worker": "memory_consolidate",
        "trigger": "immediate",
    })

    # STEP 6: Git status (only if code changes)
    uncommitted = []
    if has_code_changes:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd="/home/newadmin/swarm-bot",
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                uncommitted = result.stdout.strip().split("\n")[:10]
        except Exception:
            pass

    elapsed = asyncio.get_event_loop().time() - start
    logger.info("Teardown complete in %.1fs, uncommitted=%s", elapsed, len(uncommitted))

    # Build announcement
    announcement = f"Session saved. {task_count} tasks completed. See you next time, Bashara."

    if uncommitted:
        files_str = ", ".join(u[:50] for u in uncommitted[:3])
        announcement += f" You have uncommitted changes: {files_str}."

    return announcement


async def check_git_status() -> tuple[bool, list[str]]:
    """Check if there are uncommitted changes."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd="/home/newadmin/swarm-bot",
            capture_output=True, text=True, timeout=5,
        )
        if result.stdout.strip():
            files = [line[3:] for line in result.stdout.strip().split("\n") if line.strip()]
            return True, files
    except Exception:
        pass
    return False, []